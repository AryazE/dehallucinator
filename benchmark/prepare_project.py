import argparse
import copy
import json
from distutils import dir_util
import os
from pathlib import Path
import sys
import venv

CURSOR = '<CURSOR>'

def prepare(config, mode):
    global CURSOR

    here = Path(__file__).resolve().parent
    for i in config['evaluations']:
        dir_util.mkpath(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
        temp_dir = here/'experiment'/config['name']/mode/f'temp{i["id"]}'/config['project_root']
        dir_util.copy_tree(str(here/config['project_root']), str(temp_dir))
        dir_util.remove_tree(str(temp_dir/'tests'))
        # os.remove(str(temp_dir/'setup.py'))
        if len(i['file']) == 0:
            continue
        with open(temp_dir/i["file"]) as f:
            code = f.readlines()
        new_code = []
        for l in range(len(code)):
            temp = code[l]
            for j in i['remove']:
                if j['description'] == 'imports':
                    continue
                if j['start_line'] - 1 <= l <= j['end_line'] - 1:
                    if j['start_line'] == j['end_line']:
                        temp = code[l][:j['start_column'] - 1] + (CURSOR if j['description'] != 'imports' else '') + code[l][j['end_column'] - 1:]
                    else:
                        if l == j['start_line'] - 1:
                            temp = code[l][:j['start_column'] - 1] + (CURSOR if j['description'] != 'imports' else '')
                        elif l == j['end_line'] - 1:
                            temp = code[l][j['end_column'] - 1:]
                        else:
                            temp = None
            if temp:
                new_code.append(temp)
        with open(temp_dir/i["file"], 'w') as f:
            f.writelines(new_code)
    env_obj = venv.EnvBuilder(with_pip=True)
    env_obj.create(str(here/'experiment'/config['name']/mode/'venv'))
    context = env_obj.ensure_directories(str(here/'experiment'/config['name']/mode/'venv'))
    return context.executable

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    print(prepare(config, args.mode))