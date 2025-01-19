from .common import NovelPositivePromptManager
from .common import NovelPositivePromptCommonNode
from .common import remove_trailing_comma_and_spaces

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
    CATEGORY = "NovelAI/Positive"  
    DESCRIPTION = "Create prompt strings for XL"  

    def create_prompt(self, Prefix_Quality, Prefix_Art_style, Prefix_Overall_effect, Subject, Scene_Background, Scene_Objects, Scene_Prospect, Scene_Special_effects):
        
        # 否则拼接输入字符串  
        components = [Prefix_Quality, Prefix_Overall_effect, Subject, Prefix_Art_style, Scene_Background, Scene_Objects, Scene_Prospect, Scene_Special_effects]  
        concatenated_result = ", ".join(filter(None, components))  
        return (concatenated_result,)  

class NovelT5xxlPositivePromptNode:  
    @classmethod  
    def INPUT_TYPES(cls):  
        return {  
            "required": {  
                "Parameters": ("STRING", {"tooltip": "Quality prefix input (质量前缀)", "multiline": True}),  
                "Subject": ("STRING", {"tooltip": "Subject input (主体：可以是人也可以是场景特效等)", "multiline": True}),  
                "Instructions": ("STRING", {"tooltip": "Overall effect prefix input (整体效果)", "multiline": True}),  
                "Other": ("STRING", {"tooltip": "Other", "multiline": True}),  
            },
        }  

    RETURN_TYPES = ("STRING",)  
    RETURN_NAMES = ("positive_promt",)  
    FUNCTION = "create_prompt"  
    CATEGORY = "NovelAI/Positive"  
    DESCRIPTION = "Create prompt strings for Flux/SD3.5"  

    def create_prompt(self, Parameters, Subject, Instructions, Other):
        
        # 否则拼接输入字符串  
        concatenated_result = ""
        if Parameters and len(Parameters) != 0:  
            if not Parameters.endswith('.'):  
                concatenated_result += ("Parameters: " + Parameters + ".")  
            else:  
                concatenated_result += ("Parameters: " + Parameters)  

        if Subject and len(Subject) != 0:  
            if not Subject.endswith('.'):  
                concatenated_result += ("Subject: " + Subject + ".")  
            else:  
                concatenated_result += ("Subject: " + Subject)  

        if Instructions and len(Instructions) != 0:  
            if not Instructions.endswith('.'):  
                concatenated_result += ("Instructions: " + Instructions + ".")  
            else:  
                concatenated_result += ("Instructions: " + Instructions)  

        if Other and len(Other) != 0:  
            if not Other.endswith('.'):  
                concatenated_result += (Other + ".")  
            else:  
                concatenated_result += Other  
        return (concatenated_result,)  

class NovelRolePromptNode:  
    @classmethod  
    def INPUT_TYPES(cls):  
        return {  
            "required": {  
                "Character_Appearance": ("STRING", {"tooltip": "(人物外貌)", "multiline": True}),  
            },
            "optional": {  
                "Character_Clothing": ("STRING", {"tooltip": "(人物衣服)", "multiline": True}),  
                "Character_Actions": ("STRING", {"tooltip": "(人物动作)", "multiline": True}),  
                "Other": ("STRING", {"tooltip": "Other", "multiline": True}),  
            },  
        }  

    RETURN_TYPES = ("STRING",)  
    RETURN_NAMES = ("promt",)  
    FUNCTION = "create_prompt"  
    CATEGORY = "NovelAI/Positive"  
    DESCRIPTION = "Create prompt strings for Flux/SD3.5"  

    def create_prompt(self, Character_Appearance, Character_Clothing, Character_Actions, Other):
        # 去除每个字符串末尾的逗号  
        Character_Appearance = remove_trailing_comma_and_spaces(Character_Appearance)
        Character_Clothing = remove_trailing_comma_and_spaces(Character_Clothing)
        Character_Actions = remove_trailing_comma_and_spaces(Character_Actions)
        Other = remove_trailing_comma_and_spaces(Other)
    
        # 将非空字符串用逗号拼接  
        prompt_parts = [part for part in [Character_Appearance, Character_Clothing, Character_Actions, Other] if part]  
        print(prompt_parts)
        prompt = ', '.join(prompt_parts)  
        
        return (prompt,)   

