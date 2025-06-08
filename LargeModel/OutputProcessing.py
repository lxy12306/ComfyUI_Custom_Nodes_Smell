import re
import json

def remove_think_content(text):
    pattern = re.compile(r'\n*\s*<think>[\s\S]*?</think>\s*\n*', re.MULTILINE)
    cleaned_text, num_subs = pattern.subn('\n', text)
    return cleaned_text

def remove_extra_blank_lines(text):
    pattern = re.compile(r'\n{3,}', re.MULTILINE)
    cleaned_text, num_subs = pattern.subn('\n\n', text)
    return cleaned_text

def extract_multiple_json_to_dict(input_string):
    """
    从输入字符串中提取所有 JSON 对象并转换为字典列表，支持嵌套 JSON。
    :param input_string: 包含多个 JSON 对象的字符串
    :return: 包含所有JSON对象的字典列表
    """
    results = []
    json_pattern = re.compile(r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}))*\})', re.DOTALL)

    matches = json_pattern.finditer(input_string)

    for match in matches:
        json_str = match.group(0)
        try:
            json_dict = json.loads(json_str)
            results.append(json_dict)
        except json.JSONDecodeError as e:
            print(f"警告: 无法解析JSON: {e}")

    if not results:
        print("在输入字符串中未找到有效的JSON对象")

    return results

def get_json(text):
    """
    从输入字符串中提取所有 JSON 对象
    :param text: 包含 JSON 对象的字符串
    :return: 单个JSON对象(第一个)或JSON对象列表(如果找到多个)
    """
    try:
        json_objects = extract_multiple_json_to_dict(text)
        if not json_objects:
            return None
        return json_objects
    except Exception as e:
        print(f"提取JSON时出错: {e}")
        return None

class LargeModelCleanOutput:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("ModifiedString",)
    FUNCTION = "process_strings"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/LargeModel/OutputProc"
    DESCRIPTION = "清理大模型的输出"

    def process_strings(self, text):

        ret_text =  remove_think_content(text)
        ret_text =  remove_extra_blank_lines(ret_text)
        return (ret_text,)

class LargeModelOutputGetJson:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("JSON", "STRING")
    RETURN_NAMES = ("ret", "ret_str")
    FUNCTION = "process_strings"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/LargeModel/OutputProc"
    DESCRIPTION = "从大模型的输出中获取json"

    def process_strings(self, text):

        ret_text =  remove_think_content(text)
        ret_text =  remove_extra_blank_lines(ret_text)
        ret = get_json(ret_text)
        return (ret, ret_text)

NODE_CLASS_MAPPINGS = {
    "LargeModelCleanOutput": LargeModelCleanOutput,
    "LargeModelOutputGetJson": LargeModelOutputGetJson,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LargeModelCleanOutput": "Smell Large Model Clean Output",
    "LargeModelOutputGetJson": "Smell Large Model Output Get Json",
}