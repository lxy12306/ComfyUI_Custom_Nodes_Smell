from .libs.util import *
from .libs.function import *
import json

any_type = AlwaysEqualProxy("*")

class IfAnyExecute:
    """
    This node executes IF_TRUE if ANY is True, otherwise it executes IF_FALSE.
    ANY can be any input, IF_TRUE and IF_FALSE can be any output.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ANY": (any_type,),
                "IF_TRUE": (any_type,),
                "IF_FALSE": (any_type,),
            },
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("?",)
    FUNCTION = "return_based_on_bool"
    CATEGORY = "🌱SmellCommon/Logic"

    def return_based_on_bool(self, ANY, IF_TRUE, IF_FALSE):
        result_str = "True" if ANY else "False"
        print(f"Evaluating {type(ANY)}, *** {ANY} *** as {result_str}")
        return (IF_TRUE if ANY else IF_FALSE,)

class BOOL:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "value": ("BOOLEAN", {"default": True}),
        },
        }
    RETURN_TYPES = ("BOOLEAN", "STRING")
    RETURN_NAMES = ("value", "ret_str")
    FUNCTION = "get_value"
    CATEGORY = "🌱SmellCommon/Logic"

    def get_value(self, value):
        ret_str = "False"
        if value :
            ret_str = "True"
        return (value, ret_str)


class showAnything:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}, "optional": {"anything": (any_type, {}), },
                "hidden": {"unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO",
                           }}

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ('output',)
    INPUT_IS_LIST = True
    OUTPUT_NODE = True
    FUNCTION = "log_input"
    CATEGORY = "🌱SmellCommon/Logic"

    def log_input(self, unique_id=None, extra_pnginfo=None, **kwargs):

        values = []
        if "anything" in kwargs:
            for val in kwargs['anything']:
                try:
                    if type(val) is str:
                        values.append(val)
                    else:
                        val = json.dumps(val)
                        values.append(str(val))
                except Exception:
                    values.append(str(val))
                    pass

        if not extra_pnginfo:
            print("Error: extra_pnginfo is empty")
        elif (not isinstance(extra_pnginfo[0], dict) or "workflow" not in extra_pnginfo[0]):
            print("Error: extra_pnginfo[0] is not a dict or missing 'workflow' key")
        else:
            workflow = extra_pnginfo[0]["workflow"]
            node = next((x for x in workflow["nodes"] if str(x["id"]) == unique_id[0]), None)
            if node:
                node["widgets_values"] = [values]
        if isinstance(values, list) and len(values) == 1:
            return {"ui": {"text": values}, "result": (values[0],), }
        else:
            return {"ui": {"text": values}, "result": (values,), }

NODE_CLASS_MAPPINGS = {
    "IfAnyExecute": IfAnyExecute,
    "BOOL": BOOL,
    "Smell_showAnything": showAnything
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IfAnyExecute": "Smell If Any Execute",
    "BOOL": "Smell Bool",
    "Smell_showAnything": "Smell Show Anything"
}