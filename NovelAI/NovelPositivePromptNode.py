import json  
import os  

class NovelPositivePromptManager:  
    def __init__(self, json_name):  
        self.json_name = json_name  
        self.json_dir = r"custom_nodes\ComfyUI_Custom_Nodes_Smell\NovelAI\json"  # 使用原始字符串  

    def __load_prompts(self):  
        """从 JSON 文件加载提示词"""  
        json_file_path = os.path.join(os.getcwd(), self.json_dir, self.json_name)  
        print(f"{json_file_path}")
        if not os.path.exists(json_file_path):  
            return {}  
        with open(json_file_path, 'r', encoding='utf-8') as file:  
            data = json.load(file)  
            return data.get("prompts", {})  

    def __save_prompts(self, prompts):  
        """将提示词保存到 JSON 文件"""  
        json_file_path = os.path.join(os.getcwd(), self.json_dir, self.json_name)  
        with open(json_file_path, 'w', encoding='utf-8') as file:  
            json.dump({"prompts": prompts}, file, ensure_ascii=False, indent=2)  

    def load_prompts(self):  
        """公开方法，加载提示词"""  
        return self.__load_prompts()  

    def save_prompts(self, prompts):  
        """公开方法，保存提示词"""  
        self.__save_prompts(prompts)

class NovelPositivePromptNode:  
    @classmethod  
    def INPUT_TYPES(cls):  
        return {  
            "required": {  
                "Prefix_Quality": ("STRING", {"tooltip": "Quality prefix input (质量前缀)", "multiline": True}),  
                "Prefix_Art_style": ("STRING", {"tooltip": "Art style prefix input (艺术风格)", "multiline": True}),  
                "Prefix_Overall_effect": ("STRING", {"tooltip": "Overall effect prefix input (整体效果)", "multiline": True}),  
                "Subject": ("STRING", {"tooltip": "Subject input (主体：可以是人也可以是场景特效等)", "multiline": True}),  
                "Scene_Background": ("STRING", {"tooltip": "Scene Background input (背景)", "multiline": True}),  
                "Scene_Objects": ("STRING", {"tooltip": "Scene Objects (其他非主体物品)", "multiline": True}),  
                "Scene_Prospect": ("STRING", {"tooltip": "Scene prospect input (前景)", "multiline": True}),  
                "Scene_Special_effects": ("STRING", {"tooltip": "Scene special effects input (特效)", "multiline": True}),  
            },
        }  

    RETURN_TYPES = ("STRING",)  
    RETURN_NAMES = ("positive_promt",)  
    FUNCTION = "create_prompt"  
    CATEGORY = "NovelAI"  
    DESCRIPTION = "Create prompt strings for NovelAI"  

    def create_prompt(self, Prefix_Quality, Prefix_Art_style, Prefix_Overall_effect, Subject, Scene_Background, Scene_Objects, Scene_Prospect, Scene_Special_effects):
        
        # 否则拼接输入字符串  
        components = [Prefix_Quality, Prefix_Art_style, Prefix_Overall_effect, Subject, Scene_Background, Scene_Objects, Scene_Prospect, Scene_Special_effects]  
        concatenated_result = ", ".join(filter(None, components))  
        return (concatenated_result,)  

