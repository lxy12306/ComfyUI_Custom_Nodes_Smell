from ollama import Client as OllamaClient
import numpy as np
from PIL import Image
from io import BytesIO
import base64
import random
import os
from PIL.PngImagePlugin import PngInfo

class OllamaVisionSimple:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        seed = random.randint(1, 2 ** 31)
        return {
            "required": {
                "images": ("IMAGE",),
                "query": ("STRING", {
                    "multiline": True,
                    "default": "describe the image"
                }),
                "debug": (["enable", "disable"],),
                "url": ("STRING", {
                    "multiline": False,
                    "default": "http://127.0.0.1:11434"
                }),
                "model": ((), {}),
                "system": ("STRING", {
                    "multiline": True,
                    "default": "Describe the input image in detail. Focus on key elements such as key objects, colors, shapes, textures, lighting, composition, and overall mood. Ensure the description is objective and clear, and avoid using any special symbols",
                    "title": "system"
                }),
                "seed": ("INT", {"default": seed, "min": 0, "max": 2 ** 31, "step": 1}),
                "top_k": ("INT", {"default": 40, "min": 0, "max": 100, "step": 1}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0, "max": 1, "step": 0.05}),
                "temperature": ("FLOAT", {"default": 0.8, "min": 0, "max": 1, "step": 0.05}),
                "num_predict": ("INT", {"default": -1, "min": -2, "max": 2048, "step": 1}),
                "tfs_z": ("FLOAT", {"default": 1, "min": 1, "max": 1000, "step": 0.05}),
                "keep_alive": ("INT", {"default": 0, "min": -1, "max": 60, "step": 1}),
                "format": (["text", "json", ''],),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("description",)
    FUNCTION = "ollama_vision_simple"
    CATEGORY = "🌱SmellCommon/LargeModel/Ollama"

    def ollama_vision_simple(self, images, query, debug, url, model, system, seed, top_k, top_p, temperature, num_predict, tfs_z, keep_alive, format):
        images_binary = []

        if format == "text":
            format = ''
        client = OllamaClient(host=url)

        if format == "text":
            format = ''

        options = {
            "seed": seed,
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "num_predict": num_predict,
            "tfs_z": tfs_z,
        }

        for (batch_number, image) in enumerate(images):
            # Convert tensor to numpy array
            i = 255. * image.cpu().numpy()

            # Create PIL Image
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            # Save to BytesIO buffer
            buffered = BytesIO()
            img.save(buffered, format="PNG")

            # Get binary data
            img_binary = buffered.getvalue()
            images_binary.append(img_binary)

        if debug == "enable":
            print(f"""[Ollama Vision]
request query params:

- query: {query}
- url: {url}
- model: {model}
- options: {options}
""")

        response = client.generate(model=model, system=system, prompt=query, images=images_binary, options=options, keep_alive=str(keep_alive) + "m", format=format)

        if debug == "enable":
            print("[Ollama Vision]\nResponse:\n")
            print(response)

        return (response['response'],)

class OllamaGenerateSimple:
    saved_context = None

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        seed = random.randint(1, 2 ** 31)
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "What is Art?"
                }),
                "debug": ("BOOLEAN", {"default": False}),
                "url": ("STRING", {
                    "multiline": False,
                    "default": "http://127.0.0.1:11434"
                }),
                "model": ((), {}),
                "system": ("STRING", {
                    "multiline": True,
                    "default": "You are an art expert, gracefully describing your knowledge in art domain.",
                    "title": "system"
                }),
                "seed": ("INT", {"default": seed, "min": 0, "max": 2 ** 31, "step": 1}),
                "top_k": ("INT", {"default": 40, "min": 0, "max": 100, "step": 1}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0, "max": 1, "step": 0.05}),
                "temperature": ("FLOAT", {"default": 0.8, "min": 0, "max": 1, "step": 0.05}),
                "num_predict": ("INT", {"default": -1, "min": -2, "max": 2048, "step": 1}),
                "tfs_z": ("FLOAT", {"default": 1, "min": 1, "max": 1000, "step": 0.05}),
                "keep_alive": ("INT", {"default": 5, "min": -1, "max": 60, "step": 1}),
                "keep_context": ("BOOLEAN", {"default": False}),
                "format": (["text", "json", ''],),
            }, "optional": {
                "context": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("response", "context",)
    FUNCTION = "ollama_generate_simple"
    CATEGORY = "🌱SmellCommon/LargeModel/Ollama"

    def ollama_generate_simple(self, prompt, debug, url, model, system, seed, top_k, top_p, temperature, num_predict, tfs_z, keep_alive, keep_context, format, context=None):

        client = OllamaClient(host=url)

        if format == "text":
            format = ''

        options = {
            "seed": seed,
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "num_predict": num_predict,
            "tfs_z": tfs_z,
        }

        if context != None and isinstance(context, str):
            string_list = context.split(',')
            context = [int(item.strip()) for item in string_list]

        if keep_context and context == None:
            context = self.saved_context

        if debug:
            print(f"""[Ollama Generate Advance]
request query params:

- prompt: {prompt}
- url: {url}
- model: {model}
- options: {options}
""")

        response = client.generate(model=model, system=system, prompt=prompt, context=context, options=options,
                                   keep_alive=str(keep_alive) + "m", format=format)
        if debug:
            print("[Ollama Generate Advance]\nResponse:\n")
            print(response)

        if keep_context:
            self.saved_context = response["context"]

        return (response['response'], response['context'],)

class OllamaSaveContext:
    def __init__(self):
        self._base_dir = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "saved_context"

    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {"context": ("STRING", {"forceInput": True},),
                     "filename": ("STRING", {"default": "context"})},
                }

    RETURN_TYPES = ()
    FUNCTION = "ollama_save_context"

    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/LargeModel/Ollama"

    def ollama_save_context(self, filename, context=None):
        path = self._base_dir + os.path.sep + filename
        metadata = PngInfo()

        metadata.add_text("context", ','.join(map(str, context)))

        image = Image.new('RGB', (100, 100), (255, 255, 255))  # Creates a 100x100 white image

        image.save(path + ".png", pnginfo=metadata)

        return {"ui": {"context": context}}