class NovelHuyuanPromptNode:
    @classmethod  
    def INPUT_TYPES(cls):  
        return {  
            "required": {  
                "Subject": ("STRING", {"tooltip": "Subject input (主体：可以是人也可以是场景特效等)", "multiline": True}),  
                "Instructions": ("STRING", {"tooltip": "Overall effect prefix input (整体效果)", "multiline": True}),  
            },
            "optional": {  
                "LoraTriggerWords": ("STRING", {"tooltip": "Lora Trigger Words", "multiline": True}),
                "Other": ("STRING", {"tooltip": "Other", "multiline": True}),
            },  
        }  

    RETURN_TYPES = ("STRING",)  
    RETURN_NAMES = ("promt",)  
    FUNCTION = "create_prompt"  
    CATEGORY = "SMELL_NOVELAI_POSITIVE"  
    DESCRIPTION = "Create prompt strings for Hunyuan"  

    def create_prompt(self, Subject, Instructions, LoraTriggerWords, Other):
        
        # 否则拼接输入字符串  
        concatenated_result = ""
        if LoraTriggerWords and len(LoraTriggerWords) != 0:  
            if not LoraTriggerWords.endswith('.'):  
                concatenated_result += ("Parameters: " + LoraTriggerWords + ".")  
            else:  
                concatenated_result += ("Parameters: " + LoraTriggerWords)  

        if Subject and len(Subject) != 0:  
            if not Subject.endswith('.'):  
                concatenated_result += ("Subject: " + Subject + ".")  
            else:  
                concatenated_result += ("Subject: " + Subject)  

        if Instructions and len(Instructions) != 0:  
            if not Instructions.endswith('.'):  
                concatenated_result += ("Instructions: " + Instructions + ".")  
            else:  
                concatenated_result += ("Instructions: " + Instructions)  

        if Other and len(Other) != 0:  
            if not Other.endswith('.'):  
                concatenated_result += (Other + ".")  
            else:  
                concatenated_result += Other  
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

class NovelPositiveQualityTemplateSelectorNode(NovelPositivePromptCommonNode):  
    @classmethod  
    def INPUT_TYPES(cls):  
        # 从已有提示词中生成下拉框选项  
        cls.prompt_manager = NovelPositivePromptManager(r"quality.json")  
        prompts = cls.load_prompts()
        
        prompt_options = [(key) for key, _ in prompts.items()]  
        prompt_options.append("None")

        return {  
            "required": {  
                "user_prompt": ("STRING", {"tooltip": "添加的新提示词", "multiline": True}),
                "use_template": ("BOOLEAN", {"default": True}),    
            },  
            "optional": {  
                "selected_prompt1": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
                "selected_prompt2": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
                "selected_prompt3": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
                "selected_prompt4": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
                "selected_prompt5": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}), 
                "new_prompt_title": ("STRING", {"tooltip": "新提示词的标题"}),  
                "new_prompt": ("STRING", {"tooltip": "添加的新提示词", "multiline": True}),  
            },   
        }  

    RETURN_TYPES = ("STRING","STRING")  
    RETURN_NAMES = ("current_prompt","current_prompts_translation")  
    FUNCTION = "process_prompts"  
    CATEGORY = "NovelAI_Positive_Quality" 
    OUTPUT_NODE = True 
    DESCRIPTION = "选择和添加质量提示词"  

