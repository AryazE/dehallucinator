import argparse
import json
from distutils import dir_util
from pathlib import Path

CURSOR = '<CURSOR>'

def prepare(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)

    here = Path(__file__).parent
    for i in config['evaluations']:
        temp_dir = Path(dir_util.mkpath(here/'experiment'/config['name']/f'temp{i["id"]}'))
        dir_util.copy_tree(here/config['project_root'], temp_dir)
        with open(temp_dir/i["file"]) as f:
            code = f.readlines()
        for j in i["remove"]:
            if j["start_line"] == j["end_line"]:
                code[j["start_line"] - 1] = code[j["start_line"] - 1][:j["start_column"] - 1] + CURSOR + code[j["start_line"] - 1][j["end_column"] - 1:]
            else:
                code[j["start_line"] - 1] = code[j["start_line"] - 1][:j["start_column"] - 1]
                code[j["end_line"] - 1] = code[j["end_line"] - 1][j["end_column"] - 1:]
                code = code[:j["start_line"]] + [CURSOR] + code[j["end_line"] - 1:]
        with open(temp_dir/i["file"], 'w') as f:
            f.writelines(code)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, required=True)
    args = parser.parse_args()
    prepare(args.input)