class OllamaLoadContext:
    def __init__(self):
        self._base_dir = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "saved_context"

    @classmethod
    def INPUT_TYPES(s):
        input_dir = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "saved_context"
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)) and f != ".keep"]
        return {"required":
                    {"context_file": (files, {})},
                }

    CATEGORY = "🌱SmellCommon/LargeModel/Ollama"

    RETURN_NAMES = ("context",)
    RETURN_TYPES = ("STRING",)
    FUNCTION = "ollama_load_context"

    def ollama_load_context(self, context_file):
        with Image.open(self._base_dir + os.path.sep + context_file) as img:
            info = img.info
            res = info.get('context', '')
        return (res,)

class OllamaConnectivity:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "url": ("STRING", {
                    "multiline": False,
                    "default": "http://127.0.0.1:11434"
                }),
                "model": ((), {}),
                "keep_alive": ("INT", {"default": 5, "min": -1, "max": 120, "step": 1}),
                "keep_alive_unit": (["minutes", "hours"],),
            },
        }

    RETURN_TYPES = ("OLLAMA_CONNECTIVITY",)
    RETURN_NAMES = ("connection",)
    FUNCTION = "ollama_connectivity"
    CATEGORY = "🌱SmellCommon/LargeModel/Ollama"

    def ollama_connectivity(self, url, model, keep_alive, keep_alive_unit):
        data = {
            "url": url,
            "model": model,
            "keep_alive": keep_alive,
            "keep_alive_unit": keep_alive_unit,
        }

        return (data,)

