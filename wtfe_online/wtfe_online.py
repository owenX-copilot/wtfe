#!/usr/bin/env python3
"""
WTFE Online Service Module

Provides functionality to interact with WTFE API online services.
This is an optional module, users can choose to use online services or local analysis.
"""

import sys
import os
import json
import requests
from typing import Optional, Dict, Any
from getpass import getpass

# Import waiting manager for elegant waiting effects
try:
    from .waiting_manager import (
        waiting_context,
        EngineeringTermCategory,
        simulate_typing_effect
    )
    WAITING_MANAGER_AVAILABLE = True
except ImportError:
    WAITING_MANAGER_AVAILABLE = False
    print("Note: Waiting manager not available, using simple progress indicators")

# API地址 - 连接到线上服务
API_BASE_URL = "https://wtfe.aozai.top"
API_V1_PREFIX = "/api/v1"


class WTFEOnlineClient:
    """WTFE 在线服务客户端"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.api_key = None
        self.access_token = None

        # 尝试从配置文件加载认证信息
        self._load_auth_from_config()

    def _load_auth_from_config(self):
        """从配置文件加载认证信息"""
        try:
            import yaml
            from pathlib import Path

            api_config_path = Path(__file__).parent.parent / 'wtfe_api_config.yaml'
            if api_config_path.exists():
                with open(api_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}

                    # 加载API密钥
                    api_key = config.get('wtfe_api_key')
                    if api_key:
                        self.api_key = api_key
                        print(f"✓ 从配置文件加载API密钥")

                    # 加载访问令牌
                    access_token = config.get('wtfe_api_token')
                    if access_token:
                        self.access_token = access_token
                        print(f"✓ 从配置文件加载访问令牌")

                    # 更新API URL（如果配置文件中有）
                    api_url = config.get('wtfe_api_url')
                    if api_url and api_url != self.base_url:
                        self.base_url = api_url
                        print(f"✓ 使用配置文件中的API URL: {api_url}")
        except Exception as e:
            # 静默失败，不影响正常使用
            pass

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Send HTTP request"""
        url = f"{self.base_url}{endpoint}"

        # Add authentication headers
        headers = kwargs.get('headers', {})
        if self.access_token:
            headers['Authorization'] = f"Bearer {self.access_token}"
        elif self.api_key:
            headers['X-API-Key'] = self.api_key

        kwargs['headers'] = headers

        # Add SSL verification options (for self-signed certificates or SSL issues)
        if 'verify' not in kwargs:
            # Disable SSL verification by default to resolve certificate issues
            kwargs['verify'] = False
            # Add warning suppression
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        try:
            # Show waiting indicator for API requests
            if WAITING_MANAGER_AVAILABLE and method in ['POST', 'PUT', 'PATCH']:
                with waiting_context("API Processing", category=EngineeringTermCategory.PROCESSING) as manager:
                    response = self.session.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
            else:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            if WAITING_MANAGER_AVAILABLE:
                simulate_typing_effect(f"Request failed: {e}")
            else:
                print(f"Request failed: {e}")

            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if WAITING_MANAGER_AVAILABLE:
                        simulate_typing_effect(f"Error details: {error_data}")
                    else:
                        print(f"Error details: {error_data}")
                except:
                    if WAITING_MANAGER_AVAILABLE:
                        simulate_typing_effect(f"Response content: {e.response.text}")
                    else:
                        print(f"Response content: {e.response.text}")
            sys.exit(1)

    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register new user"""
        if WAITING_MANAGER_AVAILABLE:
            simulate_typing_effect(f"Registering user: {username} ({email})")
        else:
            print(f"Registering user: {username} ({email})")

        data = {
            "username": username,
            "email": email,
            "password": password
        }

        result = self._make_request("POST", f"{API_V1_PREFIX}/auth/register", json=data)

        if WAITING_MANAGER_AVAILABLE:
            simulate_typing_effect(f"✓ Registration successful! User ID: {result.get('id')}")
            simulate_typing_effect(f"  Please check your email {email} for verification link")
        else:
            print(f"✓ Registration successful! User ID: {result.get('id')}")
            print(f"  Please check your email {email} for verification link")
        return result

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """User login"""
        if WAITING_MANAGER_AVAILABLE:
            simulate_typing_effect(f"Logging in: {username}")
        else:
            print(f"Logging in: {username}")

        # Use OAuth2 form format
        data = {
            "username": username,
            "password": password
        }

        # Use form data instead of JSON
        result = self._make_request("POST", f"{API_V1_PREFIX}/auth/login", data=data)

        self.access_token = result.get("access_token")
        if WAITING_MANAGER_AVAILABLE:
            simulate_typing_effect(f"✓ Login successful!")
        else:
            print(f"✓ Login successful!")

        # Save access token to config file
        if self.access_token:
            try:
                import yaml
                from pathlib import Path

                api_config_path = Path(__file__).parent.parent / 'wtfe_api_config.yaml'
                config_data = {
                    'wtfe_api_token': self.access_token,
                    'wtfe_api_username': username,
                    'wtfe_api_url': API_BASE_URL
                }

                # Read existing config (if any)
                try:
                    with open(api_config_path, 'r', encoding='utf-8') as f:
                        existing_config = yaml.safe_load(f) or {}
                        config_data.update(existing_config)
                except:
                    pass

                with open(api_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, allow_unicode=True)
                if WAITING_MANAGER_AVAILABLE:
                    simulate_typing_effect(f"✓ Login information saved to {api_config_path}")
                else:
                    print(f"✓ Login information saved to {api_config_path}")
            except Exception as e:
                if WAITING_MANAGER_AVAILABLE:
                    simulate_typing_effect(f"Warning: Unable to save login information: {e}")
                else:
                    print(f"Warning: Unable to save login information: {e}")

        return result

    def resend_verification_email(self, email: str) -> Dict[str, Any]:
        """Resend verification email"""
        if WAITING_MANAGER_AVAILABLE:
            simulate_typing_effect(f"Resending verification email to: {email}")
        else:
            print(f"Resending verification email to: {email}")

        data = {
            "email": email
        }

        result = self._make_request("POST", f"{API_V1_PREFIX}/auth/resend-verification", json=data)

        if result.get("success"):
            if WAITING_MANAGER_AVAILABLE:
                simulate_typing_effect(f"✓ Verification email resent to: {email}")
            else:
                print(f"✓ Verification email resent to: {email}")
        else:
            if WAITING_MANAGER_AVAILABLE:
                simulate_typing_effect(f"✗ Failed to send verification email: {result.get('message', 'Unknown error')}")
            else:
                print(f"✗ Failed to send verification email: {result.get('message', 'Unknown error')}")

        return result

    def create_api_key(self, name: str = "default") -> Dict[str, Any]:
        """Create API key"""
        if not self.access_token:
            if WAITING_MANAGER_AVAILABLE:
                simulate_typing_effect("Error: Please login first")
            else:
                print("Error: Please login first")
            sys.exit(1)

        if WAITING_MANAGER_AVAILABLE:
            simulate_typing_effect(f"Creating API key: {name}")
        else:
            print(f"Creating API key: {name}")

        data = {
            "name": name
        }

        result = self._make_request("POST", f"{API_V1_PREFIX}/api-keys", json=data)

        api_key = result.get("api_key")
        if api_key:
            if WAITING_MANAGER_AVAILABLE:
                simulate_typing_effect(f"✓ API key created successfully!")
                simulate_typing_effect(f"  API key: {api_key}")
                simulate_typing_effect(f"  Warning: This key will only be shown once, please save it securely")
            else:
                print(f"✓ API key created successfully!")
                print(f"  API key: {api_key}")
                print(f"  Warning: This key will only be shown once, please save it securely")
            self.api_key = api_key

            # Save API key to config file
            try:
                import yaml
                from pathlib import Path
                import time

                api_config_path = Path(__file__).parent.parent / 'wtfe_api_config.yaml'
                config_data = {
                    'wtfe_api_key': api_key,
                    'wtfe_api_key_name': name,
                    'wtfe_api_key_created': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'wtfe_api_url': API_BASE_URL
                }

                # Read existing config (if any)
                try:
                    with open(api_config_path, 'r', encoding='utf-8') as f:
                        existing_config = yaml.safe_load(f) or {}
                        config_data.update(existing_config)
                except:
                    pass

                with open(api_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, allow_unicode=True)
                if WAITING_MANAGER_AVAILABLE:
                    simulate_typing_effect(f"✓ API key saved to {api_config_path}")
                else:
                    print(f"✓ API key saved to {api_config_path}")
            except Exception as e:
                if WAITING_MANAGER_AVAILABLE:
                    simulate_typing_effect(f"Warning: Unable to save API key: {e}")
                else:
                    print(f"Warning: Unable to save API key: {e}")
        else:
            if WAITING_MANAGER_AVAILABLE:
                simulate_typing_effect("✗ Failed to get API key")
            else:
                print("✗ Failed to get API key")

        return result

    def get_user_info(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        if not self.access_token:
            print("错误：请先登录")
            sys.exit(1)

        print("正在获取用户信息...")

        result = self._make_request("GET", f"{API_V1_PREFIX}/auth/me")

        # API直接返回用户对象，而不是包含"user"字段的对象
        user = result
        print(f"✓ 用户信息:")
        print(f"  用户名: {user.get('username')}")
        print(f"  邮箱: {user.get('email')}")
        print(f"  邮箱已验证: {user.get('is_verified')}")  # 注意字段名是is_verified，不是email_verified
        print(f"  创建时间: {user.get('created_at')}")

        return result

    def _safe_delete_file(self, file_path: str, max_retries: int = 3) -> None:
        """安全删除文件，支持重试机制

        Args:
            file_path: 文件路径
            max_retries: 最大重试次数
        """
        if not file_path or not os.path.exists(file_path):
            return

        for attempt in range(max_retries):
            try:
                # 在Windows上，可能需要先关闭所有句柄
                if os.name == 'nt':  # Windows系统
                    import time
                    # 等待一小段时间让系统释放文件句柄
                    time.sleep(0.1 * (attempt + 1))

                os.unlink(file_path)
                return  # 删除成功
            except PermissionError as e:
                if attempt < max_retries - 1:
                    # 等待后重试
                    import time
                    time.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    print(f"警告：无法删除临时文件 {file_path} (权限错误): {e}")
                    return
            except Exception as e:
                print(f"警告：无法删除临时文件 {file_path}: {e}")
                return

    def set_api_key(self, api_key: str) -> None:
        """设置API密钥（用于在线模式）"""
        self.api_key = api_key
        print(f"✓ API密钥已设置")

    def clear_auth(self) -> None:
        """清除认证信息"""
        self.api_key = None
        self.access_token = None
        print("✓ 认证信息已清除")

    def analyze_project(self, project_path: str, detail: bool = False) -> Dict[str, Any]:
        """
        Analyze project

        Args:
            project_path: Project path
            detail: Whether to enable detailed analysis mode

        Returns:
            Analysis result
        """
        if WAITING_MANAGER_AVAILABLE:
            simulate_typing_effect(f"Analyzing project: {project_path}")
            if detail:
                simulate_typing_effect("Detailed analysis mode enabled")
        else:
            print(f"Analyzing project: {project_path}")
            if detail:
                print("Detailed analysis mode enabled")

        # Check if file or directory exists
        from pathlib import Path
        path_obj = Path(project_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {project_path}")

        # If it's a directory, need to compress to tar.gz
        if path_obj.is_dir():
            import tempfile
            import tarfile
            import os

            if WAITING_MANAGER_AVAILABLE:
                # Use waiting context for compression
                with waiting_context("Compressing", category=EngineeringTermCategory.COMPRESSING) as manager:
                    # Create temporary file in dedicated wtfe subdirectory
                    temp_dir = tempfile.gettempdir()
                    wtfe_temp_dir = os.path.join(temp_dir, "wtfe")

                    # Ensure wtfe subdirectory exists
                    os.makedirs(wtfe_temp_dir, exist_ok=True)

                    temp_filename = f"project_{os.urandom(8).hex()}.tar.gz"
                    tar_path = os.path.join(wtfe_temp_dir, temp_filename)

                    try:
                        # Create tar.gz file
                        manager.update("Creating archive...")
                        with tarfile.open(tar_path, 'w:gz') as tar:
                            tar.add(project_path, arcname=os.path.basename(project_path))

                        manager.update("Archive created")

                        # Upload file - use with statement to ensure file handle is properly closed
                        result = None
                        with open(tar_path, 'rb') as f:
                            files = {'zip_file': (f'{os.path.basename(project_path)}.tar.gz', f, 'application/gzip')}

                            # Build request parameters
                            params = {}
                            if detail:
                                params['detail'] = 'true'

                            # Switch to uploading context
                            manager.update("Preparing upload...")

                        # Upload with separate waiting context
                        with waiting_context("Uploading", category=EngineeringTermCategory.UPLOADING) as upload_manager:
                            with open(tar_path, 'rb') as f:
                                files = {'zip_file': (f'{os.path.basename(project_path)}.tar.gz', f, 'application/gzip')}
                                result = self._make_request(
                                    "POST",
                                    f"{API_V1_PREFIX}/analyze-and-generate",
                                    files=files,
                                    params=params
                                )

                        return result
                    finally:
                        # Clean up temporary file - use retry mechanism to ensure file deletion
                        self._safe_delete_file(tar_path)
            else:
                # Fallback without waiting manager
                print("Detected directory, compressing...")

                # Create temporary file in dedicated wtfe subdirectory
                temp_dir = tempfile.gettempdir()
                wtfe_temp_dir = os.path.join(temp_dir, "wtfe")

                # Ensure wtfe subdirectory exists
                os.makedirs(wtfe_temp_dir, exist_ok=True)

                temp_filename = f"project_{os.urandom(8).hex()}.tar.gz"
                tar_path = os.path.join(wtfe_temp_dir, temp_filename)

                try:
                    # Create tar.gz file
                    with tarfile.open(tar_path, 'w:gz') as tar:
                        tar.add(project_path, arcname=os.path.basename(project_path))

                    print(f"Created compressed file: {tar_path}")

                    # Upload file - use with statement to ensure file handle is properly closed
                    result = None
                    with open(tar_path, 'rb') as f:
                        files = {'zip_file': (f'{os.path.basename(project_path)}.tar.gz', f, 'application/gzip')}

                        # Build request parameters
                        params = {}
                        if detail:
                            params['detail'] = 'true'

                        result = self._make_request(
                            "POST",
                            f"{API_V1_PREFIX}/analyze-and-generate",
                            files=files,
                            params=params
                        )

                    return result
                finally:
                    # Clean up temporary file - use retry mechanism to ensure file deletion
                    self._safe_delete_file(tar_path)
        else:
            # If it's a file, upload directly
            if WAITING_MANAGER_AVAILABLE:
                with waiting_context("Uploading", category=EngineeringTermCategory.UPLOADING) as manager:
                    with open(project_path, 'rb') as f:
                        # Determine MIME type based on file extension
                        if project_path.endswith('.tar.gz') or project_path.endswith('.tgz'):
                            mime_type = 'application/gzip'
                        elif project_path.endswith('.zip'):
                            mime_type = 'application/zip'
                        else:
                            mime_type = 'application/octet-stream'

                        files = {'zip_file': (os.path.basename(project_path), f, mime_type)}

                        # Build request parameters
                        params = {}
                        if detail:
                            params['detail'] = 'true'

                        result = self._make_request(
                            "POST",
                            f"{API_V1_PREFIX}/analyze-and-generate",
                            files=files,
                            params=params
                        )

                    return result
            else:
                print(f"Uploading file: {project_path}")
                with open(project_path, 'rb') as f:
                    # Determine MIME type based on file extension
                    if project_path.endswith('.tar.gz') or project_path.endswith('.tgz'):
                        mime_type = 'application/gzip'
                    elif project_path.endswith('.zip'):
                        mime_type = 'application/zip'
                    else:
                        mime_type = 'application/octet-stream'

                    files = {'zip_file': (os.path.basename(project_path), f, mime_type)}

                    # Build request parameters
                    params = {}
                    if detail:
                        params['detail'] = 'true'

                    result = self._make_request(
                        "POST",
                        f"{API_V1_PREFIX}/analyze-and-generate",
                        files=files,
                        params=params
                    )

                return result


def interactive_register():
    """交互式注册"""
    print("\n=== WTFE API 用户注册 ===")
    username = input("用户名: ").strip()
    email = input("邮箱: ").strip()
    password = getpass("密码: ").strip()
    confirm_password = getpass("确认密码: ").strip()

    if password != confirm_password:
        print("错误：密码不匹配")
        sys.exit(1)

    client = WTFEOnlineClient()
    return client.register(username, email, password)


def interactive_login():
    """交互式登录"""
    print("\n=== WTFE API 用户登录 ===")
    username = input("用户名: ").strip()
    password = getpass("密码: ").strip()

    client = WTFEOnlineClient()
    return client.login(username, password)


def interactive_create_api_key():
    """交互式创建API密钥"""
    print("\n=== 创建API密钥 ===")
    name = input("密钥名称 (默认: default): ").strip() or "default"

    # 先登录
    login_result = interactive_login()
    if not login_result.get("access_token"):
        print("登录失败")
        sys.exit(1)

    # 使用登录后的客户端
    client = WTFEOnlineClient()
    client.access_token = login_result.get("access_token")

    return client.create_api_key(name)


def interactive_resend_verification():
    """交互式重新发送验证邮件"""
    print("\n=== 重新发送验证邮件 ===")
    email = input("邮箱地址: ").strip()

    client = WTFEOnlineClient()
    return client.resend_verification_email(email)


def interactive_analyze_project():
    """交互式分析项目"""
    print("\n=== WTFE 在线项目分析 ===")

    # 获取项目路径
    project_path = input("项目路径: ").strip()
    if not project_path:
        print("错误：项目路径不能为空")
        sys.exit(1)

    # 询问是否使用详细模式
    detail_input = input("启用详细分析模式？(y/N): ").strip().lower()
    detail = detail_input == 'y'

    # 创建客户端
    client = WTFEOnlineClient()

    # 检查是否有API密钥或访问令牌
    if not client.api_key and not client.access_token:
        print("\n需要认证信息")
        print("1. 使用API密钥")
        print("2. 使用用户名密码登录")
        choice = input("选择认证方式 (1/2): ").strip()

        if choice == '1':
            api_key = input("API密钥: ").strip()
            client.api_key = api_key
        elif choice == '2':
            # 先登录
            login_result = interactive_login()
            if login_result.get("access_token"):
                client.access_token = login_result.get("access_token")
            else:
                print("登录失败")
                sys.exit(1)
        else:
            print("无效选择")
            sys.exit(1)

    # 分析项目
    try:
        result = client.analyze_project(project_path, detail=detail)

        # 处理结果
        if result.get('success'):
            data = result.get('data', {})
            content = data.get('content', '')

            print("\n" + "="*60)
            print("分析完成！")
            print("="*60)

            # 显示README内容
            if content:
                print("\n生成的README内容:")
                print("-"*40)
                print(content[:500] + "..." if len(content) > 500 else content)
                print("-"*40)

                # 询问是否保存到文件
                save_input = input("\n保存README到文件？(y/N): ").strip().lower()
                if save_input == 'y':
                    save_path = input("保存路径 (默认: README.md): ").strip() or "README.md"
                    try:
                        with open(save_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"✓ README已保存到: {save_path}")
                    except Exception as e:
                        print(f"保存失败: {e}")
            else:
                print("警告：未生成README内容")

            # 显示元数据
            metadata = data.get('metadata', {})
            if metadata:
                print(f"\n项目: {metadata.get('project', {}).get('name', '未知')}")
                print(f"生成器: {metadata.get('generator', '未知')}")
                print(f"格式: {metadata.get('format', '未知')}")
                print(f"长度: {metadata.get('length', 0)} 字符")
                print(f"行数: {metadata.get('lines', 0)} 行")

        return result

    except Exception as e:
        print(f"分析失败: {e}")
        sys.exit(1)


def main():
    """命令行入口"""
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print("用法: python wtfe_online.py <命令>")
        print("\n可用命令:")
        print("  register            注册新用户")
        print("  login               用户登录")
        print("  resend-verification 重新发送验证邮件")
        print("  create-api-key      创建API密钥")
        print("  user-info           获取用户信息")
        print("  analyze             分析项目并生成README")
        print("\n分析命令示例:")
        print("  python wtfe_online.py analyze /path/to/project")
        print("  python wtfe_online.py analyze /path/to/project --detail")
        sys.exit(0 if sys.argv[1] in ['-h', '--help'] else 1)

    command = sys.argv[1]
    client = WTFEOnlineClient()

    if command == "register":
        interactive_register()
    elif command == "login":
        interactive_login()
    elif command == "resend-verification":
        interactive_resend_verification()
    elif command == "create-api-key":
        interactive_create_api_key()
    elif command == "user-info":
        # 检查是否有认证信息
        if not client.access_token:
            print("需要登录以获取用户信息")
            login_result = interactive_login()
            if login_result.get("access_token"):
                client.access_token = login_result.get("access_token")
            else:
                print("登录失败")
                sys.exit(1)

        client.get_user_info()
    elif command == "analyze":
        # 分析项目命令
        if len(sys.argv) < 3:
            print("错误：需要提供项目路径")
            print("用法: python wtfe_online.py analyze <项目路径> [--detail]")
            sys.exit(1)

        project_path = sys.argv[2]
        detail = "--detail" in sys.argv or "-d" in sys.argv

        # 检查是否有认证信息（客户端初始化时已尝试从配置文件加载）
        if not client.api_key and not client.access_token:
            print("\n需要认证信息")
            print("检测到以下认证方式:")
            print("1. 使用API密钥")
            print("2. 使用用户名密码登录")
            choice = input("选择认证方式 (1/2): ").strip()

            if choice == '1':
                api_key = input("API密钥: ").strip()
                client.api_key = api_key
            elif choice == '2':
                # 先登录
                print("\n=== 用户登录 ===")
                username = input("用户名: ").strip()
                from getpass import getpass
                password = getpass("密码: ").strip()
                login_result = client.login(username, password)
                if login_result.get("access_token"):
                    client.access_token = login_result.get("access_token")
                else:
                    print("登录失败")
                    sys.exit(1)
            else:
                print("无效选择")
                sys.exit(1)

        # 分析项目
        try:
            result = client.analyze_project(project_path, detail=detail)

            # 处理结果
            if result.get('success'):
                data = result.get('data', {})
                content = data.get('content', '')

                print("\n" + "="*60)
                print("分析完成！")
                print("="*60)

                # 显示README内容
                if content:
                    # 自动保存到项目目录下的README.md
                    from pathlib import Path
                    project_dir = Path(project_path)
                    if project_dir.is_file():
                        project_dir = project_dir.parent

                    readme_path = project_dir / "README.md"
                    try:
                        with open(readme_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"✓ README已保存到: {readme_path}")
                    except Exception as e:
                        print(f"保存失败: {e}")

                    # 显示部分内容
                    print(f"\n生成的README内容 (前500字符):")
                    print("-"*40)
                    print(content[:500] + "..." if len(content) > 500 else content)
                    print("-"*40)

                # 显示元数据
                metadata = data.get('metadata', {})
                if metadata:
                    print(f"\n项目: {metadata.get('project', {}).get('name', '未知')}")
                    print(f"生成器: {metadata.get('generator', '未知')}")
                    print(f"格式: {metadata.get('format', '未知')}")
                    print(f"长度: {metadata.get('length', 0)} 字符")
                    print(f"行数: {metadata.get('lines', 0)} 行")
            else:
                print(f"分析失败: {result.get('message', '未知错误')}")

        except Exception as e:
            print(f"分析失败: {e}")
            sys.exit(1)
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()