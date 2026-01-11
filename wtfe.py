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
    if len(sys.argv) < 2:
        print('Usage: python wtfe.py [--detail] <project_path>')
        print('       python wtfe.py -m <module> <args>')
        print('\nOptions:')
        print('  --detail, -d    Enable detailed analysis (includes entry file contents for AI)')
        print('\nModules: analyze, readme, file, folder, run, context, intent')
        sys.exit(0)
    
    detail = False
    path_arg = None
    auto_confirm = False
    
    if sys.argv[1] in ['-m', '--module']:
        if len(sys.argv) < 3:
            print('Error: Missing module name', file=sys.stderr)
            sys.exit(1)
        run_module(sys.argv[2], sys.argv[3:])
    elif sys.argv[1] in ['-h', '--help']:
        print('Usage: python wtfe.py [--detail] [-a|--auto-confirm] <project_path>')
        print('       python wtfe.py -m <module> <args>')
        print('\nOptions:')
        print('  --detail, -d    Enable detailed analysis (includes entry file contents for AI)')
        print('  -a, --auto-confirm   Automatically send analysis payload to AI (no prompt)')
        sys.exit(0)
    else:
        # Parse flags
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

if __name__ == '__main__':
    main()
