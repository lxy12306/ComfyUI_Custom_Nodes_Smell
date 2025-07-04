import torch
import os
import json
import random
import math

from comfy.model_management import InterruptProcessingException
from comfy.utils import common_upscale
from nodes import PreviewImage, MAX_RESOLUTION

from PIL import Image
from PIL.PngImagePlugin import PngInfo
import torchvision.transforms.functional as F

import numpy as np
import psutil
import shutil

from server import PromptServer
from .libs.function import *
from .libs.image_chooser_server import MessageHolder, Cancelled
from .libs.image_function import *
from .libs.os_function import *

from .OpenPoseFunctionNode import MixOpenPoseNode


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




class ImageChooser(PreviewImage):
    @classmethod
    def INPUT_TYPES(self):
        return {
        "required":{
            "mode": (["Always pause", "Repeat last selection", "Only pause if batch", "Pass through", "Take First n", "Take Last n"], {"default": "Always pause"}),
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
    CATEGORY = "🌱SmellCommon/ImageFunc"

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
    CATEGORY = "🌱SmellCommon/ImageFunc"
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
                "image2": ("IMAGE", {"tooltip": "Second image input"}),
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
            "optional": {
                "mask1": ("MASK", {"tooltip": "First mask input"}),
                "mask2": ("MASK", {"tooltip": "Second mask input"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT", "INT", "INT")
    RETURN_NAMES = ("concatenated_image", "concatenated_mask", "concatenated_width", "concatenated_height", "x", "y")
    FUNCTION = "concatenate_images_and_masks"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/ImageFunc"
    DESCRIPTION = "Concatenate two images and two masks"
    def concatenate_images_and_masks(cls, image1,  image2, direction, match_image_size, mask1=None, mask2=None, first_image_shape=None):
        # 检查批量大小是否不同
        batch_size1 = image1.shape[0]
        batch_size2 = image2.shape[0]

        if mask1 == None:
            mask1 = torch.zeros_like(image1[:, :, :, 0])
        if mask2 == None:
            mask2 = torch.zeros_like(image2[:, :, :, 0])

        if batch_size1 != batch_size2:
            raise ValueError(f"Batch size mismatch: image1 has {batch_size1} samples, but image2 has {batch_size2} samples. Both must have the same batch size.")

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
                else:
                    # 如果 image1 有 alpha 通道，则为 image2 添加 alpha 通道
                    alpha_channel = torch.ones((*one_image2.shape[:-1], channels_image1 - channels_image2), device=one_image2.device)
                    alpha_channel_mask = torch.ones((*one_mask2.shape[:-1], channels_mask1 - channels_mask2), device=one_mask2.device)
                    one_image2 = torch.cat((one_image2, alpha_channel), dim=-1)


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
    RETURN_NAMES = ("image")
    FUNCTION = "blank_image"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/ImageFunc"
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
    RETURN_NAMES = ("image",)
    FUNCTION = "fill_image"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/ImageFunc"
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

class ImageAspectRatioAdjuster:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        multiple_list = ['8', '16', '32', '64', '128', '256', '512', 'None']
        return {
            "required": {
                "image": ("IMAGE",),
                "max_length": ("INT", {"default": 768, "min": 1, "max": 8192, "step": 1}),
                "round_to_multiple": (multiple_list,),
                "use_common": ("BOOLEAN", {"default": True}),  # 选择使用常见或不常见宽高比
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "STRING")  # 返回宽度、高度, max_length和字符串
    RETURN_NAMES = ("width", "height", "max_length", "ratio")
    FUNCTION = "adjust_aspect_ratio"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/ImageFunc"
    DESCRIPTION = "Adjust image to the best aspect ratio and scale to max length."

    def adjust_aspect_ratio(self, image, max_length, round_to_multiple, use_common):
        # 定义常见和不常见的宽高比
        common_aspect_ratios = {
            "1:1": (1, 1),
            "3:2": (3, 2),
            "4:3": (4, 3),
            "16:9": (16, 9),
            "2:3": (2, 3),
            "3:4": (3, 4),
        }

        uncommon_aspect_ratios = {
            "5:4": (5, 4),
            "1.85:1": (185, 100),  # 乘以100以避免浮点数
            "2.39:1": (239, 100),  # 乘以100以避免浮点数
            "4:5": (4, 5),
            "9:16": (9, 16),
            "3:1": (3, 1),
            "2:1": (2, 1),
        }

        round_to_multiple_int = 1 if round_to_multiple == "None" else int(round_to_multiple)
        max_length = (max_length // round_to_multiple_int) * round_to_multiple_int
        # 如果不是使用常见宽高比，则合并两个字典
        if use_common:
            aspect_ratios = common_aspect_ratios
        else:
            aspect_ratios = {**common_aspect_ratios, **uncommon_aspect_ratios}

        d1, d2, d3, d4 = image.size()  # 获取输入图像的尺寸

        # 确保最长边不超过 max_length
        if d3 > d2:
            d2 = int(max_length / d3 * d2)
            d3 = max_length
        else :
            d3 = int(max_length / d2 * d3)
            d2 = max_length

        d2 = d2 // round_to_multiple_int
        d3 = d3 // round_to_multiple_int
        print(f"调整后高宽, 宽度: {d3}, 高度: {d2}")

        best_ratio = None
        best_width = 0
        best_height = 0
        max_area = 0

        for ratio, (w_ratio, h_ratio) in aspect_ratios.items():
            # 计算当前宽高比的高度和宽度
            if d3 / w_ratio >= d2 / h_ratio:
                new_height = d2 // h_ratio * h_ratio
                new_width = (new_height * w_ratio) // h_ratio
            else:
                new_width = d3 // w_ratio * w_ratio
                new_height = (new_width * h_ratio) // w_ratio

            # 计算截取后的面积
            area = new_width * new_height

            # 更新最佳宽高比
            if area > max_area:
                max_area = area
                best_ratio = ratio
                best_width = new_width
                best_height = new_height

        best_width = best_width * round_to_multiple_int
        best_height = best_height * round_to_multiple_int
        max_length = max(best_width, best_height)

        # 返回宽度、高度和计算得到的宽高比、宽度和高度的字符串
        print(f"最佳宽高比: {best_ratio}, 宽度: {best_width}, 高度: {best_height}")
        return (best_width, best_height, max_length, best_ratio)

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
                "save_meta": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "FilenamePrefix2": ("STRING", {"default": None}),
                "tags": ("STRING", {"default": None}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "BatchSave"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/ImageFunc"
    DESCRIPTION = "Batch save files to a folder"

    def write_text_file(self, file, content, encoding="utf-8"):
        try:
            with open(file, 'w', encoding=encoding, newline='\n') as f:
                f.write(content)
        except OSError:
            print(f"{file} save failed")

    def BatchSave(self, Images, BaseDirectory, FilenamePrefix1, FileMax, OpenOutputDirectory, save_meta, FilenamePrefix2 = None, tags = None, prompt=None, extra_pnginfo=None):
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
                if not save_meta:
                    metadata = PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))

                image_path, txt_path = get_next_file_path(Directory, FilenamePrefix,"png",FileMax)
                img.save(image_path, pnginfo=metadata, compress_level=self.compression)
                if tags != None and tags != "":
                    self.write_text_file(txt_path, tags)

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

class ImageSwitchSaver:

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
                "save_meta": ("BOOLEAN", {"default": True}),
                "switch": ("BOOLEAN", {"default": False}),
                "switch_dir1": ("STRING", {"default": "ok"}),
                "switch_dir2": ("STRING", {"default": "error"}),
            },
            "optional": {
                "tags": ("STRING", {"default": None}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "BatchSave"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/ImageFunc"
    DESCRIPTION = "Batch save files to a folder"

    def BatchSave(self, Images, BaseDirectory, FilenamePrefix1, FileMax, OpenOutputDirectory, save_meta, switch, switch_dir1, switch_dir2, tags = None, prompt=None, extra_pnginfo=None):
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

            FilenamePrefix2 = switch_dir1
            if not switch:
                FilenamePrefix2 = switch_dir2

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
                if not save_meta:
                    metadata = PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))

                image_path, txt_path = get_next_file_path(Directory, FilenamePrefix, FileMax)
                img.save(image_path, pnginfo=metadata, compress_level=self.compression)
                if tags != None and tags != "":
                    smell_write_text_file(txt_path, tags)

            if (OpenOutputDirectory):
                smell_debug(f"OpenOutputDirectory OpenOutputDirectoryOpenOutputDirectoryOpenOutputDirectoryOpenOutputDirectoryOpenOutputDirectory {Directory}")
                try:
                    os.system(f'explorer "{Directory}"')
                    os.system(f'open "{Directory}"')
                    os.system(f'xdg-open "{Directory}"')
                except Exception as e:
                    print(f"Error opening directory: {e}")

        except Exception as e:
            print(f"Error saving image: {e}")

        return ()

class ImageScaleByAspectRatio:

    def __init__(self):
        self.NODE_NAME = 'ImageScaleByAspectRatio'
        pass

    @classmethod
    def INPUT_TYPES(self):
        ratio_list = ['original', 'custom', '1:1', '3:2', '4:3', '16:9', '2:3', '3:4', '9:16']
        fit_mode = ['letterbox', 'crop', 'fill']
        method_mode = ['lanczos', 'bicubic', 'hamming', 'bilinear', 'box', 'nearest']
        multiple_list = ['None', '8', '16', '32', '64', '128', '256', '512']
        scale_to_list = ['None', 'longest', 'shortest', 'width', 'height', 'total_pixel(kilo pixel)']
        return {
            "required": {
                "aspect_ratio": (ratio_list,),
                "proportional_width": ("INT", {"default": 1, "min": 1, "max": 1e8, "step": 1}),
                "proportional_height": ("INT", {"default": 1, "min": 1, "max": 1e8, "step": 1}),
                "fit": (fit_mode,),
                "method": (method_mode,),
                "round_to_multiple": (multiple_list,),
                "scale_to_side": (scale_to_list,),  # 是否按长边缩放
                "scale_to_length": ("INT", {"default": 1024, "min": 4, "max": 1e8, "step": 1}),
                "background_color": ("STRING", {"default": "#000000"}),  # 背景颜色
            },
            "optional": {
                "image": ("IMAGE",),  #
                "mask": ("MASK",),  #
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "BOX", "INT", "INT",)
    RETURN_NAMES = ("image", "mask", "original_size", "width", "height",)
    FUNCTION = 'image_scale_by_aspect_ratio'
    CATEGORY = "🌱SmellCommon/ImageFunc"

    def image_scale_by_aspect_ratio(self, aspect_ratio, proportional_width, proportional_height,
                                    fit, method, round_to_multiple, scale_to_side, scale_to_length,
                                    background_color,
                                    image=None, mask = None,
                                    ):
        orig_images = []
        orig_masks = []
        orig_width = 0
        orig_height = 0
        target_width = 0
        target_height = 0
        ratio = 1.0
        ret_images = []
        ret_masks = []
        if image is not None:
            for i in image:
                i = torch.unsqueeze(i, 0)
                orig_images.append(i)
            orig_width, orig_height = tensor2pil(orig_images[0]).size
        if mask is not None:
            if mask.dim() == 2:
                mask = torch.unsqueeze(mask, 0)
            for m in mask:
                m = torch.unsqueeze(m, 0)
                if not is_valid_mask(m) and m.shape==torch.Size([1,64,64]):
                    log(f"Warning: {self.NODE_NAME} input mask is empty, ignore it.", message_type='warning')
                else:
                    orig_masks.append(m)

            if len(orig_masks) > 0:
                _width, _height = tensor2pil(orig_masks[0]).size
                if (orig_width > 0 and orig_width != _width) or (orig_height > 0 and orig_height != _height):
                    log(f"Error: {self.NODE_NAME} execute failed, because the mask is does'nt match image.", message_type='error')
                    return (None, None, None, 0, 0,)
                elif orig_width + orig_height == 0:
                    orig_width = _width
                    orig_height = _height

        if orig_width + orig_height == 0:
            log(f"Error: {self.NODE_NAME} execute failed, because the image or mask at least one must be input.", message_type='error')
            return (None, None, None, 0, 0,)

        if aspect_ratio == 'original':
            ratio = orig_width / orig_height
        elif aspect_ratio == 'custom':
            ratio = proportional_width / proportional_height
        else:
            s = aspect_ratio.split(":")
            ratio = int(s[0]) / int(s[1])

        # calculate target width and height
        if ratio > 1:
            if scale_to_side == 'longest':
                target_width = scale_to_length
                target_height = int(target_width / ratio)
            elif scale_to_side == 'shortest':
                target_height = scale_to_length
                target_width = int(target_height * ratio)
            elif scale_to_side == 'width':
                target_width = scale_to_length
                target_height = int(target_width / ratio)
            elif scale_to_side == 'height':
                target_height = scale_to_length
                target_width = int(target_height * ratio)
            elif scale_to_side == 'total_pixel(kilo pixel)':
                target_width = math.sqrt(ratio * scale_to_length * 1000)
                target_height = target_width / ratio
                target_width = int(target_width)
                target_height = int(target_height)
            else:
                target_width = orig_width
                target_height = int(target_width / ratio)
        else:
            if scale_to_side == 'longest':
                target_height = scale_to_length
                target_width = int(target_height * ratio)
            elif scale_to_side == 'shortest':
                target_width = scale_to_length
                target_height = int(target_width / ratio)
            elif scale_to_side == 'width':
                target_width = scale_to_length
                target_height = int(target_width / ratio)
            elif scale_to_side == 'height':
                target_height = scale_to_length
                target_width = int(target_height * ratio)
            elif scale_to_side == 'total_pixel(kilo pixel)':
                target_width = math.sqrt(ratio * scale_to_length * 1000)
                target_height = target_width / ratio
                target_width = int(target_width)
                target_height = int(target_height)
            else:
                target_height = orig_height
                target_width = int(target_height * ratio)

        if round_to_multiple != 'None':
            multiple = int(round_to_multiple)
            target_width = num_round_up_to_multiple(target_width, multiple)
            target_height = num_round_up_to_multiple(target_height, multiple)

        _mask = Image.new('L', size=(target_width, target_height), color='black')
        _image = Image.new('RGB', size=(target_width, target_height), color='black')

        resize_sampler = Image.LANCZOS
        if method == "bicubic":
            resize_sampler = Image.BICUBIC
        elif method == "hamming":
            resize_sampler = Image.HAMMING
        elif method == "bilinear":
            resize_sampler = Image.BILINEAR
        elif method == "box":
            resize_sampler = Image.BOX
        elif method == "nearest":
            resize_sampler = Image.NEAREST

        if len(orig_images) > 0:
            for i in orig_images:
                _image = tensor2pil(i).convert('RGB')
                _image = fit_resize_image(_image, target_width, target_height, fit, resize_sampler, background_color)
                ret_images.append(pil2tensor(_image))
        if len(orig_masks) > 0:
            for m in orig_masks:
                _mask = tensor2pil(m).convert('L')
                _mask = fit_resize_image(_mask, target_width, target_height, fit, resize_sampler).convert('L')
                ret_masks.append(image2mask(_mask))
        if len(ret_images) > 0 and len(ret_masks) >0:
            log(f"{self.NODE_NAME} Processed {len(ret_images)} image(s).", message_type='finish')
            return (torch.cat(ret_images, dim=0), torch.cat(ret_masks, dim=0),[orig_width, orig_height], target_width, target_height,)
        elif len(ret_images) > 0 and len(ret_masks) == 0:
            log(f"{self.NODE_NAME} Processed {len(ret_images)} image(s).", message_type='finish')
            return (torch.cat(ret_images, dim=0), None, [orig_width, orig_height], target_width, target_height,)
        elif len(ret_images) == 0 and len(ret_masks) > 0:
            log(f"{self.NODE_NAME} Processed {len(ret_masks)} image(s).", message_type='finish')
            return (None, torch.cat(ret_masks, dim=0), [orig_width, orig_height], target_width, target_height,)
        else:
            log(f"Error: {self.NODE_NAME} skipped, because the available image or mask is not found.", message_type='error')
            return (None, None, None, 0, 0,)

class ImagePad:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                    "image": ("IMAGE", ),  # 输入图像
                    "left": ("INT", {"default": 0, "min": 0, "max": MAX_RESOLUTION, "step": 1}),  # 左侧填充像素
                    "right": ("INT", {"default": 0, "min": 0, "max": MAX_RESOLUTION, "step": 1}),  # 右侧填充像素
                    "top": ("INT", {"default": 0, "min": 0, "max": MAX_RESOLUTION, "step": 1}),  # 顶部填充像素
                    "bottom": ("INT", {"default": 0, "min": 0, "max": MAX_RESOLUTION, "step": 1}),  # 底部填充像素
                    "extra_padding": ("INT", {"default": 0, "min": 0, "max": MAX_RESOLUTION, "step": 1}),  # 额外填充像素
                    "pad_mode": (["edge", "color"], {"default": "edge", "tooltip": "填充模式：边缘色或指定颜色"}),
                    "color": ("STRING", {"default": "0, 0, 0", "tooltip": "填充颜色，RGB值(0-255)，用逗号分隔"}),
                  },
                "optional": {
                    "mask": ("MASK", ),  # 可选的输入掩码
                    "target_width": ("INT", {"default": 512, "min": 0, "max": MAX_RESOLUTION, "step": 1, "forceInput": True}),
                    "target_height": ("INT", {"default": 512, "min": 0, "max": MAX_RESOLUTION, "step": 1, "forceInput": True}),
                }
                }

    RETURN_TYPES = ("IMAGE", "MASK", )
    RETURN_NAMES = ("images", "masks",)
    FUNCTION = "pad"
    CATEGORY = "🌱SmellCommon/ImageFunc"
    DESCRIPTION = "对输入图像和掩码应用自定义填充，支持边缘颜色或指定颜色填充。"

    def pad(self, image, left, right, top, bottom, extra_padding, color, pad_mode, mask=None, target_width=None, target_height=None):
        """
        填充图像和掩码

        参数:
            image: 输入图像 [B, H, W, C]
            left, right, top, bottom: 各方向填充像素数
            extra_padding: 所有边额外填充像素数
            color: 填充颜色(RGB值0-255)
            pad_mode: 填充模式("edge"或"color")
            mask: 可选输入掩码
            target_width, target_height: 目标尺寸(指定时进行居中填充)
        """
        # 获取图像维度
        B, H, W, C = image.shape

        # 调整掩码到图像尺寸(如果提供)
        if mask is not None:
            BM, HM, WM = mask.shape
            if HM != H or WM != W:
                mask = F.interpolate(mask.unsqueeze(1), size=(H, W), mode='nearest-exact').squeeze(1)

        # 解析背景色
        bg_color = self._parse_color(color, image.dtype, image.device)

        # 计算填充尺寸及位置
        padding_info = self._calculate_padding(
            image, W, H, target_width, target_height,
            left, right, top, bottom, extra_padding
        )
        pad_left, pad_right, pad_top, pad_bottom, padded_width, padded_height = padding_info

        # 创建输出图像
        out_image = torch.zeros((B, padded_height, padded_width, C),
                              dtype=image.dtype, device=image.device)

        # 应用填充
        self._apply_padding(
            image, out_image, pad_mode, bg_color,
            pad_left, pad_right, pad_top, pad_bottom
        )

        # 创建或调整掩码
        out_masks = self._prepare_masks(
            mask, B, H, W, padded_height, padded_width,
            pad_left, pad_right, pad_top, pad_bottom,
            image.dtype, image.device
        )

        return (out_image, out_masks)

    def _parse_color(self, color_str, dtype, device):
        """解析颜色字符串为RGB tensor"""
        bg_color = [int(x.strip())/255.0 for x in color_str.split(",")]
        if len(bg_color) == 1:
            bg_color = bg_color * 3  # 灰度转RGB
        return torch.tensor(bg_color, dtype=dtype, device=device)

    def _calculate_padding(self, image, W, H, target_width, target_height,
                         left, right, top, bottom, extra_padding):
        """计算各方向填充像素数和最终尺寸"""
        if target_width is not None and target_height is not None:
            # 目标尺寸填充模式
            if extra_padding > 0:
                # 如果指定了额外填充，先缩小图像
                image_resized = common_upscale(
                    image.movedim(-1, 1),
                    W - extra_padding,
                    H - extra_padding,
                    "lanczos", "disabled"
                ).movedim(1, -1)

                # 更新尺寸信息
                _, H, W, _ = image_resized.shape

            # 居中对齐到目标尺寸
            padded_width = target_width
            padded_height = target_height
            pad_left = (padded_width - W) // 2
            pad_right = padded_width - W - pad_left
            pad_top = (padded_height - H) // 2
            pad_bottom = padded_height - H - pad_top
        else:
            # 四边单独填充模式
            pad_left = left + extra_padding
            pad_right = right + extra_padding
            pad_top = top + extra_padding
            pad_bottom = bottom + extra_padding
            padded_width = W + pad_left + pad_right
            padded_height = H + pad_top + pad_bottom

        return pad_left, pad_right, pad_top, pad_bottom, padded_width, padded_height

    def _apply_padding(self, image, out_image, pad_mode, bg_color,
                      pad_left, pad_right, pad_top, pad_bottom):
        """应用指定模式的填充"""
        B, H, W, C = image.shape

        for b in range(B):
            if pad_mode == "edge":
                # 边缘填充模式 - 提取四边缘像素
                top_edge = image[b, 0, :, :]
                bottom_edge = image[b, H-1, :, :]
                left_edge = image[b, :, 0, :]
                right_edge = image[b, :, W-1, :]

                # 用边缘颜色均值填充对应区域
                out_image[b, :pad_top, :, :] = top_edge.mean(dim=0)
                out_image[b, pad_top+H:, :, :] = bottom_edge.mean(dim=0)
                out_image[b, :, :pad_left, :] = left_edge.mean(dim=0)
                out_image[b, :, pad_left+W:, :] = right_edge.mean(dim=0)
            else:
                # 颜色填充模式 - 用指定颜色填充整个画布
                out_image[b, :, :, :] = bg_color.unsqueeze(0).unsqueeze(0)

            # 复制原始图像到中央位置
            out_image[b, pad_top:pad_top+H, pad_left:pad_left+W, :] = image[b]

    def _prepare_masks(self, mask, B, H, W, padded_height, padded_width,
                      pad_left, pad_right, pad_top, pad_bottom, dtype, device):
        """准备输出掩码"""
        if mask is not None:
            # 如果提供了掩码，使用相同的填充扩展它
            out_masks = torch.nn.functional.pad(
                mask,
                (pad_left, pad_right, pad_top, pad_bottom),
                mode='replicate'
            )
        else:
            # 如果没有掩码，创建新掩码：填充区域为1，原图区域为0
            out_masks = torch.ones((B, padded_height, padded_width), dtype=dtype, device=device)
            for m in range(B):
                out_masks[m, pad_top:pad_top+H, pad_left:pad_left+W] = 0.0

        return out_masks

NODE_CLASS_MAPPINGS = {
    "ImageChooser": ImageChooser,
    "ImageAndMaskConcatenationNode": ImageAndMaskConcatenationNode,
    "ImageBlank": ImageBlank,
    "ImageFill": ImageFill,
    "ImageSaver": ImageSaver,
    "ImageSwitchSaver": ImageSwitchSaver,
    "ImageAspectRatioAdjuster": ImageAspectRatioAdjuster,
    "ImageScaleByAspectRatio": ImageScaleByAspectRatio,
    "ImagePad": ImagePad,
    "MixOpenPoseNode": MixOpenPoseNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageChooser" : "Smell Image Chooser",
    "ImageAndMaskConcatenationNode": "Smell Image And Mask Concatenation Node",
    "ImageBlank": "Smell Image Blank",
    "ImageFill": "Smell Image Fill",
    "ImageSaver": "Smell Image Saver",
    "ImageSwitchSaver": "Smell Image Saver Switch",
    "ImageAspectRatioAdjuster": "Smell Image AspectRatio Adjuster",
    "ImageScaleByAspectRatio": "Smell Image Scale By AspectRatio",
    "ImagePad": "Smell Image Pad",
    "MixOpenPoseNode": "Smell OpenPose Mix Node",
}