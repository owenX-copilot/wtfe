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

# API地址写死为127.0.0.1:9999
API_BASE_URL = "http://127.0.0.1:9999"
API_V1_PREFIX = "/api/v1"


class WTFEOnlineClient:
    """WTFE 在线服务客户端"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.api_key = None
        self.access_token = None

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
        # 需要先登录
        login_result = interactive_login()
        if login_result.get("access_token"):
            client.access_token = login_result.get("access_token")
            client.get_user_info()
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()