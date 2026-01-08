"""
Abstract base class for AI providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AIProvider(ABC):
    """AI服务提供商抽象基类"""
    
    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        """
        初始化Provider
        
        Args:
            api_key: API密钥
            base_url: API端点
            model: 模型名称
            **kwargs: 额外参数（如temperature, max_tokens等）
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')  # 移除末尾斜杠
        self.model = model
        self.kwargs = kwargs
    
    @abstractmethod
    def generate(self, prompt: str, **override_params) -> str:
        """
        生成文本
        
        Args:
            prompt: 输入提示词
            **override_params: 临时覆盖参数（如max_tokens等）
        
        Returns:
            生成的文本内容
        
        Raises:
            APIError: API调用失败
            ValueError: 参数错误
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            配置是否有效
        """
        pass


class APIError(Exception):
    """API调用错误"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)
    
    def __str__(self):
        if self.status_code:
            return f"API Error (HTTP {self.status_code}): {self.message}"
        return f"API Error: {self.message}"
