import re


def remove_think_content(text):  
    pattern = re.compile(r'\n*\s*<think>[\s\S]*?</think>\s*\n*', re.MULTILINE)
    cleaned_text, num_subs = pattern.subn('\n', text)
    return cleaned_text

def remove_extra_blank_lines(text):  
    pattern = re.compile(r'\n{3,}', re.MULTILINE)
    cleaned_text, num_subs = pattern.subn('\n\n', text)
    return cleaned_text

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

NODE_CLASS_MAPPINGS = {
    "LargeModelCleanOutput": LargeModelCleanOutput,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LargeModelCleanOutput": "Smell Large Model Clean Output",
}