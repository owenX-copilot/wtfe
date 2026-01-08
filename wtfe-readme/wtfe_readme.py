"""
WTFE README Generator - AI Layer
Converts project analysis data to human-readable README.
"""
import json
import sys
import os
import yaml
import time
from pathlib import Path
from typing import Dict, Any, Optional

from providers import OpenAIProvider, APIError
from templates.prompt import build_readme_prompt, build_minimal_prompt


class READMEGenerator:
    """README生成器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化生成器
        
        Args:
            config_path: 配置文件路径（默认为同目录下的config.yaml）
        """
        if config_path is None:
            config_path = Path(__file__).parent / 'config.yaml'
        
        self.config = self._load_config(config_path)
        self.provider = self._init_provider()
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """加载配置文件"""
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 处理环境变量
        api_key = config.get('api_key', '')
        if api_key.startswith('${') and api_key.endswith('}'):
            env_var = api_key[2:-1]
            api_key = os.environ.get(env_var)
            if not api_key:
                raise ValueError(f"Environment variable {env_var} not set. "
                               f"Please set it or update config.yaml with your API key.")
            config['api_key'] = api_key
        
        return config
    
    def _init_provider(self) -> OpenAIProvider:
        """初始化AI Provider"""
        provider_type = self.config.get('provider', 'openai')
        
        if provider_type != 'openai':
            raise ValueError(f"Unsupported provider: {provider_type}. Currently only 'openai' is supported.")
        
        return OpenAIProvider(
            api_key=self.config['api_key'],
            base_url=self.config['base_url'],
            model=self.config['model'],
            temperature=self.config.get('temperature', 0.7),
            max_tokens=self.config.get('max_tokens', 4096),
            top_p=self.config.get('top_p', 0.9),
            stream=self.config.get('stream', False),
            enable_thinking=self.config.get('enable_thinking', False),
            thinking_budget=self.config.get('thinking_budget', 4096),
            timeout=self.config.get('timeout', 60)
        )
    
    def generate(self, analysis_result: Dict[str, Any]) -> str:
        """
        生成README
        
        Args:
            analysis_result: wtfe-analyze输出的JSON
        
        Returns:
            生成的README内容（Markdown）
        """
        # 构建Prompt
        print("[WTFE] Building prompt...", file=sys.stderr)
        prompt = build_readme_prompt(analysis_result, self.config)
        
        # 调用AI生成
        print(f"[WTFE] Calling AI model: {self.config['model']}...", file=sys.stderr)
        retry_count = self.config.get('retry_count', 3)
        
        for attempt in range(retry_count):
            try:
                readme_content = self.provider.generate(prompt)
                print("[WTFE] Generation successful!", file=sys.stderr)
                return readme_content
            
            except APIError as e:
                print(f"[WTFE] API call failed (attempt {attempt + 1}/{retry_count}): {e}", file=sys.stderr)
                
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"[WTFE] Retrying in {wait_time} seconds...", file=sys.stderr)
                    time.sleep(wait_time)
                else:
                    print("[WTFE] All retry attempts failed.", file=sys.stderr)
                    raise
    
    def generate_and_save(self, analysis_result: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        生成README并保存到文件
        
        Args:
            analysis_result: wtfe-analyze输出的JSON
            output_path: 输出路径（默认使用config中的配置）
        
        Returns:
            保存的文件路径
        """
        # 生成README
        readme_content = self.generate(analysis_result)
        
        # 确定输出路径
        if output_path is None:
            project_path = analysis_result.get('metadata', {}).get('project_path', '.')
            output_filename = self.config.get('output_file', 'README.md')
            output_path = Path(project_path) / output_filename
        else:
            output_path = Path(output_path)
        
        # 检查是否覆盖
        if output_path.exists():
            if not self.config.get('overwrite', False):
                # 不覆盖，生成新文件名
                output_path = output_path.parent / 'README_generated.md'
                print(f"[WTFE] File exists, saving to: {output_path}", file=sys.stderr)
            elif self.config.get('backup_existing', True):
                # 覆盖前备份
                backup_path = Path(str(output_path) + '.bak')
                output_path.rename(backup_path)
                print(f"[WTFE] Backed up existing file to: {backup_path}", file=sys.stderr)
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"[WTFE] README saved to: {output_path}", file=sys.stderr)
        return str(output_path)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("Usage: python wtfe_readme.py <analysis_json_file_or_stdin>", file=sys.stderr)
        print("\nExamples:", file=sys.stderr)
        print("  python wtfe_readme.py analysis.json", file=sys.stderr)
        print("  python wtfe-analyze/wtfe_analyze.py . | python wtfe_readme.py -", file=sys.stderr)
        sys.exit(1)
    
    input_source = sys.argv[1]
    
    # 读取分析结果
    if input_source == '-':
        # 从stdin读取
        print("[WTFE] Reading analysis from stdin...", file=sys.stderr)
        analysis_data = sys.stdin.read()
    else:
        # 从文件读取
        print(f"[WTFE] Reading analysis from: {input_source}", file=sys.stderr)
        with open(input_source, 'r', encoding='utf-8') as f:
            analysis_data = f.read()
    
    try:
        analysis_result = json.loads(analysis_data)
    except json.JSONDecodeError as e:
        print(f"[WTFE] Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 初始化生成器
    try:
        generator = READMEGenerator()
    except Exception as e:
        print(f"[WTFE] Error initializing generator: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 生成README
    try:
        if len(sys.argv) >= 3 and sys.argv[2] == '--stdout':
            # 输出到stdout
            readme_content = generator.generate(analysis_result)
            print(readme_content)
        else:
            # 保存到文件
            output_path = generator.generate_and_save(analysis_result)
            print(f"\n✅ README generated successfully: {output_path}")
    
    except APIError as e:
        print(f"\n❌ API Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
