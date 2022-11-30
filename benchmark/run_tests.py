import sys
import shutil
import subprocess
import json
import argparse
import logging
from distutils import dir_util
from pathlib import Path

def run_tests(config, id):
    here = Path(__file__).resolve().parent
    temp_dir = here/'experiment'/config['name']/f'temp{id}'/config['project_root']
    dir_util.copy_tree(str(here/config['project_root']/'tests'), str(temp_dir/'tests'))
    shutil.copyfile(str(here/config['project_root']/'setup.py'), str(temp_dir/'setup.py'))
    install_res = subprocess.run([sys.executable, '-m', 'pip', 'install', str(temp_dir)], check=True, capture_output=True)
    print(install_res.stdout.decode('utf-8'))
    subprocess.run([sys.executable, '-c', f'import {config["name"]}'], check=True)
    pytest_command = [
        '--tb=no', 
        '-q', 
        '--report-log', 
        f"{here/'experiment'/config['name']/f'temp{id}'}/log.json"
    ]
    pytest_command.append(str(temp_dir/'tests'))
    test_res = subprocess.run([sys.executable, '-m', 'pytest'] + pytest_command, capture_output=True)
    print(test_res.stdout.decode('utf-8'))
    uninstall_res = subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', config['name']], check=True, capture_output=True)
    print(uninstall_res.stdout.decode('utf-8'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--id', type=int, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    run_tests(config, args.id)