"""
Linux 平台的库加载器
"""

import ctypes
from ctypes.util import find_library


def load_libraries():
    """加载 Linux 平台的 FFmpeg 共享库文件"""
    lib_list = [
        "avcodec",
        "avdevice",
        "avfilter",
        "avformat",
        "avutil",
        "swresample",
        "swscale",
    ]

    loaded_count = 0
    for lib in lib_list:
        try:
            # 尝试使用系统路径查找库
            lib_path = find_library(lib)
            if lib_path:
                ctypes.CDLL(lib_path)
                loaded_count += 1
                print(f"Loaded: lib{lib}.so from {lib_path}")
            else:
                # 尝试直接加载
                ctypes.CDLL(f"lib{lib}.so")
                loaded_count += 1
                print(f"Loaded: lib{lib}.so")
        except Exception as e:
            print(f"Error loading lib{lib}.so: {e}")

    print(f"Successfully loaded {loaded_count}/{len(lib_list)} Linux shared libraries")
    return loaded_count > 0
