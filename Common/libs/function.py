import torch
import sys
import os
import shutil

def clear_memory():
    import gc
    # Cleanup
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

class AnyType(str):
  """A special class that is always equal in not equal comparisons. Credit to pythongosssss"""
  def __eq__(self, __value: object) -> bool:
    return True
  def __ne__(self, __value: object) -> bool:
    return False

# 向上取整数倍
def num_round_up_to_multiple(number: int, multiple: int) -> int:
    remainder = number % multiple
    if remainder == 0:
        return number
    else:
        factor = (number + multiple - 1) // multiple  # 向上取整的计算方式
        return factor * multiple

def log(message:str, message_type:str='info'):
    name = 'LayerStyle'

    if message_type == 'error':
        message = '\033[1;41m' + message + '\033[m'
    elif message_type == 'warning':
        message = '\033[1;31m' + message + '\033[m'
    elif message_type == 'finish':
        message = '\033[1;32m' + message + '\033[m'
    else:
        message = '\033[1;33m' + message + '\033[m'
    print(f"🌱SmellCommon: {name} -> {message}")

def smell_debug(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

def bakup_excessive_file(directory, filename_prefix, file_extension):
    bak_index = 0
    while True:
        padding = str(bak_index).zfill(4)
        dir_name = f"bak_{padding}"
        dir_path = os.path.join(directory, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            moved_files = 0
            for existing_file in os.listdir(directory):
                if (existing_file.startswith(filename_prefix) and
                    existing_file.endswith(file_extension)):
                    src_path = os.path.join(directory, existing_file)
                    dst_path = os.path.join(dir_path, existing_file)
                    shutil.move(src_path, dst_path)
                    moved_files += 1

                    txt_filename = existing_file[:-5] + ".txt"
                    txt_src_path = os.path.join(directory, txt_filename)
                    if os.path.exists(txt_src_path):
                        txt_dst_path = os.path.join(dir_path, txt_filename)
                        shutil.move(txt_src_path, txt_dst_path)
                        print(f"同时移动文本文件: {txt_filename}")
            return moved_files
        bak_index += 1

def get_next_file_path(directory, filename_prefix, file_extension, file_max=64):
    index = 1
    while True:
        padding = str(index).zfill(4)
        image_name = f"{filename_prefix}_{padding}.{file_extension}"
        image_path = os.path.join(directory, image_name)
        txt_name = f"{filename_prefix}_{padding}.txt"
        txt_path = os.path.join(directory, txt_name)
        if not os.path.exists(image_path):
            return image_path, txt_path
        index += 1
        if index > file_max:
            bakup_excessive_file(directory, filename_prefix, file_extension)
            index = 1