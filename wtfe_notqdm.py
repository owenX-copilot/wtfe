#!/usr/bin/env python3
"""
WTFE - Why The Folder Exists
Unified command-line interface

Usage:
    python wtfe.py <project_path>              # 分析项目并生成README
    python wtfe.py analyze <project_path>      # 仅分析，输出JSON
    python wtfe.py readme <analysis.json>      # 基于JSON生成README
"""
import sys
import os
import subprocess
from pathlib import Path


def get_wtfe_root():
    """获取WTFE项目根目录"""
    return Path(__file__).parent.resolve()


def run_analyze(project_path: str, output_json: bool = False):
    """运行项目分析"""
    wtfe_root = get_wtfe_root()
    analyze_script = wtfe_root / 'wtfe-analyze' / 'wtfe_analyze.py'
    
    cmd = [sys.executable, str(analyze_script), project_path]
    
    if output_json:
        # 输出到stdout供后续使用
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[WTFE] Analysis failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        return result.stdout
    else:
        # 直接显示进度（stderr）
        subprocess.run(cmd, stderr=sys.stderr, check=True, stdout=subprocess.PIPE, text=True)
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def run_readme(analysis_json: str):
    """运行README生成"""
    wtfe_root = get_wtfe_root()
    readme_script = wtfe_root / 'wtfe-readme' / 'wtfe_readme.py'
    
    # 通过stdin传递JSON
    cmd = [sys.executable, str(readme_script), '-']
    
    result = subprocess.run(
        cmd,
        input=analysis_json,
        text=True,
        stderr=sys.stderr,
        check=False
    )
    
    if result.returncode != 0:
        print(f"\n[WTFE] README generation failed (exit code {result.returncode})", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("WTFE - Why The Folder Exists")
        print("\nUsage:")
        print("  python wtfe.py <project_path>           # 分析并生成README")
        print("  python wtfe.py analyze <project_path>   # 仅分析（输出JSON）")
        print("  python wtfe.py readme <analysis.json>   # 基于JSON生成README")
        print("\nExamples:")
        print("  python wtfe.py ./my-project")
        print("  python wtfe.py analyze ./my-project > result.json")
        print("  python wtfe.py readme result.json")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # 检查API Key（生成README时需要）
    if command != 'analyze' and not os.environ.get('WTFE_API_KEY'):
        print("[WTFE] Warning: WTFE_API_KEY environment variable not set.", file=sys.stderr)
        print("[WTFE] README generation requires an API key.", file=sys.stderr)
        print("[WTFE] Set it with: export WTFE_API_KEY='your-key' (Linux/Mac)", file=sys.stderr)
        print("[WTFE]            or: $env:WTFE_API_KEY='your-key' (Windows)", file=sys.stderr)
    
    if command == 'analyze':
        # 仅分析模式
        if len(sys.argv) < 3:
            print("Error: Missing project path", file=sys.stderr)
            print("Usage: python wtfe.py analyze <project_path>", file=sys.stderr)
            sys.exit(1)
        
        project_path = sys.argv[2]
        analysis_json = run_analyze(project_path, output_json=True)
        print(analysis_json)  # 输出到stdout
    
    elif command == 'readme':
        # 仅生成README模式
        if len(sys.argv) < 3:
            print("Error: Missing analysis JSON file", file=sys.stderr)
            print("Usage: python wtfe.py readme <analysis.json>", file=sys.stderr)
            sys.exit(1)
        
        json_file = sys.argv[2]
        if not Path(json_file).exists():
            print(f"Error: File not found: {json_file}", file=sys.stderr)
            sys.exit(1)
        
        with open(json_file, 'r', encoding='utf-8') as f:
            analysis_json = f.read()
        
        run_readme(analysis_json)
    
    else:
        # 默认：完整流程（分析+生成）
        project_path = command
        
        if not Path(project_path).exists():
            print(f"Error: Path not found: {project_path}", file=sys.stderr)
            sys.exit(1)
        
        print(f"[WTFE] Analyzing project: {project_path}", file=sys.stderr)
        analysis_json = run_analyze(project_path, output_json=True)
        
        print(f"[WTFE] Generating README...", file=sys.stderr)
        run_readme(analysis_json)
        
        print(f"\n✅ Done! Check the project folder for README.md (or README_generated.md)", file=sys.stderr)


if __name__ == '__main__':
    main()
