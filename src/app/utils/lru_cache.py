"""
LRU缓存实现 - 用于内存管理优化

提供固定容量的LRU缓存，支持内存占用估算和回调函数
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Callable, Generic, TypeVar


K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    """
    LRU (Least Recently Used) 缓存
    
    特性：
    - 固定容量，超出时自动淘汰最久未使用的项
    - 支持计算每个值的大小
    - 支持淘汰回调函数
    - 线程安全（在单线程Qt环境中使用）
    
    示例：
        cache = LRUCache[str, QPixmap](max_size=100, max_memory_mb=256)
        cache.put("key1", pixmap, size_bytes=pixmap.sizeInBytes())
        value = cache.get("key1")
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: float | None = None,
        size_callback: Callable[[V], int] | None = None,
        eviction_callback: Callable[[K, V], None] | None = None,
    ) -> None:
        """
        初始化LRU缓存
        
        Args:
            max_size: 最大条目数
            max_memory_mb: 最大内存占用(MB)，None表示不限制
            size_callback: 计算值大小的回调函数，返回字节数
            eviction_callback: 淘汰条目时的回调函数
        """
        self._max_size = max_size
        self._max_memory = int(max_memory_mb * 1024 * 1024) if max_memory_mb else None
        self._size_callback = size_callback
        self._eviction_callback = eviction_callback
        
        self._cache: OrderedDict[K, V] = OrderedDict()
        self._size_map: dict[K, int] = {}
        self._current_memory = 0
    
    def get(self, key: K) -> V | None:
        """
        获取缓存值，如果不存在返回None
        
        获取成功会将该项移到最近使用位置
        """
        if key not in self._cache:
            return None
        
        # 移到末尾（最近使用）
        value = self._cache.pop(key)
        self._cache[key] = value
        return value
    
    def put(self, key: K, value: V, size_bytes: int | None = None) -> None:
        """
        添加或更新缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
            size_bytes: 值的大小（字节），如果提供则直接使用，否则通过size_callback计算
        """
        # 如果键已存在，先移除旧的
        if key in self._cache:
            self._remove(key)
        
        # 计算大小
        if size_bytes is not None:
            item_size = size_bytes
        elif self._size_callback is not None:
            item_size = self._size_callback(value)
        else:
            item_size = 0
        
        # 检查单个体积是否超过限制
        if self._max_memory and item_size > self._max_memory:
            # 单个项就超过限制，不缓存
            if self._eviction_callback:
                self._eviction_callback(key, value)
            return
        
        # 淘汰旧项直到满足容量和内存限制
        while self._needs_eviction(1, item_size):
            self._evict_lru()
        
        # 添加新项
        self._cache[key] = value
        self._size_map[key] = item_size
        self._current_memory += item_size
    
    def _needs_eviction(self, new_count: int, new_memory: int) -> bool:
        """检查是否需要淘汰旧项"""
        # 检查数量限制
        if len(self._cache) + new_count > self._max_size:
            return True
        
        # 检查内存限制
        if self._max_memory and self._current_memory + new_memory > self._max_memory:
            return True
        
        return False
    
    def _evict_lru(self) -> None:
        """淘汰最久未使用的项"""
        if not self._cache:
            return
        
        # 获取最旧的项（OrderedDict的第一个）
        key, value = self._cache.popitem(last=False)
        self._remove_internal(key, value)
    
    def _remove(self, key: K) -> V | None:
        """移除指定项"""
        if key not in self._cache:
            return None
        
        value = self._cache.pop(key)
        self._remove_internal(key, value)
        return value
    
    def _remove_internal(self, key: K, value: V) -> None:
        """内部移除处理"""
        # 减少内存计数
        item_size = self._size_map.pop(key, 0)
        self._current_memory -= item_size
        
        # 调用淘汰回调
        if self._eviction_callback:
            self._eviction_callback(key, value)
    
    def remove(self, key: K) -> V | None:
        """移除指定项并返回值"""
        return self._remove(key)
    
    def clear(self) -> None:
        """清空缓存"""
        if self._eviction_callback:
            for key, value in self._cache.items():
                self._eviction_callback(key, value)
        
        self._cache.clear()
        self._size_map.clear()
        self._current_memory = 0
    
    def contains(self, key: K) -> bool:
        """检查是否包含指定键（不改变访问顺序）"""
        return key in self._cache
    
    def __contains__(self, key: K) -> bool:
        """支持in操作符"""
        return self.contains(key)
    
    def __len__(self) -> int:
        """返回缓存项数量"""
        return len(self._cache)
    
    @property
    def size(self) -> int:
        """返回缓存项数量"""
        return len(self._cache)
    
    @property
    def memory_usage(self) -> int:
        """返回当前内存占用（字节）"""
        return self._current_memory
    
    @property
    def memory_usage_mb(self) -> float:
        """返回当前内存占用（MB）"""
        return self._current_memory / (1024 * 1024)
    
    def keys(self):
        """返回所有键的视图"""
        return self._cache.keys()
    
    def values(self):
        """返回所有值的视图"""
        return self._cache.values()
    
    def items(self):
        """返回所有键值对的视图"""
        return self._cache.items()
