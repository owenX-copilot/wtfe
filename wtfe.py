#!/usr/bin/env python3
import sys
import os
import subprocess
import json
import time
import threading
import yaml
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
    config_path = wtfe_root / 'wtfe-readme' / 'config.yaml'
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
    m = {'file':'wtfe-file/wtfe_file.py','folder':'wtfe-folder/wtfe_folder.py','run':'wtfe-run/wtfe_run.py',
         'context':'wtfe-context/wtfe_context.py','intent':'wtfe-intent/wtfe_intent.py',
         'analyze':'wtfe-analyze/wtfe_analyze.py','readme':'wtfe-readme/wtfe_readme.py'}
    if name not in m:
        print(f'Unknown module: {name}', file=sys.stderr)
        sys.exit(1)
    cmd = [sys.executable, str(wtfe_root/m[name])] + args
    sys.exit(subprocess.run(cmd).returncode)

def run_full(path):
    Colors.init_windows()
    wtfe_root = get_wtfe_root()
    if not check_api_key(): sys.exit(1)
    if not Path(path).exists():
        print(f'Error: {path} not found', file=sys.stderr)
        sys.exit(1)
    
    print(f'\n[WTFE] Analyzing: {path}\n')
    
    spinner = Spinner('Analyzing')
    spinner.start()
    r = subprocess.run([sys.executable, str(wtfe_root/'wtfe-analyze'/'wtfe_analyze.py'), path], capture_output=True, text=True)
    if r.returncode != 0:
        spinner.stop(f'{Colors.RED}Analysis failed{Colors.RESET}')
        print(r.stderr, file=sys.stderr)
        sys.exit(1)
    spinner.stop(f'{Colors.GREEN}Analysis done{Colors.RESET}')
    
    spinner = Spinner('Generating README')
    spinner.start()
    r2 = subprocess.run([sys.executable, str(wtfe_root/'wtfe-readme'/'wtfe_readme.py'), '-'], input=r.stdout, text=True, capture_output=True)
    if r2.returncode != 0:
        spinner.stop(f'{Colors.RED}Generation failed{Colors.RESET}')
        print(r2.stderr, file=sys.stderr)
        sys.exit(1)
    spinner.stop(f'{Colors.GREEN}README saved{Colors.RESET}')
    
    print(f'\n{Colors.GREEN}Done!{Colors.RESET} Check project folder for README.md\n')

def main():
    if len(sys.argv) < 2:
        print('Usage: python wtfe.py <project_path>')
        print('       python wtfe.py -m <module> <args>')
        print('Modules: analyze, readme, file, folder, run, context, intent')
        sys.exit(0)
    if sys.argv[1] in ['-m', '--module']:
        if len(sys.argv) < 3:
            print('Error: Missing module name', file=sys.stderr)
            sys.exit(1)
        run_module(sys.argv[2], sys.argv[3:])
    elif sys.argv[1] in ['-h', '--help']:
        print('Usage: python wtfe.py <project_path>')
        print('       python wtfe.py -m <module> <args>')
    else:
        run_full(sys.argv[1])

if __name__ == '__main__':
    main()
