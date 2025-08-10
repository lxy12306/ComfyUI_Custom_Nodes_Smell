import random
import numpy as np
from typing import List, Tuple, Union, Optional


class SequenceGenerator:
    """
    序列生成器类
    用于根据输入的浮点数取值范围数组生成指定重复次数的有序序列组合
    每个维度可以指定不同的分割数量，生成所有可能的组合序列
    """

    def __init__(self):
        """初始化序列生成器"""
        pass

    def generate_sequences(self,
                          value_ranges: List[Tuple[float, float]],
                          repeat_count: List[int]) -> List[List[float]]:
        """
        生成有序序列组合

        Args:
            value_ranges: 包含每个维度取值范围的数组，每个元素是(min_value, max_value)的元组
            repeat_count: 每个维度的分割数量列表，每个元素表示对应维度要生成多少个均匀分布的值

        Returns:
            包含所有生成序列的列表，每个序列是一个浮点数列表，包含所有维度组合

        Example:
            ranges = [(0.0, 1.0), (-1.0, 1.0), (2.0, 5.0)]  # 3个维度
            generator = SequenceGenerator()
            sequences = generator.generate_sequences(ranges, [2, 3, 2])
            # 第1维度2个值，第2维度3个值，第3维度2个值，共生成2*3*2=12个序列
        """
        if not value_ranges:
            raise ValueError("value_ranges 不能为空")

        if not repeat_count:
            raise ValueError("repeat_count 不能为空")

        if len(value_ranges) != len(repeat_count):
            raise ValueError(f"value_ranges长度({len(value_ranges)})必须等于repeat_count长度({len(repeat_count)})")

        for i, count in enumerate(repeat_count):
            if count <= 0:
                raise ValueError(f"repeat_count[{i}] ({count}) 必须大于0")

        # 验证取值范围的有效性
        for i, (min_val, max_val) in enumerate(value_ranges):
            if min_val > max_val:
                raise ValueError(f"第{i}个维度的最小值({min_val})不能大于最大值({max_val})")

        # 为每个维度生成均匀分布的值
        dimension_values = []
        for (min_val, max_val), count in zip(value_ranges, repeat_count):
            if count == 1:
                values = [(min_val + max_val) / 2]  # 单个值时取中点
            else:
                values = [min_val + (max_val - min_val) * i / (count - 1) for i in range(count)]
            dimension_values.append(values)

        # 生成所有可能的组合
        sequences = []
        self._generate_combinations(dimension_values, [], 0, sequences)

        return sequences

    def generate_sequences_combined(self,
                                   combined_params: List[Tuple[float, float, int]]) -> List[List[float]]:
        """
        生成有序序列组合（使用组合参数）

        Args:
            combined_params: 组合参数列表，每个元素是(min_value, max_value, repeat_count)的元组

        Returns:
            包含所有生成序列的列表，每个序列是一个浮点数列表，包含所有维度组合

        Example:
            combined_params = [(0.0, 1.0, 3), (-1.0, 1.0, 3), (2.0, 5.0, 3)]
            generator = SequenceGenerator()
            sequences = generator.generate_sequences_combined(combined_params)
            # 每个维度3个值，共生成3*3*3=27个序列
        """
        if not combined_params:
            raise ValueError("combined_params 不能为空")

        # 分离范围和重复次数
        value_ranges = [(param[0], param[1]) for param in combined_params]
        repeat_count = [param[2] for param in combined_params]

        # 调用原有方法
        return self.generate_sequences(value_ranges, repeat_count)

    def _generate_combinations(self, dimension_values: List[List[float]],
                              current_sequence: List[float],
                              dimension_index: int,
                              result: List[List[float]]):
        """
        递归生成所有维度值的组合

        Args:
            dimension_values: 每个维度的所有可能值
            current_sequence: 当前正在构建的序列
            dimension_index: 当前处理的维度索引
            result: 存储结果的列表
        """
        if dimension_index == len(dimension_values):
            # 已经处理完所有维度，添加当前序列到结果中
            result.append(current_sequence.copy())
            return

        # 遍历当前维度的所有可能值
        for value in dimension_values[dimension_index]:
            current_sequence.append(value)
            self._generate_combinations(dimension_values, current_sequence, dimension_index + 1, result)
            current_sequence.pop()  # 回溯

    def _generate_ordered_sequence(self,
                                  value_ranges: List[Tuple[float, float]],
                                  index: int,
                                  total_count: int) -> List[float]:
        """
        生成有序序列的单个序列，使用基于维度数的进制系统

        Args:
            value_ranges: 取值范围数组
            index: 当前序列的索引 (0 到 total_count-1)
            total_count: 总序列数量

        Returns:
            单个有序序列
        """
        sequence = []
        dimension_count = len(value_ranges)

        # 将索引转换为基于维度数的进制表示
        # 这样可以确保每个维度的值均匀分布
        for dim_idx, (min_val, max_val) in enumerate(value_ranges):
            # 计算当前维度在多维索引中的位置
            if dimension_count == 1:
                normalized_index = index / (total_count - 1) if total_count > 1 else 0
            else:
                # 使用多维索引系统
                power = len(value_ranges) - 1 - dim_idx
                if total_count > 1:
                    # 计算在该维度上的步长
                    steps_per_dim = int(total_count ** (1/dimension_count))
                    dim_value = (index // (steps_per_dim ** power)) % steps_per_dim
                    normalized_index = dim_value / (steps_per_dim - 1) if steps_per_dim > 1 else 0
                else:
                    normalized_index = 0

            value = min_val + (max_val - min_val) * normalized_index
            sequence.append(value)

        return sequence

    def generate_sequences_batch(self,
                                value_ranges: List[Tuple[float, float]],
                                repeat_count: List[int]) -> np.ndarray:
        """
        批量生成有序序列组合（使用numpy，性能更好）

        Args:
            value_ranges: 包含每个维度取值范围的数组
            repeat_count: 每个维度的分割数量列表

        Returns:
            shape为(total_sequences, dimension_count)的numpy数组
        """
        if not value_ranges:
            raise ValueError("value_ranges 不能为空")

        if not repeat_count:
            raise ValueError("repeat_count 不能为空")

        if len(value_ranges) != len(repeat_count):
            raise ValueError(f"value_ranges长度({len(value_ranges)})必须等于repeat_count长度({len(repeat_count)})")

        for i, count in enumerate(repeat_count):
            if count <= 0:
                raise ValueError(f"repeat_count[{i}] ({count}) 必须大于0")

        for i, (min_val, max_val) in enumerate(value_ranges):
            if min_val > max_val:
                raise ValueError(f"第{i}个维度的最小值({min_val})不能大于最大值({max_val})")

        # 计算总序列数
        total_sequences = 1
        for count in repeat_count:
            total_sequences *= count

        dimension_count = len(value_ranges)
        sequences = np.zeros((total_sequences, dimension_count))

        # 为每个维度生成均匀分布的值
        dimension_values = []
        for (min_val, max_val), count in zip(value_ranges, repeat_count):
            if count == 1:
                values = [(min_val + max_val) / 2]  # 单个值时取中点
            else:
                values = [min_val + (max_val - min_val) * i / (count - 1) for i in range(count)]
            dimension_values.append(values)

        # 使用numpy生成所有组合
        seq_idx = [0]  # 使用列表以便在递归中修改
        self._fill_numpy_combinations(dimension_values, [], 0, sequences, seq_idx)

        return sequences

    def _fill_numpy_combinations(self, dimension_values: List[List[float]],
                                current_sequence: List[float],
                                dimension_index: int,
                                result: np.ndarray,
                                seq_idx: List[int]):
        """
        递归填充numpy数组，生成所有维度值的组合
        """
        if dimension_index == len(dimension_values):
            # 已经处理完所有维度，将当前序列添加到结果中
            for i, value in enumerate(current_sequence):
                result[seq_idx[0], i] = value
            seq_idx[0] += 1
            return

        # 遍历当前维度的所有可能值
        for value in dimension_values[dimension_index]:
            current_sequence.append(value)
            self._fill_numpy_combinations(dimension_values, current_sequence, dimension_index + 1, result, seq_idx)
            current_sequence.pop()  # 回溯


class SequenceManager:
    """
    序列管理器类
    管理多个命名的序列配置，并提供动态更新和生成功能
    """

    def __init__(self):
        """初始化序列管理器"""
        self.param_map: dict[str, Tuple[float, float, int]] = {}
        self.generator = SequenceGenerator()
        self.cached_sequences: List[Tuple[List[str], List[float]]] = []

    def clear_cache(self):
        """
        清除缓存
        """
        self.cached_sequences = []

    def update(self, name: str, param: Tuple[float, float, int]):
        """
        更新指定名称的参数配置

        Args:
            name: 配置名称
            param: 参数元组 (min_value, max_value, repeat_count)
            replace: 是否替换整个配置，False表示追加，True表示替换
        """
        self.param_map[name] = param
        self.clear_cache()

    def remove(self, name: str):
        """
        移除参数配置

        Args:
            name: 配置名称
            index: 要移除的索引，None表示移除整个配置
        """
        if name not in self.param_map:
            return

        self.param_map.pop(name)
        self.clear_cache()

    def get_sequences(self, use_cache: bool = True) -> List[Tuple[List[str], List[float]]]:
        """
        获取所有配置生成的序列

        Args:
            use_cache: 是否使用缓存

        Returns:
            生成的序列列表，每个元素是(配置名称, 序列)的元组
        """
        # 检查缓存
        if use_cache and self.cached_sequences:
            return self.cached_sequences

        # 生成新序列
        sequences = []
        name_list = list(self.param_map.keys())
        value_list = list(self.param_map.values())
        value_sequences = self.generator.generate_sequences_combined(value_list)

        for idx, values in enumerate(value_sequences):
            sequences.append((name_list, values))

        # 缓存结果
        if use_cache:
            self.cached_sequences = sequences

        return sequences

    def find_value(self, seq_idx: int, name: str) -> float:
        """
        通过序列索引和配置名称查找对应的值

        Args:
            seq_idx: 序列索引
            name: 配置名称

        Returns:
            对应的浮点数值
        """
        # 如果缓存为空，先生成缓存
        if not self.cached_sequences:
            self.get_sequences()

        # 检查序列索引范围
        if seq_idx < 0 or seq_idx >= len(self.cached_sequences):
            raise ValueError(f"序列索引 {seq_idx} 超出范围 [0, {len(self.cached_sequences)-1}]")

        # 获取序列
        name_list, value_list = self.cached_sequences[seq_idx]

        # 查找配置名称对应的值
        if name not in name_list:
            raise ValueError(f"配置 '{name}' 在序列中不存在")

        name_idx = name_list.index(name)
        return value_list[name_idx]


# 使用示例
if __name__ == "__main__":
    # 创建生成器实例
    generator = SequenceGenerator()

    print("=== SequenceGenerator 示例 ===")
    # 定义每个维度的取值范围
    ranges = [(0.0, 1.0), (-1.0, 1.0), (2.0, 5.0)]

    # 方法1：使用分离的参数
    print("方法1：使用分离的参数")
    sequences = generator.generate_sequences(ranges, [2, 2, 2])
    print(f"生成 {len(sequences)} 个序列:")
    for i, seq in enumerate(sequences):
        print(f"  序列 {i+1}: {[round(x, 3) for x in seq]}")

    # 方法2：使用组合参数
    print("\n方法2：使用组合参数")
    combined_params = [(0.0, 1.0, 2), (-1.0, 1.0, 2), (2.0, 5.0, 2)]
    sequences_combined = generator.generate_sequences_combined(combined_params)
    print(f"生成 {len(sequences_combined)} 个序列:")
    for i, seq in enumerate(sequences_combined):
        print(f"  序列 {i+1}: {[round(x, 3) for x in seq]}")

    print("\n" + "="*50)
    print("=== SequenceManager 示例 ===")

    # 创建序列管理器实例
    manager = SequenceManager()

    # 添加配置
    print("\n1. 添加配置")
    manager.update("config1", (0.0, 1.0, 3))  # 第一个配置
    manager.update("config2", (-1.0, 1.0, 2))  # 第二个配置
    manager.update("config3", (2.0, 5.0, 4))  # 第三个配置

    # 获取所有序列
    sequences = manager.get_sequences()
    print(f"所有配置生成 {len(sequences)} 个序列:")
    for name, seq in sequences:
        print(f"  {name}: {[round(x, 3) for x in seq]}")

    # 更新配置
    print("\n2. 更新配置")
    manager.update("config1", (0.5, 1.5, 2))  # 更新config1

    sequences_updated = manager.get_sequences(use_cache=False)  # 不使用缓存获取最新结果
    print(f"更新后生成 {len(sequences_updated)} 个序列:")
    for name, seq in sequences_updated:
        print(f"  {name}: {[round(x, 3) for x in seq]}")

    # 测试缓存
    print("\n3. 测试缓存")
    print("第一次获取（生成新序列）:")
    sequences_first = manager.get_sequences(use_cache=False)
    print(f"生成了 {len(sequences_first)} 个序列")

    print("第二次获取（使用缓存）:")
    sequences_cached = manager.get_sequences(use_cache=True)
    print(f"从缓存获取了 {len(sequences_cached)} 个序列")

    # 移除配置
    print("\n4. 移除配置")
    print(f"移除前的配置: {list(manager.param_map.keys())}")
    manager.remove("config2")
    print(f"移除config2后的配置: {list(manager.param_map.keys())}")

    sequences_after_remove = manager.get_sequences()
    print(f"移除后生成 {len(sequences_after_remove)} 个序列:")
    for name, seq in sequences_after_remove:
        print(f"  {name}: {[round(x, 3) for x in seq]}")

    # 清除缓存
    print("\n5. 清除缓存测试")
    print(f"清除前缓存大小: {len(manager.cached_sequences)}")
    manager.clear_cache()
    print(f"清除后缓存大小: {len(manager.cached_sequences)}")

    # 测试查找接口
    print("\n6. 测试查找接口")
    try:
        # 查找特定序列中的配置值
        value1 = manager.find_value(0, "config1")  # 序列0中config1的值
        value2 = manager.find_value(5, "config3")  # 序列5中config3的值
        value3 = manager.find_value(7, "config1")  # 序列10中config1的值

        print(f"  序列0中config1的值: {round(value1, 3)}")
        print(f"  序列5中config3的值: {round(value2, 3)}")
        print(f"  序列7中config1的值: {round(value3, 3)}")

        print(f"查找后缓存大小: {len(manager.cached_sequences)}")

    except ValueError as e:
        print(f"  错误: {e}")

    print(f"\n最终配置: {list(manager.param_map.keys())}")