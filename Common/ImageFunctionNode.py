import torch
from PIL import Image
import comfy.utils
import torchvision.transforms.functional as F
  
def rescale(samples, width, height, algorithm: str):
    if algorithm == "bislerp":  # convert for compatibility with old workflows
        algorithm = "bicubic"
    algorithm = getattr(Image, algorithm.upper())  # i.e. Image.BICUBIC
    samples_pil: Image.Image = F.to_pil_image(samples[0].cpu()).resize((width, height), algorithm)
    samples = F.to_tensor(samples_pil).unsqueeze(0)
    return samples

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
    CATEGORY = "Image Function"  
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
    
NODE_CLASS_MAPPINGS = {
    "ImageAndMaskConcatenationNode": ImageAndMaskConcatenationNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageAndMaskConcatenationNode": "Smell Image And Mask Concatenation Node",
}