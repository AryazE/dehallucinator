import argparse
from pathlib import Path
import subprocess
import json

PROMPT_LIMIT = 1000

def run():
    here = Path(__file__).parent
    for config_file in [cf for cf in here.iterdir() if cf.is_file() and cf.suffix == '.json']:
        with open(here/config_file, 'r') as f:
            config = json.load(f)
        for i in config['evaluations']:
            project_root = here/'experiment'/config['name']/f'temp{i["id"]}'/config['project_root']
            with open(project_root/i["file"]) as f:
                code = f.read()
            prompt = code.split('<CURSOR>')[0][-PROMPT_LIMIT:]
            subprocess.run([
                'python', '-m', 'coder.main',
                '--mode', 'simple',
                '--project-root', str(project_root),
                '--prompt', prompt
            ])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, required=True)
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--prompt', type=str, required=True)
    args = parser.parse_args()
    run(args.name, args.id, args.prompt)