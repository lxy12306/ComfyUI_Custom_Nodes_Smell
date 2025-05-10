import os
import io
import json
import torch
import torchaudio
import struct
import platform

from .libs.function import get_next_file_path

def create_vorbis_comment_block(comment_dict, last_block):
    vendor_string = b'SmellCommon'
    vendor_length = len(vendor_string)

    comments = []
    for key, value in comment_dict.items():
        comment = f"{key}={value}".encode('utf-8')
        comments.append(struct.pack('<I', len(comment)) + comment)

    user_comment_list_length = len(comments)
    user_comments = b''.join(comments)

    comment_data = struct.pack('<I', vendor_length) + vendor_string + struct.pack('<I', user_comment_list_length) + user_comments
    if last_block:
        id = b'\x84'
    else:
        id = b'\x04'
    comment_block = id + struct.pack('>I', len(comment_data))[1:] + comment_data

    return comment_block

def insert_or_replace_vorbis_comment(flac_io, comment_dict):
    if len(comment_dict) == 0:
        return flac_io

    flac_io.seek(4)

    blocks = []
    last_block = False

    while not last_block:
        header = flac_io.read(4)
        last_block = (header[0] & 0x80) != 0
        block_type = header[0] & 0x7F
        block_length = struct.unpack('>I', b'\x00' + header[1:])[0]
        block_data = flac_io.read(block_length)

        if block_type == 4 or block_type == 1:
            pass
        else:
            header = bytes([(header[0] & (~0x80))]) + header[1:]
            blocks.append(header + block_data)

    blocks.append(create_vorbis_comment_block(comment_dict, last_block=True))

    new_flac_io = io.BytesIO()
    new_flac_io.write(b'fLaC')
    for block in blocks:
        new_flac_io.write(block)

    new_flac_io.write(flac_io.read())
    return new_flac_io


class AudioSaver:

    def __init__(self):
        self.compression = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "BaseDirectory": ("STRING", {}),
                "FilenamePrefix1": ("STRING", {"default": "Audio"}),
                "FileMax": ("INT", {"default": 64}),
                "OpenOutputDirectory": ("BOOLEAN", {"default": False}),
                "save_meta": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "FilenamePrefix2": ("STRING", {"default": None}),
                "tags": ("STRING", {"default": None}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "BatchSave"
    OUTPUT_NODE = True
    CATEGORY = "🌱SmellCommon/AudioFunc"
    DESCRIPTION = "Batch save files to a folder"

    def write_text_file(self, file, content, encoding="utf-8"):
        try:
            with open(file, 'w', encoding=encoding, newline='\n') as f:
                f.write(content)
        except OSError:
            print(f"{file} save failed")

    def BatchSave(self, audio, BaseDirectory, FilenamePrefix1, FileMax, OpenOutputDirectory, save_meta, FilenamePrefix2=None, tags=None, prompt=None, extra_pnginfo=None):
        try:
            Directory1 = BaseDirectory
            Directory2 = os.path.join(Directory1, FilenamePrefix1)
            Directory = Directory2

            if not os.path.exists(Directory1):
                os.makedirs(Directory1)
            if not os.path.exists(Directory2):
                os.makedirs(Directory2)

            _FilenamePrefix1 = FilenamePrefix1
            FilenamePrefix = _FilenamePrefix1

            if not FilenamePrefix2 == None:
                Directory3 = os.path.join(Directory2, FilenamePrefix2)
                Directory = Directory3
                if not os.path.exists(Directory3):
                    os.makedirs(Directory3)
                _FilenamePrefix2 = FilenamePrefix2
                FilenamePrefix = f"{_FilenamePrefix1}_{_FilenamePrefix2}"

            # 处理音频文件保存逻辑
            metadata = {}
            if save_meta:  # 逻辑与原始代码中的 save_meta 相反，因为音频元数据处理方式不同
                if prompt is not None:
                    metadata["prompt"] = json.dumps(prompt)
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata[x] = json.dumps(extra_pnginfo[x])

            # 遍历音频批次
            for (batch_number, waveform) in enumerate(audio["waveform"].cpu()):
                try:
                    # 获取文件路径
                    audio_path, txt_path = get_next_file_path(Directory, FilenamePrefix, "flac", FileMax)

                    # 保存音频
                    buff = io.BytesIO()
                    torchaudio.save(buff, waveform, audio["sample_rate"], format="FLAC")

                    # 添加元数据
                    buff = insert_or_replace_vorbis_comment(buff, metadata)

                    # 写入文件
                    with open(audio_path, 'wb') as f:
                        f.write(buff.getbuffer())

                    print(f"已保存音频: {audio_path}")

                    # 保存标签文件
                    if tags is not None and tags != "":
                        self.write_text_file(txt_path, tags)

                except Exception as e:
                    print(f"保存音频批次 {batch_number} 时出错: {e}")

            if (OpenOutputDirectory):
                try:
                    system = platform.system()
                    if system == "Windows":
                        os.system(f'explorer "{Directory}"')
                    elif system == "Darwin":  # macOS
                        os.system(f'open "{Directory}"')
                    else:  # Linux
                        os.system(f'xdg-open "{Directory}"')
                except Exception as e:
                    print(f"Error opening directory: {e}")

        except Exception as e:
            print(f"Error saving audio: {e}")

        return ()


class AudioTrimmer:
    """音频裁剪节点：根据时间范围裁剪音频"""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "start_time": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 600.0, "step": 0.1, "display": "slider"}),
                "end_time": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 600.0, "step": 0.1, "display": "slider"}),
            },
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "trim_audio"
    OUTPUT_NODE = False
    CATEGORY = "🌱SmellCommon/AudioFunc"
    DESCRIPTION = "根据指定的开始和结束时间裁剪音频"

    def trim_audio(self, audio, start_time, end_time):
        """裁剪音频"""
        if end_time <= start_time:
            print(f"裁剪错误: 结束时间 ({end_time}) 必须大于开始时间 ({start_time})")
            return (audio,)

        sample_rate = audio["sample_rate"]
        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)

        result_waveforms = []

        for waveform in audio["waveform"]:
            max_samples = waveform.shape[1]
            actual_end_sample = min(end_sample, max_samples)

            if start_sample >= max_samples:
                print(f"裁剪错误: 开始时间 ({start_time}秒) 超出音频长度 ({max_samples/sample_rate}秒)")
                trimmed = torch.zeros((waveform.shape[0], 1), device=waveform.device)
            else:
                trimmed = waveform[:, start_sample:actual_end_sample]

            result_waveforms.append(trimmed)

        trimmed_waveform = torch.stack(result_waveforms) if len(result_waveforms) > 1 else result_waveforms[0].unsqueeze(0)

        return ({"waveform": trimmed_waveform, "sample_rate": sample_rate},)

NODE_CLASS_MAPPINGS = {
    "AudioSaver": AudioSaver,
    "AudioTrimmer": AudioTrimmer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AudioSaver" : "Smell Audio Saver",
    "AudioTrimmer" : "Smell Audio Trimmer",
}