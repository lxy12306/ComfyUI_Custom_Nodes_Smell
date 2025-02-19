import torch
import os
import json
import random
from comfy.cli_args import args
from comfy.model_management import InterruptProcessingException

from PIL import Image
from PIL.PngImagePlugin import PngInfo
import torchvision.transforms.functional as F
import comfy.utils

import numpy as np
import psutil
import shutil

from server import PromptServer
from .libs.image_chooser_server import MessageHolder, Cancelled
from nodes import PreviewImage
def rescale(samples, width, height, algorithm: str):
    if algorithm == "bislerp":  # convert for compatibility with old workflows
        algorithm = "bicubic"
    algorithm = getattr(Image, algorithm.upper())  # i.e. Image.BICUBIC
    samples_pil: Image.Image = F.to_pil_image(samples[0].cpu()).resize((width, height), algorithm)
    samples = F.to_tensor(samples_pil).unsqueeze(0)
    return samples

def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

def is_folder_open(directory):
    for proc in psutil.process_iter():
        try:
            if proc.name() == "explorer.exe":
                if directory.lower() in [f.path.lower() for f in proc.open_files()]:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def bakup_excessive_file(directory, filename_prefix):
    bak_index = 0
    while True:
        padding = str(bak_index).zfill(4)
        dir_name = f"bak_{padding}"
        dir_path = os.path.join(directory, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            moved_files = 0
            for existing_file in os.listdir(directory):
                if (existing_file.startswith(filename_prefix) and
                    existing_file.endswith('.png')):
                    src_path = os.path.join(directory, existing_file)
                    dst_path = os.path.join(dir_path, existing_file)
                    shutil.move(src_path, dst_path)
                    moved_files += 1
            return moved_files
        bak_index += 1
def get_next_file_path(directory, filename_prefix, file_max=64):
    index = 1
    while True:
        padding = str(index).zfill(4)
        file_name = f"{filename_prefix}_{padding}.png"
        file_path = os.path.join(directory, file_name)
        if not os.path.exists(file_path):
            return file_path
        index += 1
        if index > file_max:
            bakup_excessive_file(directory, filename_prefix)
            index = 1


class ImageChooser(PreviewImage):
    @classmethod
    def INPUT_TYPES(self):
        return {
        "required":{
            "mode": (["Always pause", "Repeat last selection", "Only pause if batch", "Pass through", "Take First n", "Take Last n"], {"default": "Always Pause"}),
            "count": ("INT", { "default": 1, "min": 1, "max": 999, "step": 1 }),
        },
        "optional": {
            "images": ("IMAGE",),
        },
        "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO", "id":"UNIQUE_ID"},
        }

    RETURN_TYPES = ("IMAGE","STRING")
    RETURN_NAMES = ("images","selected")
    FUNCTION = "chooser"
    OUTPUT_NODE = True
    INPUT_IS_LIST = True
    CATEGORY = "EasyUse/Image"

    last_ic = {}
    @classmethod
    def IS_CHANGED(cls, id, **kwargs):
        mode = kwargs.get("mode",["Always pause"])
        if (mode[0]!="Repeat last selection" or not id[0] in cls.last_ic): cls.last_ic[id[0]] = random.random()
        return cls.last_ic[id[0]]

    def tensor_bundle(self, tensor_in: torch.Tensor, picks):
        if tensor_in is not None and len(picks):
            batch = tensor_in.shape[0]
            return torch.cat(tuple([tensor_in[(x) % batch].unsqueeze_(0) for x in picks])).reshape([-1] + list(tensor_in.shape[1:]))
        else:
            return None

    def batch_up_selections(self, images_in:torch.Tensor, selections, mode):
        if (mode=="Pass through"):
            chosen = range(0, self.batch)
        elif (mode=="Take First n"):
            end = self.count if self.batch >= self.count else self.batch
            chosen = range(0, end)
        elif (mode=="Take Last n"):
            start = self.batch - self.count if self.batch - self.count >= 0 else 0
            chosen = range(start, self.batch)
        else:
            chosen = [x for x in selections if x>=0]

        return (self.tensor_bundle(images_in, chosen), ",".join(str(x) for x in chosen), )

    def chooser(self, id=None, **kwargs):
        # mode doesn't exist in subclass
        self.count = int(kwargs.pop('count', [1,])[0])
        mode = kwargs.pop('mode',["Always pause",])[0]
        if mode=="Repeat last selection":
            print("Here despite 'Repeat last selection' - treat as 'Always pause'")
            mode = "Always pause"
        if mode=="Always pause":
            # pretend it was Repeat last so that the prompt matches if that is selected next time.
            # UGH
            kwargs['prompt'][0][id[0]]['inputs']['mode'] = "Repeat last selection"
        id = id[0]
        if id not in MessageHolder.stash:
            MessageHolder.stash[id] = {}
        my_stash = MessageHolder.stash[id]


        # enable stashing. If images is None, we are operating in read-from-stash mode
        if 'images' in kwargs:
            my_stash['images']  = kwargs['images']
        else:
            kwargs['images']  = my_stash.get('images', None)
            
        if (kwargs['images'] is None):
            return (None, None, None, "")
        
        # convert list to batch
        images_in         = torch.cat(kwargs.pop('images'))
        self.batch        = len(images_in)

        # any other parameters shouldn't be lists any more...
        for x in kwargs: kwargs[x] = kwargs[x][0]
 
        # call PreviewImage base
        ret = self.save_images(images=images_in, **kwargs)

        # send the images to view
        PromptServer.instance.send_sync("early-image-handler", {"id": id, "urls":ret['ui']['images']})

        # wait for selection
        try:
            is_block_condition = (mode == "Always pause" or mode == "Progress first pick" or self.batch > 1)
            is_blocking_mode = (mode not in ["Pass through", "Take First n", "Take Last n"])
            selections = MessageHolder.waitForMessage(id, asList=True) if (is_blocking_mode and is_block_condition) else [0]
        except Cancelled:
            raise InterruptProcessingException()
            #return (None, None,)

        return self.batch_up_selections(images_in=images_in, selections=selections, mode=mode)

