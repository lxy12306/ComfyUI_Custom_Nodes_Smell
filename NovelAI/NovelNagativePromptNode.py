import json  
import os  

class NovelNagativePromptManager:  
    def __init__(self, json_name):  
        self.json_name = json_name  
        self.json_dir = r"custom_nodes\ComfyUI_Custom_Nodes_Smell\NovelAI\json"  # 使用原始字符串  

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
        with open(json_file_path, 'w', encoding='utf-8') as file:  
            json.dump({"nagative_prompts": prompts}, file, ensure_ascii=False, indent=2)  

    def load_prompts(self):  
        """公开方法，加载提示词"""  
        return self.__load_prompts("nagative_prompts")  

    def load_prompts_translation(self):  
        """公开方法，加载提示词"""  
        return self.__load_prompts("negative_prompts_translation")  

    def save_prompts(self, prompts):  
        """公开方法，保存提示词"""  
        self.__save_prompts(prompts)

class NovelNagativePromptNode:  
    @classmethod  
    def INPUT_TYPES(cls):  
        return {  
            "required": {  
                "quality_prefix": ("STRING", {"tooltip": "Quality prefix input", "multiline": True}),  
                "object": ("STRING", {"tooltip": "Object input", "multiline": True}),  
            },
        }  

    RETURN_TYPES = ("STRING",)  
    RETURN_NAMES = ("nagative_promt",)  
    FUNCTION = "create_prompt"  
    CATEGORY = "NovelAI"  
    DESCRIPTION = "Create nagative prompt strings for NovelAI"  

    def create_prompt(self, quality_prefix, object):
        
        # 否则拼接输入字符串  
        components = [quality_prefix, object]  
        concatenated_result = ", ".join(filter(None, components))  
        return (concatenated_result,)  

class NovelNagativeQualityTemplateSelectorNode:  
    @classmethod  
    def INPUT_TYPES(cls):  
        # 从已有提示词中生成下拉框选项  
        cls.prompt_manager = NovelNagativePromptManager(r"bad_quality.json")  
        prompts = cls.load_prompts()
        
        prompt_options = [(key) for key, _ in prompts.items()]  
        prompt_options.append("None")

        return {  
            "required": {  
                "selected_prompt1": (sorted(prompt_options), {"tooltip": "选择的提示词"}),  
            },  
            "optional": {  
                "selected_prompt2": (sorted(prompt_options), {"tooltip": "选择的提示词"}),  
                "selected_prompt3": (sorted(prompt_options), {"tooltip": "选择的提示词"}),  
                "selected_prompt4": (sorted(prompt_options), {"tooltip": "选择的提示词"}),  
                "selected_prompt5": (sorted(prompt_options), {"tooltip": "选择的提示词"}), 
                "new_prompt_title": ("STRING", {"tooltip": "新提示词的标题"}),  
                "new_prompt": ("STRING", {"tooltip": "添加的新提示词"}),  
            },  
        }  

    RETURN_TYPES = ("STRING","STRING")  
    RETURN_NAMES = ("current_prompts","current_prompts_translation")  
    FUNCTION = "process_prompts"  
    CATEGORY = "NovelAI"  
    DESCRIPTION = "选择和添加提示词"  

    @classmethod  
    def load_prompts(cls):  
        return cls.prompt_manager.load_prompts()  
    @classmethod  
    def load_prompts_translation(cls):  
        return cls.prompt_manager.load_prompts_translation()  


    @classmethod  
    def save_prompts(cls, prompts):  
        cls.prompt_manager.save_prompts(prompts)  

    def process_prompts(self, selected_prompt1, selected_prompt2=None, selected_prompt3=None, selected_prompt4=None, selected_prompt5=None, new_prompt_title=None, new_prompt=None):  
        """处理输入并更新输出"""  
        prompts = self.load_prompts()  
        prompts_translation = self.load_prompts_translation()  
        # 选择提示词 
        selected_prompts = [selected_prompt1, selected_prompt2, selected_prompt3, selected_prompt4, selected_prompt5]  
        current_prompts = []
        current_prompts_translation = []

        # 遍历每个选择的提示  
        for selected_prompt in selected_prompts:  
            value = prompts.get(selected_prompt, None)  # 获取提示  

            if value is not None:  # 检查是否非空  
                current_prompts.append(value)   
                value2 = prompts_translation.get(selected_prompt, None)  # 获取提示  
                if value2 is not None:
                    current_prompts_translation.append(value2) 
                else :
                    current_prompts_translation.append(value)
        
        print(current_prompts)

        # 添加新提示词  
        if new_prompt and new_prompt_title:  
            # 生成新的键名  
            new_key = new_prompt_title  # 使用用户提供的标题作为键名  
            if new_key not in prompts:  
                prompts[new_key] = new_prompt  
                self.save_prompts(prompts)  
                print(f"已添加提示词: {new_prompt}，标题: {new_prompt_title}")  
                current_prompts.append(new_prompt)
            else:  
                print(f"提示词标题 '{new_prompt_title}' 已存在。")  

        concatenated_result = ",".join(filter(None, current_prompts))  
        concatenated_result_translation = ",".join(filter(None, current_prompts_translation))  
        print(concatenated_result)
        return (concatenated_result, concatenated_result_translation)  

NODE_CLASS_MAPPINGS = {
    "NovelNagativePromptNode": NovelNagativePromptNode,
    "NovelNagativeQualityTemplateSelectorNode": NovelNagativeQualityTemplateSelectorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NovelNagativePromptNode": "Novel Nagative Prompt",
    "NovelNagativeQualityTemplateSelectorNode": "Novel Nagative Quality TemplateSelector Node",
}