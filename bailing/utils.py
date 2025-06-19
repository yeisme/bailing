import yaml
import json
import re
import os
import logging

# 获取 logger
logger = logging.getLogger(__name__)


def load_prompt(prompt_path):
    with open(prompt_path, "r", encoding="utf-8") as file:
        prompt = file.read()
    return prompt.strip()


def read_json_file(file_path):
    """读取 JSON 文件并返回内容"""
    with open(file_path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"解析 JSON 时出错: {e}")
            return None


def write_json_file(file_path, data):
    """将数据写入 JSON 文件"""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def read_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config


def is_segment(tokens):
    if tokens[-1] in (",", ".", "?", "，", "。", "？", "！", "!", ";", "；", ":", "："):
        return True
    else:
        return False


def is_interrupt(query: str):
    for interrupt_word in (
        "停一下",
        "听我说",
        "不要说了",
        "stop",
        "hold on",
        "excuse me",
    ):
        if query.lower().find(interrupt_word) >= 0:
            return True
    return False


def extract_json_from_string(input_string):
    """提取字符串中的 JSON 部分"""
    pattern = r"(\{.*\})"
    match = re.search(pattern, input_string)
    if match:
        return match.group(1)  # 返回提取的 JSON 字符串
    return None


def get_mcp_object(mcp_config=None):
    """从MCP配置中提取mcp对象

    Args:
        mcp_config: MCP配置对象

    Returns:
        dict: MCP对象，如果提取失败返回 None
    """
    if mcp_config is None:
        logger.warning("MCP配置对象为空")
        return None

    mcp_obj = mcp_config.get("mcp")
    if mcp_obj:
        logger.info(f"成功提取mcp对象: {mcp_obj}")
        return mcp_obj
    else:
        logger.warning("MCP配置中未找到mcp对象")
        return None


def load_mcp_config(mcp_config_path):
    """加载 MCP 配置文件

    Args:
        mcp_config_path: MCP 配置文件路径

    Returns:
        dict: MCP 配置对象，如果加载失败返回 None
    """
    if not mcp_config_path or not os.path.exists(mcp_config_path):
        logger.info(f"MCP 配置文件不存在: {mcp_config_path}")
        return None

    try:
        with open(mcp_config_path, "r", encoding="utf-8") as f:
            mcp_config = json.load(f)
        logger.info(f"成功加载 MCP 配置文件: {mcp_config_path}")
        return get_mcp_object(mcp_config)
    except Exception as e:
        logger.error(f"加载 MCP 配置文件失败: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    mcp_config_path = "./config/github-copilot-mcp.example.json"
    mcp_config = load_mcp_config(mcp_config_path)
    if mcp_config:
        print("MCP 配置加载成功:", mcp_config)
    else:
        print("MCP 配置加载失败")