class PreviewAndChoose(PreviewImage):
    RETURN_TYPES = ("IMAGE","LATENT","MASK","STRING","SEGS")
    RETURN_NAMES = ("images","latents","masks","selected","segs")
    FUNCTION = "func"
    CATEGORY = "image_chooser"
    INPUT_IS_LIST=True
    OUTPUT_NODE = False
    last_ic = {}
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mode" : (["Always pause", "Repeat last selection", "Only pause if batch", "Progress first pick", "Pass through", "Take First n", "Take Last n"],{}),
				"count": ("INT", { "default": 1, "min": 1, "max": 999, "step": 1 }),
            },
            "optional": {"images": ("IMAGE", ), "latents": ("LATENT", ), "masks": ("MASK", ), "segs":("SEGS", ) },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO", "id":"UNIQUE_ID"},
        }

    @classmethod
    def IS_CHANGED(cls, id, **kwargs):
        mode = kwargs.get("mode",["Always pause"])
        if (mode[0]!="Repeat last selection" or not id[0] in cls.last_ic): cls.last_ic[id[0]] = random.random()
        return cls.last_ic[id[0]]

    def func(self, id, **kwargs):
        # mode doesn't exist in subclass
        self.count = int(kwargs.pop('count', [1,])[0])
        mode = kwargs.pop('mode',["Always pause",])[0]
        if mode=="Repeat last selection":
            print("Here despite 'Repeat last selection' - treat as 'Always pause'")
            mode = "Always pause"
        if mode=="Always pause":
            # pretend it was Repeat last so that the prompt matches if that is selected next time.
            # UGH
            kwargs['prompt'][0][id[0]]['inputs']['mode'] = "Repeat last selection"
        id = id[0]
        if id not in MessageHolder.stash:
            MessageHolder.stash[id] = {}
        my_stash = MessageHolder.stash[id]

        DOING_SEGS = 'segs' in kwargs

        # enable stashing. If images is None, we are operating in read-from-stash mode
        if 'images' in kwargs:
            my_stash['images']  = kwargs['images']
            my_stash['latents'] = kwargs.get('latents', None)
            my_stash['masks']   = kwargs.get('masks', None)
        else:
            kwargs['images']  = my_stash.get('images', None)
            kwargs['latents'] = my_stash.get('latents', None)
            kwargs['masks']   = my_stash.get('masks', None)
            
        if (kwargs['images'] is None):
            return (None, None, None, "")
        
        # convert list to batch
        images_in         = torch.cat(kwargs.pop('images')) if not DOING_SEGS else list(i[0,...] for i in kwargs.pop('images'))
        latents_in        = kwargs.pop('latents', None)
        masks_in          = torch.cat(kwargs.get('masks')) if kwargs.get('masks', None) is not None else None
        segs_in           = kwargs.pop('segs', None)
        kwargs.pop('masks', None)
        latent_samples_in = torch.cat(list(l['samples'] for l in latents_in)) if latents_in is not None else None
        self.batch        = images_in.shape[0] if not DOING_SEGS else len(images_in)

        # any other parameters shouldn't be lists any more...
        for x in kwargs: kwargs[x] = kwargs[x][0]
 
        # call PreviewImage base
        ret = self.save_images(images=images_in, **kwargs)

        # send the images to view
        PromptServer.instance.send_sync("early-image-handler", {"id": id, "urls":ret['ui']['images']})

        # wait for selection
        try:
            is_block_condition = (mode == "Always pause" or mode == "Progress first pick" or self.batch > 1)
            is_blocking_mode = (mode not in ["Pass through", "Take First n", "Take Last n"])
            selections = MessageHolder.waitForMessage(id, asList=True) if (is_blocking_mode and is_block_condition) else [0]
        except Cancelled:
            raise InterruptProcessingException()
            #return (None, None,)
        
        if DOING_SEGS: 
            segs_out = (segs_in[0][0], list(segs_in[0][1][i] for i in selections if i>=0) )
            return(None, None, None, None, segs_out)
        
        return self.batch_up_selections(images_in=images_in, latent_samples_in=latent_samples_in, masks_in=masks_in, selections=selections, mode=mode)

    def tensor_bundle(self, tensor_in:torch.Tensor, picks):
        if tensor_in is not None and len(picks):
            batch = tensor_in.shape[0]
            return torch.cat(tuple([tensor_in[(x)%batch].unsqueeze_(0) for x in picks])).reshape([-1]+list(tensor_in.shape[1:]))
        else:
            return None
    
    def latent_bundle(self, latent_samples_in:torch.Tensor, picks):
        if (latent_samples_in is not None and len(picks)):
            return { "samples" : self.tensor_bundle(latent_samples_in, picks) }
        else:
            return None
    
    def batch_up_selections(self, images_in:torch.Tensor, latent_samples_in:torch.Tensor, masks_in:torch.Tensor, selections, mode):
        if (mode=="Pass through"):
            chosen = range(0, self.batch)
        elif (mode=="Take First n"):
            end = self.count if self.batch >= self.count else self.batch
            chosen = range(0, end)
        elif (mode=="Take Last n"):
            start = self.batch - self.count if self.batch - self.count >= 0 else 0
            chosen = range(start, self.batch)
        else:
            chosen = [x for x in selections if x>=0]

        return (self.tensor_bundle(images_in, chosen), self.latent_bundle(latent_samples_in, chosen), self.tensor_bundle(masks_in, chosen), ",".join(str(x) for x in chosen), None, )

