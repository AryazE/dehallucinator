import os
import shutil
import subprocess
import json
import argparse
import pytest
from distutils import dir_util
from pathlib import Path

def run_tests(config, id):
    here = Path(__file__).parent
    dir_util.mkpath(str(here/'experiment'/config['name']/f'temp{id}'))
    temp_dir = here/'experiment'/config['name']/f'temp{id}'/config['project_root']
    dir_util.copy_tree(str(here/config['project_root']/'tests'), str(temp_dir/'tests'))
    shutil.copyfile(str(here/config['project_root']/'setup.py'), str(temp_dir/'setup.py'))
    subprocess.run(['pip', 'install', str(temp_dir)], check=True)
    pytest.main([str(temp_dir/'tests')])
    subprocess.run(['pip', 'uninstall', '-y', config['name']], check=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--id', type=int, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    run_tests(config, args.id)