from .libs.function import *
from .libs.os_function import *
from .libs.image_function import *
import os


class TagFilter:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_string": ("STRING",),
                "good_substrings": ("STRING",),  # Multiple good substrings
                "bad_substrings": ("STRING",),    # Multiple bad substrings
                "max_length": ("INT",)
            }
        }

    FUNCTION = "process_strings"
    RETURN_TYPES = ("BOOLEAN", "STRING")
    RETURN_NAMES = ("pass", "org_input")
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/TagFunc"
    DESCRIPTION = "Tag Filter Node"

    def process_strings(self, input_string, good_substrings, bad_substrings, max_length):
        if len(input_string) > max_length:
            smell_debug(f"输入字符串的长度 {len(input_string)} 超过最大限制 {max_length}。")
            return (False, input_string)

        good_substrings = good_substrings.strip()
        bad_substrings = bad_substrings.strip()

        good_substring_list = [substr.strip() for substr in good_substrings.split(",")]
        bad_substring_list = [substr.strip() for substr in bad_substrings.split(",")]

        if bad_substrings != "" and any(substr in input_string for substr in bad_substring_list):
            smell_debug(f"检测到输入字符串包含不良子串: {', '.join([substr for substr in bad_substring_list if substr in input_string])}。")
            return (False, input_string)

        if good_substrings != "" and not all(substr in input_string for substr in good_substring_list):
            smell_debug(f"输入字符串缺少必需的良好子串: {', '.join([substr for substr in good_substring_list if substr not in input_string])}。")
            return (False, input_string)

        return (True, input_string)

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
                "case_sensitive": ("BOOLEAN", {"default": False})
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("ModifiedString", "DeleteString")
    FUNCTION = "process_strings"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/TagFunc"
    DESCRIPTION = "Remove elements from org string if target exists in them"

    @classmethod
    def process_strings(self, org, targets, instert_first, case_sensitive):
        elements = [elem.strip() for elem in org.split(",")]
        target_list = [t.strip() for t in targets.split(",")]
        result = []
        not_result = []

        for element in elements:
            should_keep = True
            for target in target_list:
                if (case_sensitive and target in element) or (not case_sensitive and target.lower() in element.lower()):
                    should_keep = False
                    break
            if should_keep:
                result.append(element)
            else:
                not_result.append(element)

        if instert_first:
            result = target_list + result
        new_string = ",".join(result)
        delete_string = ",".join(not_result)
        return (new_string, delete_string)

class TagLoader:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "BaseDirectory": ("STRING", {}),
                "FilenamePrefix1": ("STRING", {"default": "Image"}),
                "number": ("INT", {"default": 0}),
            },
            "optional": {
                "FilenamePrefix2": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("Tag",)
    FUNCTION = "tag_loader"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/TagFunc"
    DESCRIPTION = "Load tag"

    @classmethod
    def tag_loader(self, BaseDirectory, FilenamePrefix1, number, FilenamePrefix2=None):
        number_str = str(number).zfill(4)
        Directory, FilenamePrefix = get_dir_and_prefix(BaseDirectory, FilenamePrefix1, FilenamePrefix2)
        file_path = os.path.join(Directory, f"{FilenamePrefix}_{number_str}.txt")
        print(file_path)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                return (content,)
        else:
            return (None,)

class ImageAndTagLoader:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ForceLoadImage": ("BOOLEAN", {"default": False}),
                "BaseDirectory": ("STRING", {}),
                "FilenamePrefix1": ("STRING", {"default": "Image"}),
            },
            "optional": {
                "FilenamePrefix2": ("STRING", {"default": ""}),
                "load_cap": ("INT", {"default": 0}),
                "start_index": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "MASK", "INT")
    RETURN_NAMES = ("IMAGE", "Tag", "Mask", "Index")
    OUTPUT_IS_LIST = (True, True, True, True)
    FUNCTION = "image_and_tag_loader"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/TagFunc"
    DESCRIPTION = "Load tag"

    @classmethod
    def image_and_tag_loader(self, ForceLoadImage, BaseDirectory, FilenamePrefix1, FilenamePrefix2=None, load_cap=0, start_index=0):
        Directory, FilenamePrefix = get_dir_and_prefix(BaseDirectory, FilenamePrefix1, FilenamePrefix2)
        if not os.path.isdir(Directory):
            raise FileNotFoundError(f"Directory '{Directory}' cannot be found.")
        dir_files = os.listdir(Directory)
        if len(dir_files) == 0:
            raise FileNotFoundError(f"No files in directory '{Directory}'.")

        # Filter files by extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        dir_files = [f for f in dir_files if any(f.lower().endswith(ext) for ext in valid_extensions)]

        dir_files = sorted(dir_files)
        dir_files = [os.path.join(Directory, x) for x in dir_files]
        txt_files = [f.rsplit('.', 1)[0] + '.txt' for f in dir_files]

        # start at start_index
        dir_files = dir_files[start_index:]
        txt_files = txt_files[start_index:]

        images = []
        masks = []
        tags = []
        indexs = []

        limit_images = False
        if load_cap > 0:
            limit_images = True
        image_count = 0

        for i in range(len(dir_files)):
            image_path = dir_files[i]
            txt_path = txt_files[i]
            if os.path.isdir(image_path) or os.path.isdir(txt_path):
                continue
            if not os.path.exists(txt_path) and not ForceLoadImage:
                continue
            if limit_images and image_count >= load_cap:
                break
            image, mask = load_image_from_path(image_path)

            images.append(image)
            masks.append(mask)
            if not os.path.exists(txt_path):
                tag = ""
            else :
                with open(txt_path, 'r') as file:
                   tag = file.read()
            tags.append(tag)
            indexs.append(image_count)
            image_count += 1

        return (images, tags, masks, indexs)

class TagSaver:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "BaseDirectory": ("STRING", {}),
                "FilenamePrefix1": ("STRING", {"default": "Image"}),
                "number": ("INT", {"default": 1}),
                "tag": ("STRING", {"default": ""}),
            },
            "optional": {
                "FilenamePrefix2": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "tag_saver"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/TagFunc"
    DESCRIPTION = "Save tag"

    @classmethod
    def tag_saver(self, BaseDirectory, FilenamePrefix1, number, tag, FilenamePrefix2=None):
        number_str = str(number).zfill(4)
        Directory, FilenamePrefix = get_dir_and_prefix(BaseDirectory, FilenamePrefix1, FilenamePrefix2)
        file_path = os.path.join(Directory, f"{FilenamePrefix}_{number_str}.txt")
        if tag != "":
            smell_write_text_file(file_path, tag)
        return ()

NODE_CLASS_MAPPINGS = {
    "TagFilter": TagFilter,
    "TagDeleteNode": TagDeleteNode,
    "TagLoader": TagLoader,
    "TagSaver": TagSaver,
    "ImageAndTagLoader": ImageAndTagLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TagFilter": "Smell Tag Filter",
    "TagDeleteNode": "Smell Image Tag Delete Node",
    "TagLoader": "Smell Tag Loader",
    "TagSaver": "Smell Tag Saver",
    "ImageAndTagLoader": "Smell Image And Tag Loader",
}