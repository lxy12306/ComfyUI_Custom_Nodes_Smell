
class AlwaysEqualProxy(str):
    def __eq__(self, _):
        return True

    def __ne__(self, _):
        return False


class IfAnyExecute:
    """
    This node executes IF_TRUE if ANY is True, otherwise it executes IF_FALSE.
    ANY can be any input, IF_TRUE and IF_FALSE can be any output.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ANY": (AlwaysEqualProxy("*"),),
                "IF_TRUE": (AlwaysEqualProxy("*"),),
                "IF_FALSE": (AlwaysEqualProxy("*"),),
            },
        }

    RETURN_TYPES = (AlwaysEqualProxy("*"),)
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

NODE_CLASS_MAPPINGS = {
    "IfAnyExecute": IfAnyExecute,
    "BOOL": BOOL,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IfAnyExecute": "Smell If Any Execute",
    "BOOL": "Smell Bool",
}