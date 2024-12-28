from .common import NovelPositivePromptManager

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

class NovelOverallEffectTemplateSelectorNode:  
    @classmethod  
    def INPUT_TYPES(cls):  
        # 从已有提示词中生成下拉框选项  
        cls.prompt_manager = NovelPositivePromptManager(r"overall_effect.json")  
        prompts = cls.load_prompts()
        
        prompt_options = [(key) for key, _ in prompts.items()]  
        prompt_options.append("None")

        return {  
            "required": {  
                "selected_prompt1": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
            },  
            "optional": {  
                "selected_prompt2": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
                "selected_prompt3": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
                "selected_prompt4": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
                "selected_prompt5": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}), 
                "new_prompt_title": ("STRING", {"tooltip": "新提示词的标题"}),  
                "new_prompt": ("STRING", {"tooltip": "添加的新提示词", "multiline": True}),  
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
                "new_prompt": ("STRING", {"tooltip": "添加的新提示词", "multiline": True}),  
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
    "NovelOverallEffectTemplateSelectorNode": NovelOverallEffectTemplateSelectorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NovelPositivePromptNode": "Smell Novel Positive Prompt",
    "NovelArtistTemplateSelectorNode": "Smell Novel Artist TemplateSelector Node",
    "NovelPositiveQualityTemplateSelectorNode": "Smell Novel Positive Quality TemplateSelector Node",
    "NovelOverallEffectTemplateSelectorNode": "Smell Novel OverallEffect TemplateSelector Node",
}