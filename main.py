try:
    from reload_dll.reload import load_platform_libraries

    load_platform_libraries()
except ImportError:
    pass

import argparse
import json
import requests

from bailing import robot
from bailing.utils import load_mcp_config
from bailing import logger


def push2web(payload):
    try:
        data = json.dumps(payload, ensure_ascii=False)
        url = "http://127.0.0.1:5000/add_message"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        response = requests.request(
            "POST", url, headers=headers, data=data.encode("utf-8")
        )
        logger.info(response.text)
    except Exception as e:
        logger.error(f"callback error：{payload}{e}")


def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="百聆 AI 聊天机器人")

    # Add arguments
    parser.add_argument(
        "--config", type=str, help="配置文件路径", default="config/config.yaml"
    )
    parser.add_argument(
        "--mcp-config",
        type=str,
        help="MCP 配置文件路径",
        default="config/github-copilot-mcp.example.json",
    )

    # Parse arguments
    args = parser.parse_args()
    config_path = args.config
    mcp_config_path = args.mcp_config

    # 加载 MCP 配置
    mcp_config = load_mcp_config(mcp_config_path)

    # 创建机器人实例
    bailing_robot = robot.Robot(config_path, mcp_config=mcp_config)
    bailing_robot.listen_dialogue(push2web)
    bailing_robot.run()


if __name__ == "__main__":
    main()
