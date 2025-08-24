import os
from pickle import LIST
from pyexpat import model
import time
import weakref
from typing import Dict, List, Tuple, Any, Optional, Set

from numpy import delete
from sympy import sequence
from torch import mode
from nodes import LoraLoader

from .libs.Efficiency import SequenceManager
from .libs.DoublyLinkedList import DoublyLinkedList, DoublyLinkedListNode
import threading
# 兼容 ComfyUI folder_paths
try:
    import folder_paths
except ImportError:
    class MockFolderPaths:
        @staticmethod
        def get_filename_list(folder_name):
            return []
    folder_paths = MockFolderPaths()

_MANAGER_INDEX_REGISTRY = {}
_MANAGER_INDEX_LOCK = threading.Lock()

class SmellLora:
    def __init__(self, name: str, weight_range: str, sequence_length: int, node_ref: Optional[weakref.ref] = None):
        self.name = name
        self.weight_range = weight_range
        self.sequence_length = sequence_length
        self.min_weight, self.max_weight = self._parse_weight_range(weight_range)
        self.lora_info = (self.min_weight, self.max_weight, self.sequence_length)
        self.node_ref = node_ref

    def _parse_weight_range(self, weight_range: str) -> Tuple[float, float]:
        """
        解析权重范围字符串，支持单一值或范围格式
        """
        try:
            if '-' in weight_range:
                parts = weight_range.split('-')
                if len(parts) != 2:
                    raise ValueError("Invalid weight range format")
                min_weight = float(parts[0])
                max_weight = float(parts[1])
            else:
                min_weight = max_weight = float(weight_range)
            if min_weight > max_weight:
                raise ValueError("Invalid weight range: min_weight > max_weight")
            return min_weight, max_weight
        except ValueError as e:
            raise ValueError(f"Failed to parse weight range '{weight_range}': {e}")

class SmellLoraLoad:
    """
    Smell Lora 加载节点
    用于配置和加载 Lora 模型
    """

    @classmethod
    def INPUT_TYPES(cls):
        # 获取可用的 Lora 文件列表
        lora_list = folder_paths.get_filename_list("loras")

        return {
            "required": {
                "lora_name": (lora_list, {"default": lora_list[0] if lora_list else ""}),
                "weight_range": ("STRING", {
                    "default": "0.0-1.0",
                    "multiline": False,
                    "tooltip": "权重范围，支持单一值(如 0.5)或范围(如 0.0-1.0)"
                }),
                "sequence_length": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "序列长度，即要生成多少个不同的权重值"
                }),
            },
            "optional": {
                "smell_lora_list": ("SMELL_LORA_LINK_LIST",),
            },
        }

    RETURN_TYPES = ("SMELL_LORA_LINK_LIST",)
    RETURN_NAMES = ("smell_lora_list",)
    FUNCTION = "load_lora"
    CATEGORY = "Smell/Lora"

    def load_lora(self, lora_name, weight_range, sequence_length, smell_lora_list=None):
        """
        加载和配置 Lora

        Args:
            lora_name: Lora 文件名
            weight_range: 权重范围字符串
            sequence_length: 序列长度
            smell_lora_list: Smell Lora 列表（可选）

        Returns:
            smell_lora_list: 更新后的 Smell Lora 列表
        """
        if smell_lora_list is None:
            smell_lora_list = DoublyLinkedList[SmellLora]()

        try:
            smell_lora = SmellLora(name=lora_name, weight_range=weight_range, sequence_length=sequence_length, node_ref=weakref.ref(self))
            smell_lora_list.append(smell_lora)
            print(smell_lora_list)
            return (smell_lora_list,)

        except Exception as e:
            error_info = f"错误: {str(e)}"
            return (smell_lora_list,)