class ImageAndMaskConcatenationNode:  
    @classmethod  
    def INPUT_TYPES(cls):  
        return {  
            "required": {  
                "image1": ("IMAGE", {"tooltip": "First image input"}),  
                "mask1": ("MASK", {"tooltip": "First mask input"}),  
                "image2": ("IMAGE", {"tooltip": "Second image input"}),  
                "mask2": ("MASK", {"tooltip": "Second mask input"}),  
                "direction": (
                [   'right',
                    'down',
                    'left',
                    'up',
                ],
                {
                "default": 'right'
                }),
                "match_image_size": ("BOOLEAN", {"default": True}),
            },  
        }  

    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT", "INT", "INT")  
    RETURN_NAMES = ("concatenated_image", "concatenated_mask", "concatenated_width", "concatenated_height", "x", "y")  
    FUNCTION = "concatenate_images_and_masks"  
    OUTPUT_NODE = True
    CATEGORY = "SMELL_COMMON_IMAGE_FUNCTION"  
    DESCRIPTION = "Concatenate two images and two masks"  

    def concatenate_images_and_masks(cls, image1, mask1, image2, mask2, direction, match_image_size, first_image_shape=None):  
        # 检查批量大小是否不同  
        batch_size1 = image1.shape[0]  
        batch_size2 = image2.shape[0]  

        if batch_size1 != batch_size2:  
            # 计算所需的重复次数  
            max_batch_size = max(batch_size1, batch_size2)  
            repeats1 = max_batch_size // batch_size1  
            repeats2 = max_batch_size // batch_size2  
            
            # 重复图像以匹配最大的批量大小  
            image1 = image1.repeat(repeats1, 1, 1, 1)  
            image2 = image2.repeat(repeats2, 1, 1, 1)  

            # 重复掩膜以匹配最大的批量大小  
            mask1 = mask1.repeat(repeats1, 1, 1, 1)  
            mask2 = mask2.repeat(repeats2, 1, 1, 1)  
  
        results_image = []
        results_mask = []
        concatenated_width = 0
        concatenated_height = 0
        x = 0
        y = 0

        for b in range(batch_size1):
            one_image1 = image1[b].unsqueeze(0)  # Adding batch dimension
            one_mask1 = mask1[b].unsqueeze(0)    # Adding batch dimension
            one_image2 = image2[b].unsqueeze(0)  # Adding batch dimension
            one_mask2 = mask2[b].unsqueeze(0)    # Adding batch dimension

            image1_height = one_image1.shape[1]
            image1_width = one_image1.shape[2]
            image2_height = one_image2.shape[1]
            image2_width = one_image2.shape[2]

            mask1_height = one_mask1.shape[1]
            mask1_width = one_mask1.shape[2]
            mask2_height = one_mask2.shape[1]
            mask2_width = one_mask2.shape[2]

            # 比较 image1 和 mask1 的尺寸  
            if image1_height != mask1_height or image1_width != mask1_width:  
                # 创建一个与 image1 尺寸相同的 mask1，初始化为全零或其他默认值  
                one_mask1 = torch.zeros_like(one_image1[:, :, :, 0])  # 创建一个与 image1 相同尺寸的全零掩膜  
                print(f"警告：image1 的尺寸 ({image1_height}, {image1_width}) 与 mask1 的尺寸 ({mask1_height}, {mask1_width}) 不匹配，已创建新的掩膜。") 

            # 比较 image2 和 mask2 的尺寸  
            if image2_height != mask2_height or image2_width != mask2_width:  
                # 创建一个与 image1 尺寸相同的 mask1，初始化为全零或其他默认值  
                one_mask2 = torch.zeros_like(one_image2[:, :, :, 0]) # 创建一个与 image1 相同尺寸的全零掩膜 
                print(f"警告：image2 的尺寸 ({image2_height}, {image2_width}) 与 mask2 的尺寸 ({mask2_height}, {mask2_width}) 不匹配，已创建新的掩膜。") 

            if match_image_size:  
                # 如果提供了 first_image_shape，则使用它；否则，默认为 image1 的形状  
                target_shape = first_image_shape if first_image_shape is not None else one_image1.shape  

                original_height = one_image2.shape[1]  
                original_width = one_image2.shape[2]  
                original_aspect_ratio = original_width / original_height  

                if direction in ['left', 'right']:  
                    # 匹配高度并调整宽度以保持纵横比  
                    target_height = target_shape[1]  # B, H, W, C 格式  
                    target_width = int(target_height * original_aspect_ratio)  
                elif direction in ['up', 'down']:  
                    # 匹配宽度并调整高度以保持纵横比  
                    target_width = target_shape[2]  # B, H, W, C 格式  
                    target_height = int(target_width / original_aspect_ratio)  
                
                samples = one_image2            
                samples = samples.movedim(-1, 1)
                samples = rescale(samples, target_width, target_height, "nearest")
                samples = samples.movedim(1, -1)
                one_image2 = samples
        
                samples = one_mask2
                samples = samples.unsqueeze(1)
                samples = rescale(samples, target_width, target_height, "nearest")
                samples = samples.squeeze(1)
                one_mask2 = samples


            # 确保两个图像具有相同数量的通道  
            channels_image1 = one_image1.shape[-1]  
            channels_mask1 = one_mask1.shape[-1]  
            channels_image2 = one_image2.shape[-1]  
            channels_mask2 = one_mask2.shape[-1]  

            if channels_image1 != channels_image2:  
                if channels_image1 < channels_image2:  
                    # 如果 image2 有 alpha 通道，则为 image1 添加 alpha 通道  
                    alpha_channel = torch.ones((*one_image1.shape[:-1], channels_image2 - channels_image1), device=one_image1.device)  
                    alpha_channel_mask = torch.ones((*one_mask1.shape[:-1], channels_mask2 - channels_mask1), device=one_mask1.device)  
                    one_image1 = torch.cat((one_image1, alpha_channel), dim=-1)  
                    one_mask1 = torch.cat((one_mask1, alpha_channel_mask), dim=-1)  
                else:  
                    # 如果 image1 有 alpha 通道，则为 image2 添加 alpha 通道  
                    alpha_channel = torch.ones((*one_image2.shape[:-1], channels_image1 - channels_image2), device=one_image2.device)  
                    alpha_channel_mask = torch.ones((*one_mask2.shape[:-1], channels_mask1 - channels_mask2), device=one_mask2.device)  
                    one_image2 = torch.cat((one_image2, alpha_channel), dim=-1)  
                    one_mask2 = torch.cat((one_mask2, alpha_channel_mask), dim=-1) 


            # 根据指定的方向进行拼接  
            if direction == 'right':  
                concatenated_image = torch.cat((one_image1, one_image2), dim=2)  # 沿宽度拼接  
                concatenated_mask = torch.cat((one_mask1, one_mask2), dim=2)  # 沿宽度拼接  
                x = one_image1.shape[2]
            elif direction == 'down':  
                concatenated_image = torch.cat((one_image1, one_image2), dim=1)  # 沿高度拼接  
                concatenated_mask = torch.cat((one_mask1, one_mask2), dim=1)  # 沿高度拼接  
                y = one_image1.shape[1]
            elif direction == 'left':  
                concatenated_image = torch.cat((one_image2, one_image1), dim=2)  # 沿宽度拼接  
                concatenated_mask = torch.cat((one_mask2, one_mask1), dim=2)  # 沿宽度拼接  
                x = one_image2.shape[2]
            elif direction == 'up':  
                concatenated_image = torch.cat((one_image2, one_image1), dim=1)  # 沿高度拼接  
                concatenated_mask = torch.cat((one_mask2, one_mask1), dim=1)  # 沿高度拼接  
                y = one_image2.shape[1]

            concatenated_height = concatenated_image.shape[1]
            concatenated_width = concatenated_image.shape[2]

            results_image.append(concatenated_image.squeeze(0))
            results_mask.append(concatenated_mask.squeeze(0))

        output_image = torch.stack(results_image, dim=0)
        output_mask = torch.stack(results_mask, dim=0)

        return output_image, output_mask, concatenated_width, concatenated_height, x, y

