"""
Windows 平台的库加载器
"""

import ctypes
import os
from os import environ


def load_libraries():
    """加载 Windows 平台的 FFmpeg DLL 文件"""
    ffmpeg_path = environ.get("FFMPEG_DLL_PATH")

    dll_list = [
        "avcodec-60.dll",
        "avdevice-60.dll",
        "avfilter-9.dll",
        "avformat-60.dll",
        "avutil-58.dll",
        "swresample-4.dll",
        "swscale-7.dll",
    ]

    # 检查 FFmpeg 路径是否存在
    if not os.path.exists(ffmpeg_path):
        print(f"Warning: FFmpeg path {ffmpeg_path} does not exist")
        return False

    loaded_count = 0
    for dll in dll_list:
        dll_path = ffmpeg_path + dll
        try:
            if os.path.exists(dll_path):
                ctypes.CDLL(dll_path)
                loaded_count += 1
                print(f"Loaded: {dll}")
            else:
                print(f"Warning: {dll_path} not found")
        except Exception as e:
            print(f"Error loading {dll}: {e}")

    print(f"Successfully loaded {loaded_count}/{len(dll_list)} Windows DLL files")
    return loaded_count > 0
