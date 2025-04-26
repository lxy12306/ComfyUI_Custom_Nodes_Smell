import json
import os

class NovelNagativePromptManager:
    def __init__(self, json_name):
        self.current_file_dir = os.path.dirname(__file__)
        self.json_name = json_name
        self.json_dir = os.path.join(self.current_file_dir, "json")
        print(f"json_name: {self.json_dir}")

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

class NovelPositivePromptManager:

    def __init__(self, json_name):
        self.current_file_dir = os.path.dirname(__file__)
        self.json_name = json_name
        self.json_dir = os.path.join(self.current_file_dir, "json")
        print(f"json_name: {self.json_dir}")

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

    def load_prompts(self):
        """公开方法，加载提示词"""
        return self.__load_prompts("prompts")

    def load_prompts_translation(self):
        """公开方法，加载提示词"""
        return self.__load_prompts("prompts_translation")
    def save_prompts(self, prompts):
        """公开方法，保存提示词"""
        self.__save_prompts(prompts)

class NovelPositivePromptCommonNode:

    @classmethod
    def load_prompts(cls):
        return cls.prompt_manager.load_prompts()
    @classmethod
    def load_prompts_translation(cls):
        return cls.prompt_manager.load_prompts_translation()

    @classmethod
    def save_prompts(cls, prompts):
        cls.prompt_manager.save_prompts(prompts)
    @classmethod
    def process_prompts(self, user_prompt, use_template ,selected_prompt1=None, selected_prompt2=None, selected_prompt3=None, selected_prompt4=None, selected_prompt5=None, new_prompt_title=None, new_prompt=None):
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
            else:
                print(f"提示词标题 '{new_prompt_title}' 已存在。")

        if use_template :
            current_prompts.insert(0, user_prompt)
            current_prompts_translation.insert(0, user_prompt)
        else :
            current_prompts = [user_prompt]
            current_prompts_translation = [user_prompt]

        cleaned_prompts = [prompt.strip()[:-1] if prompt.strip().endswith(',') else prompt.strip() for prompt in current_prompts]
        concatenated_result = ",".join(filter(None, cleaned_prompts))
        concatenated_result_translation = ",".join(filter(None, current_prompts_translation))
        print(concatenated_result)
                # Send update event
        return (concatenated_result, concatenated_result_translation)

    def process_prompts_with_list(self, user_prompt, use_template ,selected_prompt1=None, selected_prompt2=None, selected_prompt3=None, selected_prompt4=None, selected_prompt5=None, new_prompt_title=None, new_prompt=None):
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
            else:
                print(f"提示词标题 '{new_prompt_title}' 已存在。")

        if use_template :
            current_prompts.insert(0, user_prompt)
            current_prompts_translation.insert(0, user_prompt)
        else :
            current_prompts = [user_prompt]
            current_prompts_translation = [user_prompt]

        cleaned_prompts = [prompt.strip()[:-1] if prompt.strip().endswith(',') else prompt.strip() for prompt in current_prompts]
        cleaned_prompts_translation = [prompt.strip()[:-1] if prompt.strip().endswith(',') else prompt.strip() for prompt in current_prompts_translation]
        return (cleaned_prompts, cleaned_prompts_translation)

def remove_trailing_comma_and_spaces(input_string):
    if input_string == None:
        return None
    ret = input_string.rstrip(', ').rstrip()
    print(ret)
    return ret