class ImageBlank:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 512, "min": 8, "max": 4096, "step": 1}),
                "height": ("INT", {"default": 512, "min": 8, "max": 4096, "step": 1}),
                "red": ("INT", {"default": 255, "min": 0, "max": 255, "step": 1}),
                "green": ("INT", {"default": 255, "min": 0, "max": 255, "step": 1}),
                "blue": ("INT", {"default": 255, "min": 0, "max": 255, "step": 1}),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "blank_image"
    OUTPUT_NODE = True
    CATEGORY = "SMELL_COMMON_IMAGE_FUNCTION"  
    DESCRIPTION = "Generate a blank image"  

    def blank_image(self, width, height, red, green, blue):

        # Ensure multiples
        width = (width // 8) * 8
        height = (height // 8) * 8

        # Blend image
        blank = Image.new(mode="RGB", size=(width, height),
                          color=(red, green, blue))

        return (pil2tensor(blank), )

class ImageFill:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "width": ("INT", {"default": 512, "min": 8, "max": 4096, "step": 1}),
                "height": ("INT", {"default": 512, "min": 8, "max": 4096, "step": 1}),
                "red": ("INT", {"default": 255, "min": 0, "max": 255, "step": 1}),
                "green": ("INT", {"default": 255, "min": 0, "max": 255, "step": 1}),
                "blue": ("INT", {"default": 255, "min": 0, "max": 255, "step": 1}),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "fill_image"
    OUTPUT_NODE = True
    CATEGORY = "SMELL_COMMON_IMAGE_FUNCTION"  
    DESCRIPTION = "Fill image" 

    def fill_image(self, image, width, height, red, green, blue):
        d1, d2, d3, d4 = image.size()

        if d3 > width or d2 > height:
            raise ValueError(f"图像尺寸超出限制，宽度限制为 {width}，当前宽度为 {d2}；高度限制为 {height}，当前高度为 {d3}。")

        color_tensor = torch.tensor([red, green, blue], dtype=torch.float32)

        new_image = torch.ones(
            (d1, height, width, d4),
            dtype=torch.float32,
        ) * color_tensor

        left = int((width - d3) / 2)
        top = int((height - d2) / 2)

        new_image[:, top:top + d2, left:left + d3, :] = image

        return (new_image, )

class ImageSaver:

    def __init__(self):
        self.compression = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "Images": ("IMAGE",),
                "BaseDirectory": ("STRING", {}),
                "FilenamePrefix1": ("STRING", {"default": "Image"}),
                "FileMax": ("INT", {"default": 64}),
                "OpenOutputDirectory": ("BOOLEAN", {"default": False}),
            },
            "optional": {  
                "FilenamePrefix2": ("STRING", {"default": None}),  
            },  
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "BatchSave"
    OUTPUT_NODE = True
    CATEGORY = "SMELL_COMMON_IMAGE_FUNCTION"  
    DESCRIPTION = "Batch save files to a folder"  

    def BatchSave(self, Images, BaseDirectory, FilenamePrefix1, FileMax, OpenOutputDirectory, FilenamePrefix2 = None, prompt=None, extra_pnginfo=None):
        try:
            Directory1 = BaseDirectory
            Directory2 = os.path.join(Directory1, FilenamePrefix1)
            Directory = Directory2

            if not os.path.exists(Directory1):
                os.makedirs(Directory1)
            if not os.path.exists(Directory2):
                os.makedirs(Directory2)

            _FilenamePrefix1 = FilenamePrefix1
            FilenamePrefix = _FilenamePrefix1

            if not FilenamePrefix2 == None:
                Directory3 = os.path.join(Directory2, FilenamePrefix2)
                Directory = Directory3
                if not os.path.exists(Directory3):
                    os.makedirs(Directory3)
                _FilenamePrefix2 = FilenamePrefix2
                FilenamePrefix = f"{_FilenamePrefix1}_{_FilenamePrefix2}"

            for image in Images:
                print(image)
                i = 255. * image.cpu().numpy()
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                metadata = None
                if not args.disable_metadata:
                    metadata = PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))

                file_path = get_next_file_path(Directory, FilenamePrefix, FileMax)
                img.save(file_path, pnginfo=metadata, compress_level=self.compression)

            if (OpenOutputDirectory):
                try:
                    os.system(f'explorer "{Directory}"')
                    os.system(f'open "{Directory}"')
                    os.system(f'xdg-open "{Directory}"')
                except Exception as e:
                    print(f"Error opening directory: {e}")

        except Exception as e:
            print(f"Error saving image: {e}")

        return ()

