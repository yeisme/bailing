"""
动态加载平台相关的库文件
"""

import platform
import importlib


def load_platform_libraries():
    """根据平台动态加载相应的库文件"""
    system = platform.system().lower()

    # 构建模块名
    module_name = f"reload_dll.reload_{system}"

    try:
        # 动态导入平台相关的模块
        module = importlib.import_module(module_name)
        if hasattr(module, "load_libraries"):
            module.load_libraries()
            print(f"Successfully loaded {system} libraries")
        else:
            print(f"Warning: {module_name} module found but no load_libraries function")
    except ImportError:
        print(f"Warning: Platform-specific module {module_name} not found")
        # 尝试加载通用的库加载逻辑
        try:
            from . import reload_common

            reload_common.load_libraries()
        except ImportError:
            print("No platform-specific or common library loader found")
    except Exception as e:
        print(f"Error loading {system} libraries: {e}")
