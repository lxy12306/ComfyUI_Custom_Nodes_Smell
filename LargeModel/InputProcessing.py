import json  
import os  

class LargeModelRoleManager:  

    def __init__(self):  
        self.current_file_dir = os.path.dirname(__file__)
        self.json_name = "role.json"  
        self.json_dir = os.path.join(self.current_file_dir, "json")

    def __load_prompts(self, key):  
        """从 JSON 文件加载提示词"""  
        json_file_path = os.path.join(os.getcwd(), self.json_dir, self.json_name)  
        print(f"{json_file_path}")
        if not os.path.exists(json_file_path):  
            return {}  
        with open(json_file_path, 'r', encoding='utf-8') as file:  
            data = json.load(file)  
            return data.get(key, {})  

    def __save_prompts(self, prompts):  
        """将提示词保存到 JSON 文件"""  
        
        json_file_path = os.path.join(os.getcwd(), self.json_dir, self.json_name)

        # 读取现有的 JSON 文件内容  
        with open(json_file_path, 'r', encoding='utf-8') as file:  
            data = json.load(file)  # 读取整个 JSON 数据  

        # 更新 prompts 项  
        data["prompts"] = prompts  

        # 将更新后的数据写回 JSON 文件  
        with open(json_file_path, 'w', encoding='utf-8') as file:  
            json.dump(data, file, ensure_ascii=False, indent=2)   

    def load_roles(self):  
        """公开方法，加载提示词"""  
        return self.__load_prompts("prompts")  

    def load_examples(self):  
        """公开方法，加载提示词"""  
        return self.__load_prompts("examples")  

    def save_prompts(self, prompts):  
        """公开方法，保存提示词"""  
        self.__save_prompts(prompts)

class LargeModelRoleSelectorNode:  
    @classmethod  
    def INPUT_TYPES(cls):  
        # 从已有提示词中生成下拉框选项  
        cls.role_manager = LargeModelRoleManager()  
        cls.roles = cls.role_manager.load_roles()
        cls.examples = cls.role_manager.load_examples()
        
        role_options = [(key) for key, _ in cls.roles.items()]  
        role_options.append("None")

        return {
            "required": {  
                "role": (sorted(role_options), {"tooltip": "选择的角色"}),  
                "user_input": ("STRING", {"tooltip": "user_input", "multiline": True}),
                "output_limit" : ("INT", { "default": 256, "min": 1, "max": 9999999, "step": 1 }),
            },
            "optional": {  
                "old_prompt": ("STRING", {"tooltip": "old_prompt", "multiline": True}),
                "new_prompt": ("STRING", {"tooltip": "new_prompt", "multiline": True}),
            },
        }

    RETURN_TYPES = ("STRING","STRING")  
    RETURN_NAMES = ("system","prompt")  
    FUNCTION = "process_roles"  
    
    CATEGORY = "🌱SmellCommon/LargeModel/InputProc" 
    DESCRIPTION = "roles选择器"

    def process_roles(cls, role, user_input, output_limit, old_prompt=None, new_prompt=None):
        role_str = cls.roles[role]
        role_str = role_str.replace("\"keyword_num\"", f"{output_limit}")
        if "DeleteKeyword" in role:
            if old_prompt is not None:
                role_str = role_str.replace("subject_old", old_prompt)
        elif "ReplaceKeyword" in role:
            if old_prompt is not None and new_prompt is not None:
                role_str = role_str.replace("subject_old", old_prompt)
                role_str = role_str.replace("subject_new", new_prompt)
        elif "ImageToVedio" in role:
            if new_prompt is not None:
                role_str = role_str.replace("action_new", new_prompt)
        example_str = cls.examples[role]

        promt = role_str + "# Original Text \"\"\" {} \"\"\"".format(user_input)
        system = role_str + "# Example \"\"\" {} \"\"\"".format(example_str)

        return (system, promt)

NODE_CLASS_MAPPINGS = {
    "LargeModelRoleSelectorNode": LargeModelRoleSelectorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LargeModelRoleSelectorNode": "Smell Large Model Role Selector Node",
}