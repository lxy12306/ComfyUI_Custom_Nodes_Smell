import math
import comfy.utils
import torch
import numpy as np
from PIL import Image, ImageChops

def tensor_to_pil(tensor_image):
    # Check if the input is a batch of images  
    if tensor_image.ndim == 4:  # Batch of images (N, C, H, W)  
        pil_images = []  
        for i in range(tensor_image.shape[0]):  
            img = tensor_image[i].squeeze(0)  # Remove the channel dimension  
            pil_image = Image.fromarray((img.cpu().numpy() * 255).astype(np.uint8))  
            pil_images.append(pil_image)  
        return pil_images  # Return a list of PIL images  
    else:  # Single image (C, H, W)  
        tensor_image = tensor_image.squeeze(0)  
        pil_image = Image.fromarray((tensor_image.cpu().numpy() * 255).astype(np.uint8))  
        return [pil_image] 
def pil_to_tensor(pil_image):  
    # Check if the input is a list of images  
    if isinstance(pil_image, list):  
        tensors = []  
        for pil_image in pil_image:  
            tensor = torch.from_numpy(np.array(pil_image).astype(np.float32) / 255).unsqueeze(0)  
            tensors.append(tensor)  
        return torch.cat(tensors, dim=0)  # Concatenate tensors along the batch dimension  
    else:  # Single image  
        return torch.from_numpy(np.array(pil_image).astype(np.float32) / 255).unsqueeze(0)  
    
def generate_gaussian_noise(width, height, noise_scale=0.05):
        noise = np.random.normal(128, 128 * noise_scale, (height, width, 3)).astype(np.uint8)
        return Image.fromarray(noise)


class HighresFixScaler:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "vae": ("VAE",),
                "magnification": ("FLOAT", {"default": 1, "min": 1, "max": 8}),
                "upscale_method": (["nearest-exact", "bilinear", "area", "bicubic", "lanczos"],),
                "inject_func": (["darker", "soft_light", "lighter"],),
                "noise_scale": ("FLOAT", {"default": 0.40, "min": 0.00, "max": 100.00, "step": 0.01}),
                "blend_opacity": ("INT", {"default": 20, "min": 0, "max": 100}),
            },
            "optional": {
                "mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "scale_and_encode"
    CATEGORY = "🌱SmellCommon/Noise"
    def soft_light_blend(self, base_images, noise_image, inject_func, mask=None, opacity=15):  
        # Resize noise image to match the size of the base images  
        noise_image = noise_image.resize(base_images[0].size)  
        noise_image = noise_image.convert('RGB')  

        blended_images = []  

        if mask is not None:  
            mask_pils = tensor_to_pil(mask)

        
        for i in range(0, len(base_images)):  
            base_image = base_images[i]
            base_image = base_image.convert('RGB')  

            if inject_func == "soft_light":  
                noise_blended = ImageChops.soft_light(base_image, noise_image)  
            elif inject_func == "darker":  
                noise_blended = ImageChops.darker(base_image, noise_image)  
            elif inject_func == "lighter":  
                noise_blended = ImageChops.lighter(base_image, noise_image)  

            blended_image = Image.blend(base_image, noise_blended, opacity / 100)  

            if mask is not None:  
                mask_pil = mask_pils[i].convert('L') 
                mask_resized = mask_pil.resize(base_image.size)  
                inverted_mask = ImageChops.invert(mask_resized)  
                blended_image = Image.composite(base_image, blended_image, inverted_mask)  

            blended_images.append(blended_image)  

        return blended_images  # Return a list of blended images  

    def scale_and_encode(self, image, vae, magnification, upscale_method, inject_func, noise_scale=0.40, blend_opacity=20, mask=None):
        # Calculate dimensions
        _, original_height, original_width, _ = image.shape
        
        new_height = int(int(int(magnification * original_height) / 64) * 64)
        new_width = int(int(int(magnification * original_width) / 64) * 64) 

        # Upscale
        samples = image.movedim(-1, 1)
        scaled = comfy.utils.common_upscale(samples, new_width, new_height, upscale_method, "disabled")
        scaled = scaled.movedim(1, -1)

        # Apply noise and blend
        scaled_pils = tensor_to_pil(scaled)
        noise_image = generate_gaussian_noise(new_width, new_height, noise_scale)
        blended_images = self.soft_light_blend(scaled_pils, noise_image, inject_func, mask, blend_opacity)
        blended_tensor = pil_to_tensor(blended_images)

        # Encode with VAE
        encoded = vae.encode(blended_tensor[:, :, :, :3])
        return ({"samples": encoded},)


class Noise_CustomNoise:
    def __init__(self, noise_latent):
        self.seed = 0
        self.noise_latent = noise_latent

    def generate_noise(self, input_latent):
        return self.noise_latent.detach().clone().cpu()

class CustomNoise:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":{
            "noise": ("LATENT",),
            }}

    RETURN_TYPES = ("NOISE",)
    FUNCTION = "get_noise"
    CATEGORY = "🌱SmellCommon/Noise"

    def get_noise(self, noise):
        noise_latent = noise["samples"].detach().clone()
        std, mean = torch.std_mean(noise_latent, dim=(-2, -1), keepdim=True)
        noise_latent = (noise_latent - mean) / std
        return (Noise_CustomNoise(noise_latent),)

NODE_CLASS_MAPPINGS = {
    "HighresFixScaler": HighresFixScaler,
    "CustomNoise": CustomNoise,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HighresFixScaler": "Smell HighresFixScaler",
    "CustomNoise": "Smell CustomNoise",
}