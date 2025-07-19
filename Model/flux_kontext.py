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

class KontextPresets:
    data = {
    "prefix": "You are a creative prompt engineer. Your mission is to analyze the provided image and generate exactly 1 distinct image transformation *instructions*.",
    "presets": [
        {
        "name": "Komposer Teleport",
        "brief": "Teleport the subject to a random location, scenario and/or style. Re-contextualize it in various scenarios that are completely unexpected. Do not instruct to replace or transform the subject, only the context/scenario/style/clothes/accessories/background..etc."
        },
        {
        "name": "Move Camera",
        "brief": "Move the camera to reveal new aspects of the scene. Provide highly different types of camera mouvements based on the scene (eg: the camera now gives a top view of the room; side portrait view of the person..etc )."
        },
        {
        "name": "Relight",
        "brief": "Suggest new lighting settings for the image. Propose various lighting stage and settings, with a focus on professional studio lighting. Some suggestions should contain dramatic color changes, alternate time of the day, remove or include some new natural lights...etc"
        },
        {
        "name": "Product",
        "brief": "Turn this image into the style of a professional product photo. Describe a variety of scenes (simple packshot or the item being used), so that it could show different aspects of the item in a highly professional catalog. Suggest a variety of scenes, light settings and camera angles/framings, zoom levels, etc. Suggest at least 1 scenario of how the item is used."
        },
        {
        "name": "Zoom",
        "brief": "Zoom {{SUBJECT}} of the image. If a subject is provided, zoom on it. Otherwise, zoom on the main subject of the image. Provide different level of zooms."
        },
        {
        "name": "Colorize",
        "brief": "Colorize the image. Provide different color styles / restoration guidance."
        },
        {
        "name": "Movie Poster",
        "brief": "Create a movie poster with the subjects of this image as the main characters. Take a random genre (action, comedy, horror, etc) and make it look like a movie poster. Sometimes, the user would provide a title for the movie (not always). In this case the user provided: . Otherwise, you can make up a title based on the image. If a title is provided, try to fit the scene to the title, otherwise get inspired by elements of the image to make up a movie. Make sure the title is stylized and add some taglines too. Add lots of text like quotes and other text we typically see in movie posters."
        },
        {
        "name": "Cartoonify",
        "brief": "Turn this image into the style of a cartoon or manga or drawing. Include a reference of style, culture or time (eg: mangas from the 90s, thick lined, 3D pixar, etc)"
        },
        {
        "name": "Remove Text",
        "brief": "Remove all text from the image."
        },
        {
        "name": "Haircut",
        "brief": "Change the haircut of the subject. Suggest a variety of haircuts, styles, colors, etc. Adapt the haircut to the subject's characteristics so that it looks natural. Describe how to visually edit the hair of the subject so that it has this new haircut."
        },
        {
        "name": "Bodybuilder",
        "brief": "Ask to largely increase the muscles of the subjects while keeping the same pose and context. Describe visually how to edit the subjects so that they turn into bodybuilders and have these exagerated large muscles: biceps, abdominals, triceps, etc. You may change the clothes to make sure they reveal the overmuscled, exagerated body."
        },
        {
        "name": "Remove Furniture",
        "brief": "Remove all furniture and all appliances from the image. Explicitely mention to remove lights, carpets, curtains, etc if present."
        },
        {
        "name": "Interior Design",
        "brief": "You are an interior designer. Redo the interior design of this image. Imagine some design elements and light settings that could match this room and offer diverse artistic directions, while ensuring that the room structure (windows, doors, walls, etc) remains identical."
        }
    ],
    "suffix": "Your response must consist of concise instruction ready for the image editing AI. Do not add any conversational text, explanations, or deviations; only the instructions."
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "preset": ([preset["name"] for preset in cls.data.get("presets", [])],),
            }
        }
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("Prompt",)
    FUNCTION = "get_preset"
    CATEGORY = "utils"

    @classmethod
    def get_brief_by_name(cls, name):
        for preset in cls.data.get("presets", []):
            if preset["name"] == name:
                return preset["brief"]
        return None

    def get_preset(cls, preset):
        brief = "The Brief:"+cls.get_brief_by_name(preset)
        fullString = cls.data.get("prefix")+'\n'+brief+'\n'+cls.data.get("suffix")
        return (fullString,)