class NovelSubjectTemplateSelectorNode(NovelPositivePromptCommonNode):  
    @classmethod  
    def INPUT_TYPES(cls):  
        # 从已有提示词中生成下拉框选项  
        cls.prompt_manager = NovelPositivePromptManager(r"subject.json")  
        prompts = cls.load_prompts()
        
        prompt_options = [(key) for key, _ in prompts.items()]  
        prompt_options.append("None")

        return {  
            "required": {  
                "user_prompt": ("STRING", {"tooltip": "添加的新提示词", "multiline": True}),
                "use_template": ("BOOLEAN", {"default": False}),    
            },  
            "optional": {  
                "selected_prompt1": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
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
    CATEGORY = "NovelAI_Positive_Subject"  
    OUTPUT_NODE = True
    DESCRIPTION = "选择和添加主体提示词"  

class NovelJoyCaptionTwoExtraOptionsNode(NovelPositivePromptCommonNode):  
    @classmethod  
    def INPUT_TYPES(cls):  
        # 从已有提示词中生成下拉框选项  
        cls.prompt_manager = NovelPositivePromptManager(r"joycaptiontwo.json")  
        prompts = cls.load_prompts()
        
        prompt_options = [(key) for key, _ in prompts.items()]  
        prompt_options.append("None")

        return {  
            "required": {  
                "user_prompt": ("STRING", {"tooltip": "添加的新提示词", "multiline": True}),
                "use_template": ("BOOLEAN", {"default": False}),    
            },  
            "optional": {  
                "selected_prompt1": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
                "selected_prompt2": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
                "selected_prompt3": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
                "selected_prompt4": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}),  
                "selected_prompt5": (sorted(prompt_options), {"tooltip": "选择的提示词", "default": "None"}), 
                "new_prompt_title": ("STRING", {"tooltip": "新提示词的标题"}),  
                "new_prompt": ("STRING", {"tooltip": "添加的新提示词", "multiline": True}),  
            },  
        }  
    
    RETURN_TYPES = ("Extra_Options","Extra_Options")  
    RETURN_NAMES = ("current_options","current_options_translation")  
    FUNCTION = "process_prompts_with_list"  
    CATEGORY = "NovelAI_JoyCaptionTwo"  
    OUTPUT_NODE = True
    DESCRIPTION = "JoyCaptionTwo Additional parameters for reverse inference"  

NODE_CLASS_MAPPINGS = {
    "NovelPositivePromptNode": NovelPositivePromptNode,
    "NovelT5xxlPositivePromptNode": NovelT5xxlPositivePromptNode,
    "NovelHuyuanPromptNode": NovelHuyuanPromptNode,
    "NovelArtistTemplateSelectorNode": NovelArtistTemplateSelectorNode,
    "NovelPositiveQualityTemplateSelectorNode": NovelPositiveQualityTemplateSelectorNode,
    "NovelOverallEffectTemplateSelectorNode": NovelOverallEffectTemplateSelectorNode,
    "NovelSubjectTemplateSelectorNode": NovelSubjectTemplateSelectorNode,
    "NovelRolePromptNode": NovelRolePromptNode, 
    "NovelJoyCaptionTwoExtraOptionsNode": NovelJoyCaptionTwoExtraOptionsNode,
}



NODE_DISPLAY_NAME_MAPPINGS = {
    "NovelPositivePromptNode": "Smell Novel Positive Prompt",
    "NovelT5xxlPositivePromptNode": "Smell Novel T5xxl Positive Prompt",
    "NovelHuyuanPromptNode": "Smell Novel Hunyuan Prompt",
    "NovelArtistTemplateSelectorNode": "Smell Novel Artist TemplateSelector Node",
    "NovelPositiveQualityTemplateSelectorNode": "Smell Novel Positive Quality TemplateSelector Node",
    "NovelOverallEffectTemplateSelectorNode": "Smell Novel OverallEffect TemplateSelector Node",
    "NovelSubjectTemplateSelectorNode": "Smell Novel Subject TemplateSelector Node",
    "NovelRolePromptNode": "Smell Novel Role Prompt", 
    "NovelJoyCaptionTwoExtraOptionsNode": "Smell Novel JoyCaptionTwo ExtraOptions Node",
}