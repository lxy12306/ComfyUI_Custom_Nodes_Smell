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


class NovelPositivePromptManager:  
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
            json.dump({"prompts": prompts}, file, ensure_ascii=False, indent=2)  

    def load_prompts(self):  
        """公开方法，加载提示词"""  
        return self.__load_prompts("prompts")  

    def load_prompts_translation(self):  
        """公开方法，加载提示词"""  
        return self.__load_prompts("prompts_translation")  
    def save_prompts(self, prompts):  
        """公开方法，保存提示词"""  
        self.__save_prompts(prompts)