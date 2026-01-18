#!/usr/bin/env python3
"""
WTFE 在线服务模块

提供与WTFE API在线服务交互的功能。
这是一个可选模块，用户可以选择使用在线服务或本地分析。
"""

import sys
import os
import json
import requests
from typing import Optional, Dict, Any
from getpass import getpass

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
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"

        # 添加认证头
        headers = kwargs.get('headers', {})
        if self.access_token:
            headers['Authorization'] = f"Bearer {self.access_token}"
        elif self.api_key:
            headers['X-API-Key'] = self.api_key

        kwargs['headers'] = headers

        # 添加SSL验证选项（针对自签名证书或SSL问题）
        if 'verify' not in kwargs:
            # 默认禁用SSL验证以解决证书问题
            kwargs['verify'] = False
            # 添加警告抑制
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"错误详情: {error_data}")
                except:
                    print(f"响应内容: {e.response.text}")
            sys.exit(1)

    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """注册新用户"""
        print(f"正在注册用户: {username} ({email})")

        data = {
            "username": username,
            "email": email,
            "password": password
        }

        result = self._make_request("POST", f"{API_V1_PREFIX}/auth/register", json=data)

        print(f"✓ 注册成功！用户ID: {result.get('id')}")
        print(f"  请检查邮箱 {email} 中的验证邮件以激活账户")
        return result

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        print(f"正在登录: {username}")

        # 使用OAuth2表单格式
        data = {
            "username": username,
            "password": password
        }

        # 使用表单数据而不是JSON
        result = self._make_request("POST", f"{API_V1_PREFIX}/auth/login", data=data)

        self.access_token = result.get("access_token")
        print(f"✓ 登录成功！")

        # 保存访问令牌到配置文件
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

                # 读取现有配置（如果有）
                try:
                    with open(api_config_path, 'r', encoding='utf-8') as f:
                        existing_config = yaml.safe_load(f) or {}
                        config_data.update(existing_config)
                except:
                    pass

                with open(api_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, allow_unicode=True)
                print(f"✓ 登录信息已保存到 {api_config_path}")
            except Exception as e:
                print(f"警告：无法保存登录信息: {e}")

        return result

    def resend_verification_email(self, email: str) -> Dict[str, Any]:
        """重新发送验证邮件"""
        print(f"正在重新发送验证邮件到: {email}")

        data = {
            "email": email
        }

        result = self._make_request("POST", f"{API_V1_PREFIX}/auth/resend-verification", json=data)

        if result.get("success"):
            print(f"✓ 验证邮件已重新发送到: {email}")
        else:
            print(f"✗ 验证邮件发送失败: {result.get('message', '未知错误')}")

        return result

    def create_api_key(self, name: str = "default") -> Dict[str, Any]:
        """创建API密钥"""
        if not self.access_token:
            print("错误：请先登录")
            sys.exit(1)

        print(f"正在创建API密钥: {name}")

        data = {
            "name": name
        }

        result = self._make_request("POST", f"{API_V1_PREFIX}/api-keys", json=data)

        api_key = result.get("api_key")
        if api_key:
            print(f"✓ API密钥创建成功！")
            print(f"  API密钥: {api_key}")
            print(f"  警告：此密钥只会显示一次，请妥善保存")
            self.api_key = api_key

            # 保存API密钥到配置文件
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

                # 读取现有配置（如果有）
                try:
                    with open(api_config_path, 'r', encoding='utf-8') as f:
                        existing_config = yaml.safe_load(f) or {}
                        config_data.update(existing_config)
                except:
                    pass

                with open(api_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, allow_unicode=True)
                print(f"✓ API密钥已保存到 {api_config_path}")
            except Exception as e:
                print(f"警告：无法保存API密钥: {e}")
        else:
            print("✗ 未能获取API密钥")

        return result

    def get_user_info(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        if not self.access_token:
            print("错误：请先登录")
            sys.exit(1)

        print("正在获取用户信息...")

        result = self._make_request("GET", f"{API_V1_PREFIX}/auth/me")

        user = result.get("user", {})
        print(f"✓ 用户信息:")
        print(f"  用户名: {user.get('username')}")
        print(f"  邮箱: {user.get('email')}")
        print(f"  邮箱已验证: {user.get('email_verified')}")
        print(f"  创建时间: {user.get('created_at')}")

        return result

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
        分析项目

        Args:
            project_path: 项目路径
            detail: 是否启用详细分析模式

        Returns:
            分析结果
        """
        print(f"正在分析项目: {project_path}")
        if detail:
            print("详细分析模式已启用")

        # 检查文件或目录是否存在
        from pathlib import Path
        path_obj = Path(project_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"路径不存在: {project_path}")

        # 如果是目录，需要压缩成tar.gz
        if path_obj.is_dir():
            import tempfile
            import tarfile
            import os

            print("检测到目录，正在压缩...")

            # 创建临时tar.gz文件
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
                tar_path = tmp_file.name

                # 创建tar.gz
                with tarfile.open(tar_path, 'w:gz') as tar:
                    tar.add(project_path, arcname=os.path.basename(project_path))

                print(f"已创建压缩文件: {tar_path}")

                try:
                    # 上传文件
                    with open(tar_path, 'rb') as f:
                        files = {'zip_file': (f'{os.path.basename(project_path)}.tar.gz', f, 'application/gzip')}

                        # 构建请求参数
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
                    # 清理临时文件
                    os.unlink(tar_path)
        else:
            # 如果是文件，直接上传
            print(f"上传文件: {project_path}")
            with open(project_path, 'rb') as f:
                # 根据文件扩展名确定MIME类型
                if project_path.endswith('.tar.gz') or project_path.endswith('.tgz'):
                    mime_type = 'application/gzip'
                elif project_path.endswith('.zip'):
                    mime_type = 'application/zip'
                else:
                    mime_type = 'application/octet-stream'

                files = {'zip_file': (os.path.basename(project_path), f, mime_type)}

                # 构建请求参数
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