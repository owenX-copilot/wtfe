#!/usr/bin/env python3
import sys
import os
import subprocess
import json
import time
import threading
import yaml
import argparse
from pathlib import Path
from getpass import getpass

def get_wtfe_root():
    return Path(__file__).parent.resolve()

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    
    @staticmethod
    def init_windows():
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except: pass

class Spinner:
    def __init__(self, msg='Processing'):
        self.msg = msg
        self.running = False
        self.thread = None
        self.frames = ['|', '/', '-', '\\']
        self.i = 0
    
    def _spin(self):
        while self.running:
            sys.stderr.write(f'\r{self.frames[self.i % 4]} {self.msg}...')
            sys.stderr.flush()
            self.i += 1
            time.sleep(0.1)
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()
    
    def stop(self, final=None):
        self.running = False
        if self.thread: self.thread.join()
        sys.stderr.write('\r' + ' '*60 + '\r')
        if final: sys.stderr.write(final + '\n')
        sys.stderr.flush()

def check_api_key():
    if os.environ.get('WTFE_API_KEY'):
        return True
    wtfe_root = get_wtfe_root()
    config_path = wtfe_root / 'wtfe_readme' / 'config.yaml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
            key = cfg.get('api_key', '')
            # 忽略以$开头的变量引用，以及默认的占位符
            if key and not key.startswith('$') and 'your_api_key' not in key:
                os.environ['WTFE_API_KEY'] = key
                return True
    except: pass
    
    print('\n[WTFE] First-time setup')
    print('='*50)
    print('1. SiliconFlow (CN, cheap)')
    print('2. OpenAI')
    print('3. Ollama (local, no key)')
    print('='*50)
    c = input('Choose [1/2/3] (default 1): ').strip() or '1'
    
    if c == '3':
        data = {'provider':'openai','base_url':'http://localhost:11434/v1','api_key':'dummy','model':'llama3.1:8b'}
        print('Note: Run ollama pull llama3.1:8b first')
    else:
        key = getpass('Enter API Key: ').strip()
        if not key:
            print('Error: Key cannot be empty')
            return False
        if c == '2':
            data = {'provider':'openai','base_url':'https://api.openai.com/v1','api_key':key,'model':'gpt-4o-mini'}
        else:
            data = {'provider':'openai','base_url':'https://api.siliconflow.cn/v1','api_key':key,'model':'deepseek-ai/DeepSeek-V3.2'}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            full = yaml.safe_load(f)
        full.update(data)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(full, f, allow_unicode=True)
        os.environ['WTFE_API_KEY'] = data['api_key']
        print(f'Saved to {config_path}\n')
        return True
    except Exception as e:
        print(f'Error: {e}')
        return False

def run_module(name, args):
    wtfe_root = get_wtfe_root()
    m = {'file':'wtfe_file/wtfe_file.py','folder':'wtfe_folder/wtfe_folder.py','run':'wtfe_run/wtfe_run.py',
         'context':'wtfe_context/wtfe_context.py','intent':'wtfe_intent/wtfe_intent.py',
         'analyze':'wtfe_analyze/wtfe_analyze.py','readme':'wtfe_readme/wtfe_readme.py'}
    if name not in m:
        print(f'Unknown module: {name}', file=sys.stderr)
        sys.exit(1)
    cmd = [sys.executable, str(wtfe_root/m[name])] + args
    sys.exit(subprocess.run(cmd).returncode)

