"""Ollama 连接测试脚本 - 模拟 ollama.py 的请求格式"""
import httpx
from dotenv import load_dotenv

load_dotenv()
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
print(f"OLLAMA_URL: {OLLAMA_URL}")

def test():
    try:
        with httpx.Client(timeout=300.0) as client:
            # 测试 1: 完整 payload（模拟 ollama.py）
            print("\n[测试1] 发送完整 payload (think + options)...")
            resp = client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": "qwen3:8b",
                    "messages": [{"role": "user", "content": "hi"}],
                    "think": True,
                    "stream": True,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_ctx": 32768,
                        "max_tokens": 40960,
                        "keep_alive": "24h",
                        "repeat_penalty": 1.0,
                    },
                }
            )
            print(f"状态: {resp.status_code}")
            print(f"响应: {resp.text[:300]}")

            # 测试 2: 简化 payload
            print("\n[测试2] 简化 payload (无 options)...")
            resp = client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": "qwen3:8b",
                    "messages": [{"role": "user", "content": "hi"}],
                    "stream": True,
                }
            )
            print(f"状态: {resp.status_code}")
            print(f"响应: {resp.text[:300]}")

            # 测试 3: 带 think 参数
            print("\n[测试3] 带 think 参数...")
            resp = client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": "qwen3:8b",
                    "messages": [{"role": "user", "content": "hi"}],
                    "think": True,
                    "stream": True,
                }
            )
            print(f"状态: {resp.status_code}")
            print(f"响应: {resp.text[:300]}")

    except Exception as e:
        print(f"\n错误: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test()