class OllamaOptionsAdvance:
# 运行时选项说明：
#
# num_keep: (Optional[int])
#   保留在内存中的先前 token 数量，有助于维护上下文或减少内存占用。
#
# seed: (Optional[int])
#   随机数生成的种子，用于使采样过程可复现。
#
# num_predict: (Optional[int])
#   生成的最大 token 数量。
#
# top_k: (Optional[int])
#   在 top-k 采样中，仅考虑概率最高的 k 个 token。
#
# top_p: (Optional[float])
#   在 nucleus (top-p) 采样中，仅考虑达到累计概率阈值的 token。
#
# tfs_z: (Optional[float])
#   尾部自由采样参数，影响根据 token 概率分布确定采样阈值。
#
# typical_p: (Optional[float])
#   典型采样参数，用于在多样性和连贯性之间取得平衡。
#
# repeat_last_n: (Optional[int])
#   用于重复惩罚的 token 数量，防止生成重复内容。
#
# temperature: (Optional[float])
#   控制生成文本的随机性，数值越低，输出越确定。
#
# repeat_penalty: (Optional[float])
#   对频繁重复的 token 增加惩罚系数。
#
# presence_penalty: (Optional[float])
#   对已经出现过的 token 进行惩罚，鼓励生成新内容。
#
# frequency_penalty: (Optional[float])
#   根据 token 的出现频率施加惩罚，防止使用过多。
#
# mirostat: (Optional[int])
#   启用 Mirostat 采样算法，通过控制困惑度来调整生成文本。
#
# mirostat_tau: (Optional[float])
#   Mirostat 算法的目标值参数。
#
# mirostat_eta: (Optional[float])
#   Mirostat 调整过程中使用的学习率参数。
#
# penalize_newline: (Optional[bool])
#   如果启用，对换行字符施加惩罚，影响文本格式。
#
# stop: (Optional[Sequence[str]])
#   当生成的文本中遇到序列列表中的特定字符串时停止生成。

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        seed = random.randint(1, 2 ** 31)
        return {
            "required": {
                "enable_num_ctx": ("BOOLEAN", {"default": True}),
                "num_ctx": ("INT", {"default": 2048, "min": 0, "max": 16384, "step": 1}),

                "enable_num_predict": ("BOOLEAN", {"default": False}),
                "num_predict": ("INT", {"default": 2048, "min": 0, "max": 16384, "step": 1}),

                "enable_seed": ("BOOLEAN", {"default": True}),
                "seed": ("INT", {"default": seed, "min": 0, "max": 2 ** 31, "step": 1}),

                "enable_top_k": ("BOOLEAN", {"default": True}),
                "top_k": ("INT", {"default": 40, "min": 0, "max": 100, "step": 1}),

                "enable_top_p": ("BOOLEAN", {"default": True}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0, "max": 1, "step": 0.05}),

                "enable_temperature": ("BOOLEAN", {"default": True}),
                "temperature": ("FLOAT", {"default": 0.8, "min": 0, "max": 1, "step": 0.05}),

                "enable_num_keep": ("BOOLEAN", {"default": False}),
                "num_keep": ("INT", {"default": 2048, "min": 0, "step": 1}),



                "enable_tfs_z": ("BOOLEAN", {"default": False}),
                "tfs_z": ("FLOAT", {"default": 1, "min": 1, "max": 1000, "step": 0.05}),

                "enable_typical_p": ("BOOLEAN", {"default": False}),
                "typical_p": ("FLOAT", {"default": 1, "min": 0, "max": 1, "step": 0.05}),

                "enable_repeat_last_n": ("BOOLEAN", {"default": False}),
                "repeat_last_n": ("INT", {"default": 64, "min": -1, "max": 64, "step": 1}),

                "enable_repeat_penalty": ("BOOLEAN", {"default": False}),
                "repeat_penalty": ("FLOAT", {"default": 1.1, "min": 0, "max": 2, "step": 0.05}),

                "enable_presence_penalty": ("BOOLEAN", {"default": False}),
                "presence_penalty": ("FLOAT", {"default": 1.1, "min": 0, "max": 2, "step": 0.05}),

                "enable_frequency_penalty": ("BOOLEAN", {"default": False}),
                "frequency_penalty": ("FLOAT", {"default": 1.1, "min": 0, "max": 2, "step": 0.05}),

                "enable_mirostat": ("BOOLEAN", {"default": False}),
                "mirostat": ("INT", {"default": 0, "min": 0, "max":2, "step": 1}),

                "enable_mirostat_tau": ("BOOLEAN", {"default": False}),
                "mirostat_tau": ("FLOAT", {"default": 5.0, "min": 0, "step": 0.1}),

                "enable_mirostat_eta": ("BOOLEAN", {"default": False}),
                "mirostat_eta": ("FLOAT", {"default": 0.1, "min": 0, "step": 0.1}),

                "debug": ("BOOLEAN", {"default": False}), # this is for nodes code usage only, not ollama api.
            },
        }

    RETURN_TYPES = ("OLLAMA_OPTIONS",)
    RETURN_NAMES = ("options",)
    FUNCTION = "ollama_options_advance"
    CATEGORY = "🌱SmellCommon/LargeModel/Ollama"

    def ollama_options_advance(self, **kargs):

        if kargs['debug']:
            print("--- ollama options advance dump\n")
            print(kargs)
            print("---------------------------------------------------------")

        return (kargs,)

