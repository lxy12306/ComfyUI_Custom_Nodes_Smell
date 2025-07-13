import torch 
from comfy.comfy_types import IO
import node_helpers


class FluxKontextInpaintingConditioning:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"conditioning": ("CONDITIONING", ),
                             "vae": ("VAE", ),
                             "pixels": ("IMAGE", ),
                             "mask": ("MASK", ),
                             "noise_mask": ("BOOLEAN", {"default": True, "tooltip": "Add a noise mask to the latent so sampling will only happen within the mask. Might improve results or completely break things depending on the model."}),
                             }}

    RETURN_TYPES = ("CONDITIONING","LATENT")
    RETURN_NAMES = ("conditioning", "latent")
    FUNCTION = "encode"

    CATEGORY = "conditioning/inpaint"

    def _encode_latent(self, vae, pixels):
        t = vae.encode(pixels[:,:,:,:3])
        return {"samples":t}

    def _concat_conditioning_latent(self, conditioning, latent=None):
        if latent is not None:
            conditioning = node_helpers.conditioning_set_values(conditioning, {"reference_latents": [latent["samples"]]}, append=True)
        return conditioning


    def encode(self, conditioning, pixels, vae, mask, noise_mask=True):
        x = (pixels.shape[1] // 8) * 8
        y = (pixels.shape[2] // 8) * 8
        mask = torch.nn.functional.interpolate(mask.reshape((-1, 1, mask.shape[-2], mask.shape[-1])), size=(pixels.shape[1], pixels.shape[2]), mode="bilinear")

        orig_pixels = pixels
        pixels = orig_pixels.clone()
        if pixels.shape[1] != x or pixels.shape[2] != y:
            x_offset = (pixels.shape[1] % 8) // 2
            y_offset = (pixels.shape[2] % 8) // 2
            pixels = pixels[:,x_offset:x + x_offset, y_offset:y + y_offset,:]
            mask = mask[:,:,x_offset:x + x_offset, y_offset:y + y_offset]

        m = (1.0 - mask.round()).squeeze(1)
        for i in range(3):
            pixels[:,:,:,i] -= 0.5
            pixels[:,:,:,i] *= m
            pixels[:,:,:,i] += 0.5
        concat_latent = vae.encode(pixels)
        orig_latent = vae.encode(orig_pixels)

        pixels_latent = self._encode_latent(vae, orig_pixels)

        c = node_helpers.conditioning_set_values(conditioning, {"concat_latent_image": concat_latent,
                                                                "concat_mask": mask})
        conditioning = self._concat_conditioning_latent(c, pixels_latent)

        out_latent = {}

        out_latent["samples"] = orig_latent
        if noise_mask:
            out_latent["noise_mask"] = mask

        return (conditioning, out_latent)

    def encdasdsaode(self, positive, negative, pixels, vae, mask, noise_mask=True):
        x = (pixels.shape[1] // 8) * 8
        y = (pixels.shape[2] // 8) * 8
        mask = torch.nn.functional.interpolate(mask.reshape((-1, 1, mask.shape[-2], mask.shape[-1])), size=(pixels.shape[1], pixels.shape[2]), mode="bilinear")

        orig_pixels = pixels
        pixels = orig_pixels.clone()
        if pixels.shape[1] != x or pixels.shape[2] != y:
            x_offset = (pixels.shape[1] % 8) // 2
            y_offset = (pixels.shape[2] % 8) // 2
            pixels = pixels[:,x_offset:x + x_offset, y_offset:y + y_offset,:]
            mask = mask[:,:,x_offset:x + x_offset, y_offset:y + y_offset]

        m = (1.0 - mask.round()).squeeze(1)
        for i in range(3):
            pixels[:,:,:,i] -= 0.5
            pixels[:,:,:,i] *= m
            pixels[:,:,:,i] += 0.5
        concat_latent = vae.encode(pixels)
        orig_latent = vae.encode(orig_pixels)

        out_latent = {}

        out_latent["samples"] = orig_latent
        if noise_mask:
            out_latent["noise_mask"] = mask

        out = []
        for conditioning in [positive, negative]:
            c = node_helpers.conditioning_set_values(conditioning, {"concat_latent_image": concat_latent,
                                                                    "concat_mask": mask})
            out.append(c)
        return (out[0], out[1], out_latent)
