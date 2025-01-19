
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
    CATEGORY = "Eden 🌱/Logic"
    
    def return_based_on_bool(self, ANY, IF_TRUE, IF_FALSE):
        result_str = "True" if ANY else "False"
        print(f"Evaluating {type(ANY)}, *** {ANY} *** as {result_str}")
        return (IF_TRUE if ANY else IF_FALSE,)

NODE_CLASS_MAPPINGS = {
    "IfAnyExecute": IfAnyExecute,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IfAnyExecute": "Smell If Any Execute",
}