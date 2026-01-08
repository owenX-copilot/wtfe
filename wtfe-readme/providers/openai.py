"""
OpenAI-compatible API provider.
Supports: OpenAI, SiliconFlow, Azure OpenAI, Ollama, vLLM, etc.
"""
import requests
import time
from typing import Dict, Any, Optional
from .base import AIProvider, APIError


class OpenAIProvider(AIProvider):
    """OpenAI兼容格式的Provider（支持所有OpenAI API兼容服务）"""
    
    def generate(self, prompt: str, **override_params) -> str:
        """
        使用OpenAI格式API生成文本
        
        Args:
            prompt: 输入提示词
            **override_params: 临时覆盖参数
        
        Returns:
            生成的文本
        """
        # 合并默认参数和覆盖参数
        params = {
            'temperature': self.kwargs.get('temperature', 0.7),
            'max_tokens': self.kwargs.get('max_tokens', 4096),
            'top_p': self.kwargs.get('top_p', 0.9),
            'stream': self.kwargs.get('stream', False),
            **override_params
        }
        
        # 构造请求体（OpenAI格式）
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert technical writer who generates clear, comprehensive README documentation for software projects."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": params['temperature'],
            "max_tokens": params['max_tokens'],
            "top_p": params['top_p'],
            "stream": params['stream']
        }
        
        # DeepSeek特有参数（其他模型会忽略）
        if 'deepseek' in self.model.lower():
            payload['enable_thinking'] = self.kwargs.get('enable_thinking', False)
            if payload['enable_thinking']:
                payload['thinking_budget'] = self.kwargs.get('thinking_budget', 4096)
        
        # 发送请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        endpoint = f"{self.base_url}/chat/completions"
        
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=self.kwargs.get('timeout', 60)
            )
            
            # 检查HTTP状态码
            if response.status_code != 200:
                raise APIError(
                    message=f"API request failed: {response.text}",
                    status_code=response.status_code,
                    response_body=response.text
                )
            
            # 解析响应
            result = response.json()
            
            # 提取生成的内容
            if 'choices' not in result or len(result['choices']) == 0:
                raise APIError(f"Invalid API response: no choices found. Response: {result}")
            
            content = result['choices'][0]['message']['content']
            return content.strip()
        
        except requests.exceptions.Timeout:
            raise APIError(f"Request timeout after {self.kwargs.get('timeout', 60)} seconds")
        except requests.exceptions.ConnectionError as e:
            raise APIError(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
        except KeyError as e:
            raise APIError(f"Failed to parse API response: missing key {e}")
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效（发送一个测试请求）
        
        Returns:
            配置是否有效
        """
        try:
            # 发送一个最小的测试请求
            test_prompt = "Hello"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": test_prompt}],
                "max_tokens": 10
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
        
        except Exception:
            return False
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> Optional[float]:
        """
        估算API调用成本（美元）
        
        Args:
            input_tokens: 输入token数
            output_tokens: 输出token数
        
        Returns:
            成本（美元），如果无法估算返回None
        """
        # 常见模型的定价（每百万token，美元）
        PRICING = {
            # SiliconFlow定价（极便宜）
            'deepseek-ai/DeepSeek-V3.2': {'input': 0.27, 'output': 1.1},
            'deepseek-ai/DeepSeek-V3.2-Exp': {'input': 0.27, 'output': 1.1},
            'Qwen/Qwen2.5-72B-Instruct': {'input': 0.35, 'output': 0.35},
            
            # OpenAI定价
            'gpt-4o': {'input': 2.5, 'output': 10.0},
            'gpt-4o-mini': {'input': 0.15, 'output': 0.6},
            'gpt-3.5-turbo': {'input': 0.5, 'output': 1.5},
        }
        
        if self.model not in PRICING:
            return None
        
        pricing = PRICING[self.model]
        cost = (input_tokens / 1_000_000 * pricing['input'] + 
                output_tokens / 1_000_000 * pricing['output'])
        return cost
