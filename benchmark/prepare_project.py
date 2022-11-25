import argparse
import json
from distutils import dir_util
import os
from pathlib import Path

CURSOR = '<CURSOR>'

def prepare(config):
    global CURSOR

    here = Path(__file__).parent
    for i in config['evaluations']:
        dir_util.mkpath(str(here/'experiment'/config['name']/f'temp{i["id"]}'))
        temp_dir = here/'experiment'/config['name']/f'temp{i["id"]}'/config['project_root']
        dir_util.copy_tree(str(here/config['project_root']), str(temp_dir))
        dir_util.remove_tree(str(temp_dir/'tests'))
        os.remove(str(temp_dir/'setup.py'))
        if len(i['file']) == 0:
            continue
        with open(temp_dir/i["file"]) as f:
            code = f.readlines()
        for j in i["remove"]:
            if j["start_line"] == j["end_line"]:
                code[j["start_line"] - 1] = code[j["start_line"] - 1][:j["start_column"] - 1] + (CURSOR if j['description'] != 'imports' else '') + code[j["start_line"] - 1][j["end_column"] - 1:]
            else:
                code[j["start_line"] - 1] = code[j["start_line"] - 1][:j["start_column"] - 1]
                code[j["end_line"] - 1] = code[j["end_line"] - 1][j["end_column"] - 1:]
                code = code[:j["start_line"]] + ([CURSOR] if j['description'] != 'imports' else []) + code[j["end_line"] - 1:]
        with open(temp_dir/i["file"], 'w') as f:
            f.writelines(code)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    prepare(config)