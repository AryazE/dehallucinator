import argparse
from pathlib import Path
import logging
import subprocess
import json
from autoimport import fix_code
from coder.utils import clip_prompt

PROMPT_LIMIT = 500

def run_completion(config, id, mode):
    global PROMPT_LIMIT
    here = Path(__file__).parent
    project_root = here/'experiment'/config["name"]/f'temp{id}'/config['project_root']
    with open(project_root/config["evaluations"][id]["file"]) as f:
        code = f.read()
    splited_code = code.split('<CURSOR>')
    prompt = clip_prompt(splited_code[0], PROMPT_LIMIT)
    logging.debug(f'Running completion for {config["name"]} {id} with prompt: \n{prompt}')
    subprocess.run([
        'python', '-m', 'coder.main',
        '--mode', mode,
        '--project-root', str(project_root),
        '--output', str(project_root/f'completion.out'),
        '--prompt', prompt
    ], check=True)
    with open(project_root/f'completion.out') as f:
        completion = f.read()
    final_code = splited_code[0] + completion + splited_code[1]
    with open(project_root/config["evaluations"][id]["file"], 'w') as f:
        f.write(fix_code(final_code))
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    run_completion(config, args.id, args.mode)