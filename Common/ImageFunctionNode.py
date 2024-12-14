import torch
from PIL import Image
import comfy.utils
  
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

    RETURN_TYPES = ("IMAGE", "MASK")  
    RETURN_NAMES = ("concatenated_image", "concatenated_mask")  
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
  
        image1_height = image1.shape[1]
        image1_width = image1.shape[2]
        image2_height = image2.shape[1]
        image2_width = image2.shape[2]

        mask1_height = mask1.shape[1]
        mask1_width = mask1.shape[2]
        mask2_height = mask2.shape[1]
        mask2_width = mask2.shape[2]

        # 比较 image1 和 mask1 的尺寸  
        if image1_height != mask1_height or image1_width != mask1_width:  
            raise ValueError(f"错误：image1 的尺寸 ({image1_height}, {image1_width}) 与 mask1 的尺寸 ({mask1_height}, {mask1_width}) 不匹配")  

        # 比较 image2 和 mask2 的尺寸  
        if image2_height != mask2_height or image2_width != mask2_width:  
            raise ValueError(f"错误：image2 的尺寸 ({image2_height}, {image2_width}) 与 mask2 的尺寸 ({mask2_height}, {mask2_width}) 不匹配")  

        if match_image_size:  
            # 如果提供了 first_image_shape，则使用它；否则，默认为 image1 的形状  
            target_shape = first_image_shape if first_image_shape is not None else image1.shape  

            original_height = image2.shape[1]  
            original_width = image2.shape[2]  
            original_aspect_ratio = original_width / original_height  

            if direction in ['left', 'right']:  
                # 匹配高度并调整宽度以保持纵横比  
                target_height = target_shape[1]  # B, H, W, C 格式  
                target_width = int(target_height * original_aspect_ratio)  
            elif direction in ['up', 'down']:  
                # 匹配宽度并调整高度以保持纵横比  
                target_width = target_shape[2]  # B, H, W, C 格式  
                target_height = int(target_width / original_aspect_ratio)  
            
            # 调整 image2 和 mask2 以适应 common_upscale 的预期格式  
            image2_for_upscale = image2.movedim(-1, 1)  # 将 C 移到第二个位置 (B, C, H, W)  
            mask2_for_upscale = mask2.movedim(-1, 1)  # 将 C 移到第二个位置 (B, C, H, W)  
            
            # 调整 image2 和 mask2 的大小以匹配目标尺寸，同时保持纵横比  
            image2_resized = comfy.utils.common_upscale(image2_for_upscale, target_width, target_height, "lanczos", "disabled")  
            mask2_resized = comfy.utils.common_upscale(mask2_for_upscale, target_width, target_height, "lanczos", "disabled")  
            
            # 在调整大小后将 image2 和 mask2 调整回原始格式 (B, H, W, C)  
            image2_resized = image2_resized.movedim(1, -1)  
            mask2_resized = mask2_resized.movedim(1, -1)  
        else:  
            image2_resized = image2  
            mask2_resized = mask2  

        # 确保两个图像具有相同数量的通道  
        channels_image1 = image1.shape[-1]  
        channels_mask1 = mask1.shape[-1]  
        channels_image2 = image2_resized.shape[-1]  
        channels_mask2 = mask2_resized.shape[-1]  

        if channels_image1 != channels_image2:  
            if channels_image1 < channels_image2:  
                # 如果 image2 有 alpha 通道，则为 image1 添加 alpha 通道  
                alpha_channel = torch.ones((*image1.shape[:-1], channels_image2 - channels_image1), device=image1.device)  
                alpha_channel_mask = torch.ones((*mask2.shape[:-1], channels_mask2 - channels_mask1), device=mask1.device)  
                image1 = torch.cat((image1, alpha_channel), dim=-1)  
                mask1 = torch.cat((mask1, alpha_channel_mask), dim=-1)  
            else:  
                # 如果 image1 有 alpha 通道，则为 image2 添加 alpha 通道  
                alpha_channel = torch.ones((*image2_resized.shape[:-1], channels_image1 - channels_image2), device=image2_resized.device)  
                alpha_channel_mask = torch.ones((*mask2_resized.shape[:-1], channels_mask1 - channels_mask2), device=mask2_resized.device)  
                image2_resized = torch.cat((image2_resized, alpha_channel), dim=-1)  
                mask2_resized = torch.cat((mask2_resized, alpha_channel_mask), dim=-1) 


        # 根据指定的方向进行拼接  
        if direction == 'right':  
            concatenated_image = torch.cat((image1, image2_resized), dim=2)  # 沿宽度拼接  
            concatenated_mask = torch.cat((mask1, mask2_resized), dim=2)  # 沿宽度拼接  
        elif direction == 'down':  
            concatenated_image = torch.cat((image1, image2_resized), dim=1)  # 沿高度拼接  
            concatenated_mask = torch.cat((mask1, mask2_resized), dim=1)  # 沿高度拼接  
        elif direction == 'left':  
            concatenated_image = torch.cat((image2_resized, image1), dim=2)  # 沿宽度拼接  
            concatenated_mask = torch.cat((mask2_resized, mask1), dim=2)  # 沿宽度拼接  
        elif direction == 'up':  
            concatenated_image = torch.cat((image2_resized, image1), dim=1)  # 沿高度拼接  
            concatenated_mask = torch.cat((mask2_resized, mask1), dim=1)  # 沿高度拼接  

        return concatenated_image, concatenated_mask
    
NODE_CLASS_MAPPINGS = {
    "ImageAndMaskConcatenationNode": ImageAndMaskConcatenationNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageAndMaskConcatenationNode": "Smell Image And Mask Concatenation Node",
}