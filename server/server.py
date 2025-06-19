from pathlib import Path
from typing import Dict, List, Any
from litestar import Litestar, WebSocket, get, post, websocket
from litestar.response import Template
from litestar.template.config import TemplateConfig
from litestar.exceptions import WebSocketException
from litestar.contrib.jinja import JinjaTemplateEngine

# 存储对话数据
dialogue: List[Dict[str, Any]] = []

# 存储活跃的WebSocket连接
active_connections: List[WebSocket] = []


@websocket("/ws")
async def websocket_handler(socket: WebSocket) -> None:
    """处理WebSocket连接"""
    await socket.accept()
    active_connections.append(socket)

    try:
        # 发送初始对话数据
        await socket.send_json({"type": "update_dialogue", "data": dialogue})

        # 保持连接活跃
        while True:
            try:
                # 等待客户端消息，用于保持连接
                await socket.receive_json()
            except Exception:
                break

    except WebSocketException:
        pass
    finally:
        if socket in active_connections:
            active_connections.remove(socket)


async def broadcast_dialogue_update():
    """广播对话更新到所有连接的客户端"""
    if not active_connections:
        return

    # 移除已断开的连接
    disconnected = []
    for connection in active_connections[:]:
        try:
            await connection.send_json({"type": "update_dialogue", "data": dialogue})
        except Exception:
            disconnected.append(connection)

    # 清理断开的连接
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)


@get("/")
async def index() -> Template:
    """返回首页模板"""
    return Template("index.html")


@post("/add_message")
async def add_message(data: Dict[str, Any]) -> Dict[str, str]:
    """添加新消息到对话"""
    message = {
        "role": data.get("role"),
        "content": data.get("content"),
        "start_time": "",
        "end_time": "",
        "audio_file": "",
        "tts_file": "",
        "vad_status": "",
    }
    dialogue.append(message)

    # 异步广播更新
    await broadcast_dialogue_update()

    return {"status": "success"}


# 配置模板引擎
template_config = TemplateConfig(
    directory=Path(__file__).parent / "templates",
    engine=JinjaTemplateEngine,
)

# 创建Litestar应用
app = Litestar(
    route_handlers=[
        index,
        add_message,
        websocket_handler,
    ],
    template_config=template_config,
    debug=True,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True, log_level="info")
