import json
import logging

logger = logging.getLogger(__name__)

json_path = "./config/github-copilot-mcp.example.json"


def get_mcp_object():
    """从JSON文件中提取mcp对象"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            j = json.load(f)
            logger.info(f"成功加载JSON文件: {json_path}")

            # 提取mcp对象
            mcp_obj = j.get("mcp")
            if mcp_obj:
                logger.info(f"成功提取mcp对象: {mcp_obj}")
                return mcp_obj
            else:
                logger.warning("JSON中未找到mcp对象")
                return None

    except FileNotFoundError:
        logger.error(f"文件未找到: {json_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON解码错误: {e} - 文件: {json_path}")
        return None
    except Exception as e:
        logger.error(f"发生错误: {e} - 文件: {json_path}")
        return None


# 全局变量存储mcp对象
mcp_config = get_mcp_object()

if __name__ == "__main__":
    if mcp_config:
        print("MCP对象:", mcp_config)
        print("MCP服务器配置:")
        for server_name, server_config in mcp_config.get("servers", {}).items():
            print(f"  - {server_name}: {server_config}")
    else:
        print("未能提取MCP对象。请检查日志以获取更多信息。")