def handle_auth_command(args):
    """处理认证相关命令"""
    # 动态导入在线服务模块
    try:
        from wtfe_online.wtfe_online import WTFEOnlineClient
    except ImportError:
        print("错误：在线服务模块未找到")
        print("请确保 wtfe_online/wtfe_online.py 文件存在")
        sys.exit(1)

    client = WTFEOnlineClient()

    if args.auth_command == "register":
        print("\n=== WTFE API 用户注册 ===")
        username = input("用户名: ").strip()
        email = input("邮箱: ").strip()
        password = getpass("密码: ").strip()
        confirm_password = getpass("确认密码: ").strip()

        if password != confirm_password:
            print("错误：密码不匹配")
            sys.exit(1)

        client.register(username, email, password)

    elif args.auth_command == "login":
        print("\n=== WTFE API 用户登录 ===")
        username = input("用户名: ").strip()
        password = getpass("密码: ").strip()

        result = client.login(username, password)

        # 保存访问令牌到单独的文件
        if result.get("access_token"):
            wtfe_root = get_wtfe_root()
            api_config_path = wtfe_root / 'wtfe_api_config.yaml'
            try:
                config_data = {
                    'wtfe_api_token': result.get("access_token"),
                    'wtfe_api_username': username,
                    'wtfe_api_url': 'https://wtfe.aozai.top'
                }
                with open(api_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, allow_unicode=True)
                print(f"✓ 登录信息已保存到 {api_config_path}")
                print(f"  此文件独立于主配置文件，不会影响现有配置")
            except Exception as e:
                print(f"警告：无法保存登录信息: {e}")

    elif args.auth_command == "resend-verification":
        print("\n=== 重新发送验证邮件 ===")
        email = input("邮箱地址: ").strip()
        client.resend_verification_email(email)

    elif args.auth_command == "api-key":
        print("\n=== 创建API密钥 ===")
        name = input("密钥名称 (默认: default): ").strip() or "default"

        # 尝试从API配置文件获取访问令牌
        access_token = None
        wtfe_root = get_wtfe_root()
        api_config_path = wtfe_root / 'wtfe_api_config.yaml'
        try:
            with open(api_config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
                access_token = cfg.get('wtfe_api_token')
        except:
            pass

        if access_token:
            client.access_token = access_token
            result = client.create_api_key(name)

            # 保存API密钥到配置文件
            api_key = result.get("api_key")
            if api_key:
                try:
                    with open(api_config_path, 'r', encoding='utf-8') as f:
                        cfg = yaml.safe_load(f) or {}
                    # Save original API key (no truncation needed with SHA256 hashing)
                    cfg['wtfe_api_key'] = api_key
                    cfg['wtfe_api_key_name'] = name
                    cfg['wtfe_api_key_created'] = time.strftime("%Y-%m-%d %H:%M:%S")
                    with open(api_config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(cfg, f, allow_unicode=True)
                    print(f"✓ API密钥已保存到 {api_config_path}")
                except Exception as e:
                    print(f"警告：无法保存API密钥: {e}")
        else:
            print("错误：未找到登录信息，请先登录")
            print("使用方法：python wtfe.py auth login")
            sys.exit(1)

    elif args.auth_command == "user-info":
        # 尝试从API配置文件获取访问令牌
        access_token = None
        wtfe_root = get_wtfe_root()
        api_config_path = wtfe_root / 'wtfe_api_config.yaml'
        try:
            with open(api_config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
                access_token = cfg.get('wtfe_api_token')
        except:
            pass

        if access_token:
            client.access_token = access_token
            client.get_user_info()
        else:
            print("错误：未找到登录信息，请先登录")
            print("使用方法：python wtfe.py auth login")
            sys.exit(1)


def run_full(path, detail=False, auto_confirm=False):
    Colors.init_windows()
    wtfe_root = get_wtfe_root()
    if not check_api_key(): sys.exit(1)
    if not Path(path).exists():
        print(f'Error: {path} not found', file=sys.stderr)
        sys.exit(1)
    
    print(f'\n[WTFE] Analyzing: {path}\n')
    if detail:
        print(f'{Colors.YELLOW}[Detail Mode] Entry file contents will be included for better accuracy{Colors.RESET}\n', file=sys.stderr)
    
    spinner = Spinner('Analyzing')
    spinner.start()
    cmd = [sys.executable, str(wtfe_root/'wtfe_analyze'/'wtfe_analyze.py'), path]
    if detail:
        cmd.append('--detail')
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        spinner.stop(f'{Colors.RED}Analysis failed{Colors.RESET}')
        print(r.stderr, file=sys.stderr)
        sys.exit(1)
    spinner.stop(f'{Colors.GREEN}Analysis done{Colors.RESET}')
    
    # Save analysis payload to file so user can review (privacy safeguard)
    project_root = Path(path)
    pending_path = project_root / '.wtfe_pending_analysis.json'
    try:
        with pending_path.open('w', encoding='utf-8') as pf:
            pf.write(r.stdout)
        print(f"[WTFE] Analysis payload written to: {pending_path}")
    except Exception as e:
        print(f"[WTFE] Warning: Failed to write analysis payload to {pending_path}: {e}")

    # Parse analysis JSON to extract log
    analysis_log = {}
    try:
        analysis_json = json.loads(r.stdout)
        analysis_log = analysis_json.get('analysis_log', {})
    except:
        pass

    # Ask for user confirmation before sending to AI unless auto_confirm is True
    if not auto_confirm:
        print('\nPlease review the analysis payload at:', pending_path)
        try:
            yn = input('Send analysis to AI for README generation? [y/N]: ').strip().lower()
        except EOFError:
            yn = 'n'
        if yn != 'y':
            print('[WTFE] Aborted by user. Analysis payload saved; README generation skipped.')
            # still print summary
            print(f'\n{Colors.BOLD}[WTFE] Analysis Summary{Colors.RESET}')
            print('=' * 60)
            print(f'Mode: {Colors.CYAN}{analysis_log.get("mode", "unknown").upper()}{Colors.RESET}')
            print(f'Modules executed: {", ".join(analysis_log.get("modules", {}).keys())}')
            print('=' * 60 + '\n')
            return

    # Read the payload from file (ensures user's reviewed content is sent)
    try:
        payload = pending_path.read_text(encoding='utf-8')
    except Exception:
        payload = r.stdout

    spinner = Spinner('Generating README')
    spinner.start()
    r2 = subprocess.run([sys.executable, str(wtfe_root/'wtfe_readme'/'wtfe_readme.py'), '-'], input=payload, text=True, capture_output=True)
    if r2.returncode != 0:
        spinner.stop(f'{Colors.RED}Generation failed{Colors.RESET}')
        print(r2.stderr, file=sys.stderr)
        sys.exit(1)
    spinner.stop(f'{Colors.GREEN}README saved{Colors.RESET}')
    
    # Print analysis summary log
    print(f'\n{Colors.BOLD}[WTFE] Analysis Summary{Colors.RESET}')
    print('=' * 60)
    print(f'Mode: {Colors.CYAN}{analysis_log.get("mode", "unknown").upper()}{Colors.RESET}')
    print(f'Modules executed: {", ".join(analysis_log.get("modules", {}).keys())}')
    
    # Detail mode specific log
    if detail and 'entry_details' in analysis_log:
        entry_log = analysis_log['entry_details']
        if isinstance(entry_log, dict):
            print(f'\n{Colors.BOLD}Detail Mode Statistics:{Colors.RESET}')
            print(f'  • Files processed: {entry_log.get("files_processed", 0)}')
            print(f'  • Full content sent: {entry_log.get("files_full_content", 0)} files')
            print(f'  • Downgraded to snippet: {entry_log.get("files_downgraded", 0)} files')
            print(f'  • Total tokens: {entry_log.get("total_tokens", 0)}')
            if entry_log.get('files_details'):
                print(f'\n  File details:')
                for fd in entry_log['files_details']:
                    mode_color = Colors.GREEN if fd.get('mode') == 'full' else Colors.YELLOW
                    print(f'    - {fd["file"]}: {mode_color}{fd.get("mode", "unknown").upper()}{Colors.RESET} ({fd.get("tokens", 0)} tokens)')
    
    print('=' * 60 + '\n')

def main():
    global sys
    parser = argparse.ArgumentParser(description='WTFE - Why The Folder Exists')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 分析命令
    analyze_parser = subparsers.add_parser('analyze', help='分析项目并生成README')
    analyze_parser.add_argument('path', help='项目路径')
    analyze_parser.add_argument('--detail', '-d', action='store_true', help='启用详细分析模式')
    analyze_parser.add_argument('--auto-confirm', '-a', action='store_true', help='自动确认发送分析到AI')

    # 模块命令
    module_parser = subparsers.add_parser('module', help='运行特定模块')
    module_parser.add_argument('module_name', help='模块名称: analyze, readme, file, folder, run, context, intent')
    module_parser.add_argument('args', nargs=argparse.REMAINDER, help='模块参数')

    # 认证命令
    auth_parser = subparsers.add_parser('auth', help='用户认证和API密钥管理')
    auth_parser.add_argument('auth_command', choices=['register', 'login', 'resend-verification', 'api-key', 'user-info'],
                           help='认证命令: register(注册), login(登录), resend-verification(重新发送验证邮件), api-key(创建API密钥), user-info(用户信息)')

    # 在线模式命令
    online_parser = subparsers.add_parser('online', help='使用在线服务分析项目')
    online_parser.add_argument('path', help='项目路径')
    online_parser.add_argument('--detail', '-d', action='store_true', help='启用详细分析模式')
    online_parser.add_argument('--auto-confirm', '-a', action='store_true', help='自动确认发送分析到AI')
    online_parser.add_argument('--api-key', help='API密钥（可选，从配置文件读取）')

    # 向后兼容的旧版参数解析
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    # 检查是否是旧版参数格式
    if sys.argv[1] in ['-m', '--module']:
        # 旧版模块命令
        if len(sys.argv) < 3:
            print('Error: Missing module name', file=sys.stderr)
            sys.exit(1)
        run_module(sys.argv[2], sys.argv[3:])
    elif sys.argv[1] in ['-h', '--help']:
        # 旧版帮助
        print('Usage: python wtfe.py [--detail] [-a|--auto-confirm] <project_path>')
        print('       python wtfe.py -m <module> <args>')
        print('\nOptions:')
        print('  --detail, -d    Enable detailed analysis (includes entry file contents for AI)')
        print('  -a, --auto-confirm   Automatically send analysis payload to AI (no prompt)')
        print('\n新命令格式:')
        print('  python wtfe.py analyze <path> [--detail] [--auto-confirm]')
        print('  python wtfe.py auth <command> (register|login|resend-verification|api-key|user-info)')
        print('  python wtfe.py online <path> [--detail] [--auto-confirm] [--api-key]')
        sys.exit(0)
    elif not sys.argv[1].startswith('-') and len(sys.argv) >= 2:
        # 检查是否是新版命令
        if sys.argv[1] in ['auth', 'analyze', 'module', 'online']:
            # 使用新版参数解析
            args = parser.parse_args()

            if args.command == 'analyze':
                run_full(args.path, detail=args.detail, auto_confirm=args.auto_confirm)
            elif args.command == 'module':
                run_module(args.module_name, args.args)
            elif args.command == 'auth':
                handle_auth_command(args)
            elif args.command == 'online':
                # 在线模式 - 调用wtfe_online.py analyze命令
                import subprocess

                # 构建命令参数
                cmd = [sys.executable, str(get_wtfe_root() / 'wtfe_online' / 'wtfe_online.py'), 'analyze', args.path]

                if args.detail:
                    cmd.append('--detail')
                if args.api_key:
                    # 暂时不支持直接传递API密钥，需要用户交互输入
                    print("注意：API密钥需要通过交互方式输入")
                    print("运行命令后，系统会提示输入API密钥")

                # 执行命令
                try:
                    subprocess.run(cmd, check=True)
                except subprocess.CalledProcessError as e:
                    sys.exit(e.returncode)
                except FileNotFoundError:
                    print("错误：wtfe_online模块未找到")
                    print("请确保wtfe_online/wtfe_online.py文件存在")
                    sys.exit(1)
            else:
                parser.print_help()
        else:
            # 旧版分析命令
            detail = False
            path_arg = None
            auto_confirm = False

            args = sys.argv[1:]
            for arg in args:
                if arg in ['--detail', '-d']:
                    detail = True
                elif arg in ['-a', '--auto-confirm']:
                    auto_confirm = True
                elif not arg.startswith('-'):
                    path_arg = arg

            if not path_arg:
                print('Error: Missing project path', file=sys.stderr)
                sys.exit(1)

            run_full(path_arg, detail=detail, auto_confirm=auto_confirm)
    else:
        # 新版参数解析
        args = parser.parse_args()

        if args.command == 'analyze':
            run_full(args.path, detail=args.detail, auto_confirm=args.auto_confirm)
        elif args.command == 'module':
            run_module(args.module_name, args.args)
        elif args.command == 'auth':
            handle_auth_command(args)
        elif args.command == 'online':
            # 在线模式 - 调用wtfe_online.py analyze命令
            import subprocess
            import sys

            # 构建命令参数
            cmd = [sys.executable, str(get_wtfe_root() / 'wtfe_online' / 'wtfe_online.py'), 'analyze', args.path]

            if args.detail:
                cmd.append('--detail')
            if args.api_key:
                # 暂时不支持直接传递API密钥，需要用户交互输入
                print("注意：API密钥需要通过交互方式输入")
                print("运行命令后，系统会提示输入API密钥")

            # 执行命令
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)
            except FileNotFoundError:
                print("错误：wtfe_online模块未找到")
                print("请确保wtfe_online/wtfe_online.py文件存在")
                sys.exit(1)
        else:
            parser.print_help()

if __name__ == '__main__':
    main()