class NovelArtistTemplateSelectorNode:  
    @classmethod  
    def INPUT_TYPES(cls):  
        # 从已有提示词中生成下拉框选项  
        cls.prompt_manager = NovelPositivePromptManager(r"artist.json")  
        prompts = cls.load_prompts()
        print(prompts)
        prompt_options = [(key) for key, _ in prompts.items()]  
        print(f"Loading JSON :{prompt_options}")  

        return {  
            "required": {  
                "selected_prompt": (sorted(prompt_options), {"tooltip": "选择的提示词"}),  
            },  
            "optional": {  
                "new_prompt_title": ("STRING", {"tooltip": "新提示词的标题"}),  
                "new_prompt": ("STRING", {"tooltip": "添加的新提示词"}),  
            },  
        }  

    RETURN_TYPES = ("STRING",)  
    RETURN_NAMES = ("current_prompt",)  
    FUNCTION = "process_prompts"  
    CATEGORY = "NovelAI"  
    DESCRIPTION = "选择和添加提示词"  
        
    @classmethod  
    def load_prompts(cls):  
        return cls.prompt_manager.load_prompts()  


    @classmethod  
    def save_prompts(cls, prompts):  
        cls.prompt_manager.save_prompts(prompts)  

    def process_prompts(self, selected_prompt, new_prompt_title=None, new_prompt=None):  
        """处理输入并更新输出"""  
        prompts = self.load_prompts()  

        # 选择提示词  
        current_prompt = prompts.get(selected_prompt, "无效的提示词")  

        # 添加新提示词  
        if new_prompt and new_prompt_title:  
            # 生成新的键名  
            new_key = new_prompt_title  # 使用用户提供的标题作为键名  
            if new_key not in prompts:  
                prompts[new_key] = new_prompt  
                self.save_prompts(prompts)  
                print(f"已添加提示词: {new_prompt}，标题: {new_prompt_title}")  
                current_prompt = new_prompt
            else:  
                print(f"提示词标题 '{new_prompt_title}' 已存在。")  

        return (current_prompt,)  


class NovelPositiveQualityTemplateSelectorNode:  
    @classmethod  
    def INPUT_TYPES(cls):  
        # 从已有提示词中生成下拉框选项  
        cls.prompt_manager = NovelPositivePromptManager(r"quality.json")  
        prompts = cls.load_prompts()
        
        prompt_options = [(key) for key, _ in prompts.items()]  

        return {  
            "required": {  
                "selected_prompt": (sorted(prompt_options), {"tooltip": "选择的提示词"}),  
            },  
            "optional": {  
                "new_prompt_title": ("STRING", {"tooltip": "新提示词的标题"}),  
                "new_prompt": ("STRING", {"tooltip": "添加的新提示词"}),  
            },  
        }  

    RETURN_TYPES = ("STRING",)  
    RETURN_NAMES = ("current_prompt",)  
    FUNCTION = "process_prompts"  
    CATEGORY = "NovelAI"  
    DESCRIPTION = "选择和添加提示词"  

    @classmethod  
    def load_prompts(cls):  
        return cls.prompt_manager.load_prompts()  

    @classmethod  
    def save_prompts(cls, prompts):  
        cls.prompt_manager.save_prompts(prompts)  

    def process_prompts(self, selected_prompt, new_prompt_title=None, new_prompt=None):  
        """处理输入并更新输出"""  
        prompts = self.load_prompts()  

        # 选择提示词  
        current_prompt = prompts.get(selected_prompt, "无效的提示词")  

        # 添加新提示词  
        if new_prompt and new_prompt_title:  
            # 生成新的键名  
            new_key = new_prompt_title  # 使用用户提供的标题作为键名  
            if new_key not in prompts:  
                prompts[new_key] = new_prompt  
                self.save_prompts(prompts)  
                print(f"已添加提示词: {new_prompt}，标题: {new_prompt_title}")  
                current_prompt = new_prompt
            else:  
                print(f"提示词标题 '{new_prompt_title}' 已存在。")  

        return (current_prompt,)  

NODE_CLASS_MAPPINGS = {
    "NovelPositivePromptNode": NovelPositivePromptNode,
    "NovelArtistTemplateSelectorNode": NovelArtistTemplateSelectorNode,
    "NovelPositiveQualityTemplateSelectorNode": NovelPositiveQualityTemplateSelectorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NovelPositivePromptNode": "Novel Positive Prompt",
    "NovelArtistTemplateSelectorNode": "Novel Artist TemplateSelector Node",
    "NovelPositiveQualityTemplateSelectorNode": "Novel Positive Quality TemplateSelector Node",
}