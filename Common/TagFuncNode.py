from .libs.function import *

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
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("ModifiedString",)
    FUNCTION = "process_strings"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/TagFunc"
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
    "TagFilter": TagFilter,
    "TagDeleteNode": TagDeleteNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TagFilter": "Smell Tag Filter",
    "TagDeleteNode": "Smell Image Tag Delete Node"
}