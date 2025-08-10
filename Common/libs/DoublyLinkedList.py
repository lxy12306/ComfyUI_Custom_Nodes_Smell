"""
通用双向链表实现
支持泛型、迭代器、索引访问等功能
"""

from typing import TypeVar, Generic, Optional, Iterator, Union, Any, Iterable
import weakref
import time

T = TypeVar('T')


class DoublyLinkedListNode(Generic[T]):
    """
    双向链表节点类

    Args:
        data: 节点存储的数据
    """

    def __init__(self, data: T):
        self.data: T = data
        self.next: Optional['DoublyLinkedListNode[T]'] = None
        self.prev: Optional['DoublyLinkedListNode[T]'] = None
        self.created_time = time.time()

    def __str__(self) -> str:
        return f"Node({self.data})"

    def __repr__(self) -> str:
        return self.__str__()


class DoublyLinkedList(Generic[T]):
    """
    通用双向链表类

    特性:
    - 支持泛型
    - 支持迭代器协议
    - 支持索引访问
    - 支持切片操作
    - 支持常用列表操作
    """

    def __init__(self, iterable: Optional[Iterable[T]] = None):
        """
        初始化双向链表

        Args:
            iterable: 可迭代对象，用于初始化链表
        """
        self.head: Optional[DoublyLinkedListNode[T]] = None
        self.tail: Optional[DoublyLinkedListNode[T]] = None
        self._size = 0

        # 如果提供了可迭代对象，初始化链表
        if iterable is not None:
            for item in iterable:
                self.append(item)

    def __len__(self) -> int:
        """返回链表长度"""
        return self._size

    def __bool__(self) -> bool:
        """判断链表是否为空"""
        return self._size > 0

    def __str__(self) -> str:
        """字符串表示"""
        items = [str(item) for item in self]
        return f"DoublyLinkedList([{', '.join(items)}])"

    def __repr__(self) -> str:
        return self.__str__()

    def __iter__(self) -> Iterator[T]:
        """正向迭代器"""
        current = self.head
        while current:
            yield current.data
            current = current.next

    def __reversed__(self) -> Iterator[T]:
        """反向迭代器"""
        current = self.tail
        while current:
            yield current.data
            current = current.prev

    def __getitem__(self, index: Union[int, slice]) -> Union[T, 'DoublyLinkedList[T]']:
        """索引访问和切片操作"""
        if isinstance(index, slice):
            return self._get_slice(index)

        if not isinstance(index, int):
            raise TypeError("索引必须是整数或切片")

        # 处理负索引
        if index < 0:
            index += self._size

        if index < 0 or index >= self._size:
            raise IndexError("链表索引超出范围")

        # 优化：根据索引位置选择从头部或尾部开始遍历
        if index < self._size // 2:
            # 从头部开始
            current = self.head
            for _ in range(index):
                if current is None:
                    raise IndexError("链表索引超出范围")
                current = current.next
        else:
            # 从尾部开始
            current = self.tail
            for _ in range(self._size - 1 - index):
                if current is None:
                    raise IndexError("链表索引超出范围")
                current = current.prev

        if current is None:
            raise IndexError("链表索引超出范围")
        return current.data

    def __setitem__(self, index: int, value: T) -> None:
        """设置指定索引的值"""
        if not isinstance(index, int):
            raise TypeError("索引必须是整数")

        # 处理负索引
        if index < 0:
            index += self._size

        if index < 0 or index >= self._size:
            raise IndexError("链表索引超出范围")

        # 找到对应节点
        if index < self._size // 2:
            current = self.head
            for _ in range(index):
                if current is None:
                    raise IndexError("链表索引超出范围")
                current = current.next
        else:
            current = self.tail
            for _ in range(self._size - 1 - index):
                if current is None:
                    raise IndexError("链表索引超出范围")
                current = current.prev

        if current is None:
            raise IndexError("链表索引超出范围")
        current.data = value

    def __delitem__(self, index: int) -> None:
        """删除指定索引的元素"""
        if not isinstance(index, int):
            raise TypeError("索引必须是整数")

        # 处理负索引
        if index < 0:
            index += self._size

        if index < 0 or index >= self._size:
            raise IndexError("链表索引超出范围")

        # 找到对应节点并删除
        if index < self._size // 2:
            current = self.head
            for _ in range(index):
                if current is None:
                    raise IndexError("链表索引超出范围")
                current = current.next
        else:
            current = self.tail
            for _ in range(self._size - 1 - index):
                if current is None:
                    raise IndexError("链表索引超出范围")
                current = current.prev

        if current is None:
            raise IndexError("链表索引超出范围")
        self._remove_node(current)

    def __eq__(self, other: Any) -> bool:
        """相等比较"""
        if not isinstance(other, DoublyLinkedList):
            return False

        if len(self) != len(other):
            return False

        for a, b in zip(self, other):
            if a != b:
                return False

        return True

    def __add__(self, other: 'DoublyLinkedList[T]') -> 'DoublyLinkedList[T]':
        """连接两个链表"""
        result = DoublyLinkedList[T]()
        for item in self:
            result.append(item)
        for item in other:
            result.append(item)
        return result

    def __iadd__(self, other: 'DoublyLinkedList[T]') -> 'DoublyLinkedList[T]':
        """就地连接"""
        for item in other:
            self.append(item)
        return self

    def _get_slice(self, slice_obj: slice) -> 'DoublyLinkedList[T]':
        """处理切片操作"""
        start, stop, step = slice_obj.indices(self._size)
        result = DoublyLinkedList[T]()

        if step == 1:
            # 优化：连续切片
            current = self.head
            for i in range(start):
                if current is None:
                    break
                current = current.next

            for i in range(start, stop):
                if current is None:
                    break
                result.append(current.data)
                current = current.next
        else:
            # 通用切片
            for i in range(start, stop, step):
                item = self[i]
                if not isinstance(item, DoublyLinkedList):  # 确保是 T 类型
                    result.append(item)

        return result

    def _get_node_at(self, index: int) -> DoublyLinkedListNode[T]:
        """获取指定索引的节点（内部使用）"""
        if index < 0:
            index += self._size

        if index < 0 or index >= self._size:
            raise IndexError("链表索引超出范围")

        if index < self._size // 2:
            current = self.head
            for _ in range(index):
                if current is None:
                    raise IndexError("链表索引超出范围")
                current = current.next
        else:
            current = self.tail
            for _ in range(self._size - 1 - index):
                if current is None:
                    raise IndexError("链表索引超出范围")
                current = current.prev

        if current is None:
            raise IndexError("链表索引超出范围")
        return current

    def _remove_node(self, node: DoublyLinkedListNode[T]) -> None:
        """移除指定节点（内部使用）"""
        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next

        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

        self._size -= 1

    def append(self, item: T) -> None:
        """在链表末尾添加元素"""
        new_node = DoublyLinkedListNode(item)

        if not self.head:
            self.head = self.tail = new_node
        else:
            if self.tail is not None:
                new_node.prev = self.tail
                self.tail.next = new_node
                self.tail = new_node

        self._size += 1

    def prepend(self, item: T) -> None:
        """在链表开头添加元素"""
        new_node = DoublyLinkedListNode(item)

        if not self.head:
            self.head = self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node

        self._size += 1

    def insert(self, index: int, item: T) -> None:
        """在指定位置插入元素"""
        if index < 0:
            index += self._size

        if index < 0:
            index = 0
        elif index > self._size:
            index = self._size

        if index == 0:
            self.prepend(item)
        elif index == self._size:
            self.append(item)
        else:
            new_node = DoublyLinkedListNode(item)
            target_node = self._get_node_at(index)

            new_node.next = target_node
            new_node.prev = target_node.prev
            if target_node.prev:
                target_node.prev.next = new_node
            target_node.prev = new_node

            self._size += 1

    def remove(self, item: T) -> None:
        """移除第一个匹配的元素"""
        current = self.head
        while current:
            if current.data == item:
                self._remove_node(current)
                return
            current = current.next

        raise ValueError(f"链表中没有找到元素: {item}")

    def pop(self, index: int = -1) -> T:
        """移除并返回指定位置的元素"""
        if self._size == 0:
            raise IndexError("pop from empty list")

        if index < 0:
            index += self._size

        if index < 0 or index >= self._size:
            raise IndexError("pop index out of range")

        node = self._get_node_at(index)
        data = node.data
        self._remove_node(node)
        return data

    def clear(self) -> None:
        """清空链表"""
        self.head = self.tail = None
        self._size = 0

    def index(self, item: T, start: int = 0, stop: Optional[int] = None) -> int:
        """查找元素的索引"""
        if stop is None:
            stop = self._size

        current = self.head
        for i in range(self._size):
            if current is None:
                break
            if i >= start and i < stop and current.data == item:
                return i
            current = current.next

        raise ValueError(f"链表中没有找到元素: {item}")

    def count(self, item: T) -> int:
        """统计元素出现次数"""
        count = 0
        for data in self:
            if data == item:
                count += 1
        return count

    def reverse(self) -> None:
        """就地反转链表"""
        current = self.head
        self.head, self.tail = self.tail, self.head

        while current:
            current.next, current.prev = current.prev, current.next
            current = current.prev  # 原来的 next

    def copy(self) -> 'DoublyLinkedList[T]':
        """创建链表的浅拷贝"""
        return DoublyLinkedList[T](self)

    def extend(self, iterable: Iterable[T]) -> None:
        """用可迭代对象扩展链表"""
        for item in iterable:
            self.append(item)

    def to_list(self) -> list[T]:
        """转换为Python列表"""
        return list(self)

    def is_empty(self) -> bool:
        """检查链表是否为空"""
        return self._size == 0

    def get_head(self) -> Optional[T]:
        """获取头部元素"""
        return self.head.data if self.head else None

    def get_tail(self) -> Optional[T]:
        """获取尾部元素"""
        return self.tail.data if self.tail else None

    def find_all(self, predicate) -> 'DoublyLinkedList[T]':
        """查找所有满足条件的元素"""
        result = DoublyLinkedList[T]()
        for item in self:
            if predicate(item):
                result.append(item)
        return result

    def filter(self, predicate) -> 'DoublyLinkedList[T]':
        """过滤元素（返回新链表）"""
        return self.find_all(predicate)

    def map(self, func) -> 'DoublyLinkedList':
        """映射操作（返回新链表）"""
        result = DoublyLinkedList()
        for item in self:
            result.append(func(item))
        return result

    def get_info(self) -> dict:
        """获取链表详细信息"""
        return {
            'size': self._size,
            'is_empty': self.is_empty(),
            'head': self.get_head(),
            'tail': self.get_tail(),
            'elements': self.to_list()
        }