class SmellLoraManager(SequenceManager):
    """
    按 index 共享 Lora 配置。
    同一 index 的所有此节点实例共享同一份状态；任意一个传入新列表都会刷新该 index 的共享内容。
    不再区分主/次。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "index": ("INT", {
                    "default": 0, "min": 0, "max": 9999, "step": 1,
                    "tooltip": "同 index 节点共享一份状态"
                }),
                "smell_lora_list": ("SMELL_LORA_LINK_LIST",),
            },
            "optional": {
                "model": ("MODEL", {"default": None}),
                "clip": ("CLIP", {"default": None})
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("model", "clip", "smell_lora_info")
    FUNCTION = "manage_loras"
    CATEGORY = "Smell/Lora"

    @classmethod
    def IS_CHANGED(cls, index, smell_lora_list, mode=None, clip=None):
        """
        确定节点是否需要重新执行
        返回值变化时，节点会被重新执行
        """

        # 组合多个因素来确保节点在需要时重新执行
        change_hash = f"{index}_{smell_lora_list}_{model}_{clip}_{time.time()}"

        return change_hash

    def __init__(self):
        super().__init__()
        self.lora_list: Optional[DoublyLinkedList[SmellLora]] = None
        self.global_index = 0
        self.lora_info = "未注册 Lora"
        self.index: Optional[int] = None   # 当前节点绑定 index
        self.sequences: List[Tuple[List[str], List[float]]] = []  # 初始化 sequences 属性
        # 不再使用 _is_primary 区分主次，所有同 index 节点等同操作共享实例

    def _preview_sequences(self, max_count: int = 3) -> str:
        """
        返回当前 global_index 起的最多 max_count 个序列的简洁 JSON 字符串:
        [
          {"idx": 实际索引, "cur": 是否当前, "pairs": [["loraA", 0.5], ...]},
          ...
        ]
        """
        if not self.sequences:
            return "[]"
        total = len(self.sequences)
        span = min(max_count, total)
        preview = []
        for offset in range(span):
            idx = (self.global_index + offset) % total
            names, weights = self.sequences[idx]
            preview.append({
                "idx": idx,
                "cur": offset == 0,
                "pairs": list(zip(names, weights))
            })
        try:
            import json
            # 使用缩进便于阅读，并在末尾补换行
            return json.dumps(preview, ensure_ascii=False, indent=2) + "\n"
        except Exception:
            return str(preview)

    def manage_loras(self, index, smell_lora_list, model=None, clip=None):
        """
        按 index 共享状态：
        - 每个 index 对应 _MANAGER_INDEX_REGISTRY 中的一个管理实例(第一次出现的节点)
        - 同 index 的其它节点调用时若提供新的列表也会更新该共享实例
        """
        # 绑定 index
        if self.index != index:
            self = SmellLoraManager()  # 重置当前实例
            self.index = index

        # 获取或注册共享实例
        with _MANAGER_INDEX_LOCK:
            shared = _MANAGER_INDEX_REGISTRY.get(index)
            if shared is None:
                _MANAGER_INDEX_REGISTRY[index] = self
                shared = self
        # 若调用节点不是共享实例，后续操作仍作用在共享实例
        target = shared
        # 若 SequenceManager 里尚未有 param_map（极端情况），初始化防御
        if not hasattr(target, "param_map"):
            target.param_map = {}
        # 列表引用变化则重建
        if target.lora_list is not smell_lora_list:
            target.lora_list = smell_lora_list
            target.global_index = 0
            target.param_map.clear()
            for lora in smell_lora_list:
                target.update(lora.name, lora.lora_info)
            target.sequences = target.get_sequences()
            target.lora_info = f"[index={index}] 注册 {len(target.param_map.keys())} 个 Lora, total_sequences: {len(target.sequences)}, step: {target.global_index}\n preview: {target._preview_sequences()}"
        else:
            target.global_index = (target.global_index + 1) % (len(target.sequences) if target.sequences else 1)
            target.lora_info = f"[index={index}] 注册 {len(target.param_map.keys())} 个 Lora, total_sequences: {len(target.sequences)}, step: {target.global_index}\n preview: {target._preview_sequences()}"

        if model is not None:
            for lora, seq in zip(target.sequences[target.global_index][0], target.sequences[target.global_index][1]):
                seq_model = seq
                seq_clip = seq if clip is None else 0
                model, clip = LoraLoader().load_lora(model, clip, lora, seq_model, seq_clip)

        return (model, clip, target.lora_info,)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "SmellLoraLoad": SmellLoraLoad,
    "SmellLoraManager": SmellLoraManager
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SmellLoraLoad": "Smell Lora Load",
    "SmellLoraManager": "Smell Lora Manager",
}
