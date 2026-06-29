"""
Demo 后端服务器 - 用于 DSW (Data Science Workshop) 部署

功能：
  1. 提供静态网页服务（index.html）
  2. WebSocket 服务接收用户的动作/prompt，推送生成的视频帧

部署方式（在阿里云 DSW 的终端中运行）：
  pip install fastapi uvicorn websockets aiofiles
  python server.py

  然后在 DSW 的"自定义服务"或端口转发中暴露 8080 端口
"""

import asyncio
import io
import json
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# ============================================================
# 配置
# ============================================================
HOST = "0.0.0.0"
HTTP_PORT = 8080       # 网页服务端口
WS_PORT = 8765         # WebSocket 端口（前端连接用）

# ============================================================
# FastAPI App
# ============================================================
app = FastAPI()

# 静态文件服务
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def index():
    """返回主页"""
    return FileResponse(Path(__file__).parent / "index.html")


# ============================================================
# WebSocket 服务（视频流式生成）
# ============================================================

# ---- 在这里替换为你的模型 ----
# from your_model import StreamingPipeline
# pipeline = StreamingPipeline()

class DummyPipeline:
    """
    模拟的 Pipeline，用于测试前端交互。
    替换为你的真实模型后删除这个类。
    """
    def __init__(self):
        self.current_prompt = ""
        self.frame_count = 0

    def set_prompt(self, prompt: str):
        self.current_prompt = prompt
        print(f"[Pipeline] Prompt switched to: {prompt[:50]}...")

    def generate_next_frame(self, keyboard, mouse):
        """
        生成下一帧（返回 JPEG bytes）

        在真实实现中：
          1. 把 keyboard/mouse 编码为动作条件
          2. DiT 少步去噪生成 latent
          3. VAE 解码为像素
          4. 编码为 JPEG 返回
        """
        import numpy as np
        self.frame_count += 1

        # 生成一个假的彩色帧用于测试
        h, w = 360, 640
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # 根据按键改变颜色
        r = 50 + keyboard[0] * 100  # W pressed → more red
        g = 50 + keyboard[2] * 100  # A pressed → more green
        b = 50 + keyboard[1] * 100  # S pressed → more blue
        frame[:, :] = [r, g, b]

        # 加个移动的方块表示动态
        x = (self.frame_count * 5) % w
        y = h // 2
        frame[y-20:y+20, x:min(x+40, w)] = [255, 255, 255]

        # 编码为 JPEG
        from PIL import Image
        img = Image.fromarray(frame)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=80)
        return buf.getvalue()


# 初始化 Pipeline
pipeline = DummyPipeline()
# pipeline = StreamingPipeline()  # 替换为你的真实模型


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """处理 WebSocket 连接"""
    await websocket.accept()
    print("[WS] Client connected")

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg["type"] == "init":
                # 初始化生成
                pipeline.set_prompt(msg["prompt"])
                print(f"[WS] Generation started: mode={msg.get('mode')}, "
                      f"resolution={msg.get('resolution')}")

            elif msg["type"] == "action":
                # 接收动作，生成下一帧
                keyboard = msg.get("keyboard", [0, 0, 0, 0])
                mouse = msg.get("mouse", [0, 0])

                # 生成帧
                frame_bytes = pipeline.generate_next_frame(keyboard, mouse)

                # 发送帧给前端
                await websocket.send_bytes(frame_bytes)

            elif msg["type"] == "prompt_switch":
                # 切换 Prompt
                pipeline.set_prompt(msg["prompt"])
                print(f"[WS] Prompt switched")

    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS] Error: {e}")


# ============================================================
# 启动服务
# ============================================================
if __name__ == "__main__":
    print(f"""
    ==========================================
    Demo Server Starting
    ==========================================
    Web UI:    http://localhost:{HTTP_PORT}
    WebSocket: ws://localhost:{HTTP_PORT}/ws

    In DSW: Use the port forwarding feature
    to access from your browser.
    ==========================================
    """)

    uvicorn.run(app, host=HOST, port=HTTP_PORT)