def test_doubly_linked_list():
    """
    双向链表测试函数
    测试所有主要功能
    """
    print("=" * 60)
    print("双向链表测试开始")
    print("=" * 60)

    # 测试1: 基本创建和添加
    print("\n1. 测试基本创建和添加")
    dll = DoublyLinkedList[int]()
    print(f"空链表: {dll}")
    print(f"长度: {len(dll)}, 是否为空: {dll.is_empty()}")

    # 添加元素
    dll.append(1)
    dll.append(2)
    dll.append(3)
    print(f"添加1,2,3后: {dll}")

    dll.prepend(0)
    print(f"前置添加0后: {dll}")

    # 测试2: 索引访问
    print("\n2. 测试索引访问")
    print(f"dll[0] = {dll[0]}")
    print(f"dll[1] = {dll[1]}")
    print(f"dll[-1] = {dll[-1]}")
    print(f"dll[-2] = {dll[-2]}")

    # 修改元素
    dll[1] = 10
    print(f"设置dll[1]=10后: {dll}")

    # 测试3: 插入操作
    print("\n3. 测试插入操作")
    dll.insert(2, 20)
    print(f"在位置2插入20后: {dll}")

    dll.insert(0, -1)
    print(f"在位置0插入-1后: {dll}")

    dll.insert(len(dll), 99)
    print(f"在末尾插入99后: {dll}")

    # 测试4: 删除操作
    print("\n4. 测试删除操作")
    removed = dll.pop()
    print(f"pop()移除: {removed}, 链表: {dll}")

    removed = dll.pop(0)
    print(f"pop(0)移除: {removed}, 链表: {dll}")

    dll.remove(20)
    print(f"remove(20)后: {dll}")

    # 测试5: 查找操作
    print("\n5. 测试查找操作")
    try:
        index = dll.index(10)
        print(f"元素10的索引: {index}")
    except ValueError as e:
        print(f"查找错误: {e}")

    count = dll.count(2)
    print(f"元素2的数量: {count}")

    # 测试6: 切片操作
    print("\n6. 测试切片操作")
    print(f"原链表: {dll}")
    print(f"dll[1:3]: {dll[1:3]}")
    print(f"dll[:2]: {dll[:2]}")
    print(f"dll[::2]: {dll[::2]}")
    print(f"dll[::-1]: {dll[::-1]}")

    # 测试7: 迭代器
    print("\n7. 测试迭代器")
    print("正向迭代:", end=" ")
    for item in dll:
        print(item, end=" ")
    print()

    print("反向迭代:", end=" ")
    for item in reversed(dll):
        print(item, end=" ")
    print()

    # 测试8: 链表操作
    print("\n8. 测试链表操作")
    dll2 = DoublyLinkedList([100, 200, 300])
    print(f"新链表dll2: {dll2}")

    dll3 = dll + dll2
    print(f"dll + dll2: {dll3}")

    dll_copy = dll.copy()
    print(f"dll的拷贝: {dll_copy}")

    # 测试9: 高级操作
    print("\n9. 测试高级操作")
    dll.extend([4, 5, 6])
    print(f"扩展[4,5,6]后: {dll}")

    # 过滤偶数
    even_nums = dll.filter(lambda x: x % 2 == 0)
    print(f"过滤偶数: {even_nums}")

    # 映射平方
    squared = dll.map(lambda x: x * x)
    print(f"平方映射: {squared}")

    # 测试10: 反转
    print("\n10. 测试反转")
    print(f"反转前: {dll}")
    dll.reverse()
    print(f"反转后: {dll}")

    # 测试11: 边界情况
    print("\n11. 测试边界情况")
    empty_dll = DoublyLinkedList[str]()

    try:
        empty_dll.pop()
    except IndexError as e:
        print(f"空链表pop错误: {e}")

    try:
        empty_dll.remove("不存在")
    except ValueError as e:
        print(f"移除不存在元素错误: {e}")

    try:
        print(f"空链表索引访问: {empty_dll[0]}")
    except IndexError as e:
        print(f"空链表索引错误: {e}")

    # 测试12: 字符串类型
    print("\n12. 测试字符串类型")
    str_dll = DoublyLinkedList(["hello", "world", "python"])
    print(f"字符串链表: {str_dll}")
    str_dll.insert(1, "beautiful")
    print(f"插入beautiful后: {str_dll}")

    # 测试13: 比较操作
    print("\n13. 测试比较操作")
    dll_a = DoublyLinkedList([1, 2, 3])
    dll_b = DoublyLinkedList([1, 2, 3])
    dll_c = DoublyLinkedList([1, 2, 4])

    print(f"dll_a == dll_b: {dll_a == dll_b}")
    print(f"dll_a == dll_c: {dll_a == dll_c}")

    # 测试14: 详细信息
    print("\n14. 测试详细信息")
    info = dll.get_info()
    print("链表详细信息:")
    for key, value in info.items():
        print(f"  {key}: {value}")

    # 测试15: 性能测试
    print("\n15. 性能测试")
    import time

    # 测试大量添加操作
    start_time = time.time()
    large_dll = DoublyLinkedList[int]()
    for i in range(10000):
        large_dll.append(i)

    end_time = time.time()
    print(f"添加10000个元素耗时: {end_time - start_time:.4f}秒")

    # 测试随机访问
    start_time = time.time()
    for i in range(0, 10000, 100):
        _ = large_dll[i]

    end_time = time.time()
    print(f"100次随机访问耗时: {end_time - start_time:.4f}秒")

    print("\n" + "=" * 60)
    print("双向链表测试完成")
    print("=" * 60)


if __name__ == "__main__":
    # 运行测试
    test_doubly_linked_list()