class OllamaGenerateAdvance:
    def __init__(self):
        self.saved_context = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "system": ("STRING", {
                    "multiline": True,
                    "default": "You are an AI artist."
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "What is art?"
                }),
                "keep_context": ("BOOLEAN", {"default": False}),
                "format": (["text", "json"],),
                "debug": (["disable", "enable"],),
            },
            "optional": {
                "connectivity": ("OLLAMA_CONNECTIVITY", {"forceInput": False},),
                "options": ("OLLAMA_OPTIONS", {"forceInput": False},),
                "images": ("IMAGE", {"forceInput": False},),
                "context": ("OLLAMA_CONTEXT", {"forceInput": False},),
                "meta": ("OLLAMA_META", {"forceInput": False},),
            }
        }

    RETURN_TYPES = ("STRING", "OLLAMA_CONTEXT", "OLLAMA_META",)
    RETURN_NAMES = ("result", "context", "meta",)
    FUNCTION = "ollama_generate_advance"
    CATEGORY = "🌱SmellCommon/LargeModel/Ollama"

    def get_request_options(self, options):
        response = None

        if options is None:
            return response

        enablers = ["enable_num_ctx",
                    "enable_num_keep","enable_seed", "enable_num_predict", "enable_top_k",
                    "enable_top_p", "enable_tfs_z", "enable_typical_p", "enable_repeat_last_n",
                    "enable_temperature", "enable_repeat_penalty", "enable_presence_penalty",
                    "enable_frequency_penalty", "enable_mirostat", "enable_mirostat_tau",
                    "enable_mirostat_eta"]

        for enabler in enablers:
            if options[enabler]:
                if response is None:
                    response = {}
                key = enabler.replace("enable_", "")
                response[key] = options[key]

        return response

    def ollama_generate_advance(self, system, prompt, format, debug, keep_context, context = None, options=None, connectivity=None, images=None, meta=None):

        if connectivity is None and meta is None:
            raise Exception("Required input connectivity or meta.")

        if connectivity is None and meta['connectivity'] is None:
            raise Exception("Required input connectivity or connectivity in meta.")

        if meta is not None:
            if connectivity is not None: # bypass the current meta connectivity
                meta["connectivity"] = connectivity
            if options is not None: # bypass the current meta options
                meta["options"] = options
        else:
            meta = {"options": options, "connectivity": connectivity}

        url = meta['connectivity']['url']
        model = meta['connectivity']['model']
        client = OllamaClient(host=url)

        debug_print = True if debug == "enable" else False

        if format == "text":
            format = ''

        if context is not None and isinstance(context, str):
            string_list = context.split(',')
            context = [int(item.strip()) for item in string_list]

        if keep_context and context is None:
            context = self.saved_context

        keep_alive_unit =  'm' if meta['connectivity']['keep_alive_unit'] == "minutes" else 'h'
        request_keep_alive = str(meta['connectivity']['keep_alive']) + keep_alive_unit

        request_options = self.get_request_options(options)

        images_b64 = None
        if images is not None:
            images_b64 = []
            for (batch_number, image) in enumerate(images):
                i = 255. * image.cpu().numpy()
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_bytes = base64.b64encode(buffered.getvalue())
                images_b64.append(str(img_bytes, 'utf-8'))

        if debug_print:
            print(f"""
--- ollama generate advance request:

url: {url}
model: {model}
system: {system}
prompt: {prompt}
images: {0 if images_b64 is None else len(images_b64)}
context: {context}
options: {request_options}
keep alive: {request_keep_alive}
format: {format}
---------------------------------------------------------
""")

        response = client.generate(
            model=model,
            system=system,
            prompt=prompt,
            images=images_b64,
            context=context,
            options=request_options,
            keep_alive= request_keep_alive,
            format=format,
        )

        if debug_print:
            print("\n--- ollama generate advance response:")
            print(response)
            print("---------------------------------------------------------")

        if keep_context:
            self.saved_context = response["context"]
            if debug_print:
                print("saving context to node memory.")

        return response['response'], response['context'], meta,

NODE_CLASS_MAPPINGS = {
    "OllamaVisionSimple": OllamaVisionSimple,
    "OllamaGenerateSimple": OllamaGenerateSimple,
    "OllamaConnectivity" : OllamaConnectivity,
    "OllamaOptionsAdvance" : OllamaOptionsAdvance,
    "OllamaGenerateAdvance" : OllamaGenerateAdvance
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OllamaVisionSimple" : "Smell Ollama Vision Simple",
    "OllamaGenerateSimple" : "Smell Ollama Generate Simple",
    "OllamaConnectivity" : "Smell Ollama Connectivity",
    "OllamaOptionsAdvance" : "Smell Ollama Options Advance",
    "OllamaGenerateAdvance" : "Smell Ollama Generate Advance"
}