class ImageAndTagLoader:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder": ("STRING", {"default": "None"}),
                "prefix": ("STRING", {"default": "None"}),
                "number": ("INT", {"default": 0}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("Tag",)
    FUNCTION = "image_and_tag_loader"
    OUTPUT_NODE = True
    CATEGORY = "SMELL_COMMON_IMAGE_ADN_TAG_LOADER"  
    DESCRIPTION = "Load image and tag"  

    @classmethod
    def image_and_tag_loader(self, folder, prefix, number):
        number_str = str(number).zfill(8)
        file_path = os.path.join(folder, f"{prefix}_{number_str}.txt")
        print(file_path)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                return (content,)
        else:
            return (None,)

class TagDeleteNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "org": ("STRING", {"default": ""}),
                "targets": ("STRING", {"default": ""}),
                "instert_first": ("BOOLEAN", {"default": False}),  
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("ModifiedString",)
    FUNCTION = "process_strings"
    OUTPUT_NODE = True
    CATEGORY = "SMELL_COMMON_TAG_DELETE_NODE"
    DESCRIPTION = "Remove elements from org string if target exists in them"

    @classmethod
    def process_strings(self, org, targets, instert_first):
        elements = [elem.strip() for elem in org.split(",")]
        target_list = [t.strip() for t in targets.split(",")]
        result = []

        for element in elements:
            should_keep = True
            for target in target_list:
                if target.lower() in element.lower():
                    should_keep = False
                    break
            if should_keep:
                result.append(element)

        if instert_first:
            result = target_list + result
        new_string = ",".join(result)
        return (new_string,)

NODE_CLASS_MAPPINGS = {
    "ImageChooser": ImageChooser,
    "ImageAndMaskConcatenationNode": ImageAndMaskConcatenationNode,
    "ImageBlank": ImageBlank,
    "ImageFill": ImageFill,
    "ImageSaver": ImageSaver,
    "ImageAndTagLoader": ImageAndTagLoader,
    "TagDeleteNode": TagDeleteNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageChooser" : "Smell Image Chooser",
    "ImageAndMaskConcatenationNode": "Smell Image And Mask Concatenation Node",
    "ImageBlank": "Smell Image Blank",
    "ImageFill": "Smell Image Fill",
    "ImageSaver": "Smell Image Saver",
    "ImageAndTagLoader": "Smell Image And Tag Loader",
    "TagDeleteNode": "Smell Image Tag Delete Node"
}