import os
import folder_paths
import json
from nodes import CheckpointLoaderSimple

'''

def populate_items(names, type):
    for idx, item_name in enumerate(names):

        file_path = folder_paths.get_full_path(type, item_name)

        if file_path is None:
            print(f"Unable to get path for {type} {item_name}")
            continue

        file_path_no_ext = os.path.splitext(file_path)[0]
        json_path = file_path_no_ext + ".json"  
        has_json = os.path.isfile(json_path)
        default_json_content = {  
            "From": "None",  
            "Description": "None",  
            "Other": "None"  
        }  
        if has_json:
            try:  
                with open(json_path, 'r', encoding='utf-8') as json_file:  
                    existing_data = json.load(json_file)  
            
                for key in default_json_content:  
                    if key not in existing_data or existing_data[key] is None:  
                        existing_data[key] = "None"  
                
                with open(json_path, 'w', encoding='utf-8') as json_file:  
                    json.dump(existing_data, json_file, indent=2, ensure_ascii=False)  
            
            except (json.JSONDecodeError, IOError):  
                # 如果JSON文件损坏或无法读取，使用默认内容  
                with open(json_path, 'w', encoding='utf-8') as json_file:  
                    json.dump(default_json_content, json_file, indent=2, ensure_ascii=False)  
                existing_data = default_json_content
        else :
            # 写入JSON文件  
            with open(json_path, 'w', encoding='utf-8') as json_file:  
                json.dump(default_json_content, json_file, indent=2, ensure_ascii=False)  
            print(f"创建默认JSON文件: {json_path}") 
            existing_data = default_json_content  
        

        names[idx] = {
            "content": item_name,
            "meta": existing_data,
        }
    names.sort(key=lambda i: i["content"].lower())
'''


def populate_items(names, type):
    metas = {}
    for idx, item_name in enumerate(names):

        file_path = folder_paths.get_full_path(type, item_name)

        if file_path is None:
            print(f"Unable to get path for {type} {item_name}")
            continue

        file_path_no_ext = os.path.splitext(file_path)[0]
        json_path = file_path_no_ext + ".json"  
        has_json = os.path.isfile(json_path)
        default_json_content = {  
            "From": "None",  
            "Description": "None",  
            "Other": "None"  
        }  
        existing_data = None
        if has_json:
            try:  
                with open(json_path, 'r', encoding='utf-8') as json_file:  
                    existing_data = json.load(json_file)  
            
                for key in default_json_content:  
                    if key not in existing_data or existing_data[key] is None:  
                        existing_data[key] = "None"  
            
            except (json.JSONDecodeError, IOError):  
                existing_data = default_json_content
        else :
            existing_data = default_json_content  

        existing_data["JsonFile"] = json_path
        with open(json_path, 'w', encoding='utf-8') as json_file:  
            json.dump(existing_data, json_file, indent=2, ensure_ascii=False)  
        
        names[idx] = {
            "content": item_name,
            "image": None,
        }
        metas[item_name] = existing_data
    names.sort(key=lambda i: i["content"].lower())
    return metas

class CheckpointLoaderWithMeta(CheckpointLoaderSimple):
    
    @classmethod
    def INPUT_TYPES(s):
        types = super().INPUT_TYPES()
        names = types["required"]["ckpt_name"][0]
        s.metas = populate_items(names, "checkpoints")
        types["optional"] = { "From": ("HIDDEN",),
                              "Description": ("HIDDEN"),}
        return types

    RETURN_TYPES = (*CheckpointLoaderSimple.RETURN_TYPES, "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "From", "Description")
    FUNCTION = "load_checkpoint"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/CheckPoint"
    DESCRIPTION = "Load checkpoint model"  


    @classmethod
    def VALIDATE_INPUTS(s, ckpt_name):
        types = super().INPUT_TYPES()
        names = types["required"]["ckpt_name"][0]

        name = ckpt_name["content"]
        if name in names:
            return True
        else:
            return f"Checkpoint not found: {name}"

    def load_checkpoint(self, **kwargs):
        content = kwargs["ckpt_name"]["content"]
        meta = self.metas[content]
        kwargs["ckpt_name"] = content
        From = kwargs.pop("From", "")
        Description = kwargs.pop("Description", "")

        return (*super().load_checkpoint(**kwargs), meta["From"], meta["JsonFile"])
    
NODE_CLASS_MAPPINGS = {
    "CheckpointLoaderWithMeta": CheckpointLoaderWithMeta,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CheckpointLoaderWithMeta": "Smell Checkpoint Loader Simple With Meta",
}