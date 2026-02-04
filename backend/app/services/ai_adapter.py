"""
AI 服务适配器
用于统一调用不同的 AI 模型（本地 Ollama 和云端 Coze）
"""
import json
import httpx
import logging
from typing import Dict, Any, AsyncGenerator, Optional
from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class BaseAIEngine(ABC):
    """AI 引擎基类"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        pass


class OllamaEngine(BaseAIEngine):
    """Ollama 本地模型引擎"""

    def __init__(self, model_name: str = "qwen3:8b", base_url: str = None):
        self.model_name = model_name
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.timeout = 300  # 5分钟超时

    async def generate(self, prompt: str, **kwargs) -> str:
        """同步生成响应"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": kwargs.get("temperature", 0.1),
                            "top_p": kwargs.get("top_p", 0.9),
                        }
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    logger.error(f"Ollama API 错误: {response.status_code} - {response.text}")
                    raise Exception(f"Ollama API 调用失败: {response.status_code}")

        except httpx.TimeoutException:
            logger.error("Ollama 请求超时")
            raise Exception("Ollama 请求超时，请检查服务状态")
        except Exception as e:
            logger.error(f"Ollama 调用异常: {str(e)}")
            raise

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成响应"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": kwargs.get("temperature", 0.1),
                            "top_p": kwargs.get("top_p", 0.9),
                        }
                    }
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        yield data["response"]
                                    if data.get("done", False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                    else:
                        logger.error(f"Ollama 流式 API 错误: {response.status_code}")
                        raise Exception(f"Ollama 流式调用失败: {response.status_code}")

        except httpx.TimeoutException:
            logger.error("Ollama 流式请求超时")
            raise Exception("Ollama 流式请求超时")
        except Exception as e:
            logger.error(f"Ollama 流式调用异常: {str(e)}")
            raise

    async def check_connection(self) -> bool:
        """检查连接状态"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False


class CozeEngine(BaseAIEngine):
    """Coze 云端模型引擎（暂不实现）"""

    async def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError("Coze 引擎暂未实现")

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Coze 流式引擎暂未实现")


class AIAdapter:
    """AI 适配器主类"""

    def __init__(self):
        self.ollama_engine = OllamaEngine()
        self.coze_engine = CozeEngine()  # 暂未实现

    async def formal_check(self, text: str) -> Dict[str, Any]:
        """形式检查：错别字、格式等"""
        prompt = f"""你是一个专业的专利校对员。请检查以下文本中的错别字、标点错误和格式问题。

文本内容：
{text}

请以 JSON 格式输出结果，包含以下字段：
{{
    "errors": [
        {{
            "location": "错误位置描述",
            "original": "原文内容",
            "suggestion": "修改建议",
            "error_type": "错误类型（错别字/标点/格式）",
            "severity": "严重程度（high/medium/low）"
        }}
    ],
    "summary": "整体审核总结"
}}

请只返回 JSON 格式，不要包含其他解释。"""

        try:
            response = await self.ollama_engine.generate(prompt)
            # 尝试解析 JSON 响应
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # 如果不是标准 JSON，尝试提取 JSON 部分
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"errors": [], "summary": f"AI 响应解析失败: {response}"}

        except Exception as e:
            logger.error(f"形式检查失败: {str(e)}")
            return {"errors": [], "summary": f"检查失败: {str(e)}"}

    async def logic_check(self, claims: str, description: str) -> AsyncGenerator[str, None]:
        """逻辑检查：权利要求支持性分析"""
        prompt = f"""你是一个资深专利审查员。请分析以下权利要求书是否得到了说明书的充分支持。

权利要求书：
{claims}

说明书：
{description}

请逐步分析：
1. 权利要求中的每个技术特征
2. 说明书是否有对应的描述
3. 可能存在的支持性问题
4. 改进建议

请详细分析并给出专业意见。"""

        try:
            async for chunk in self.ollama_engine.generate_stream(prompt):
                yield chunk
        except Exception as e:
            logger.error(f"逻辑检查失败: {str(e)}")
            yield f"分析失败: {str(e)}"


# 全局 AI 适配器实例
ai_adapter = AIAdapter()