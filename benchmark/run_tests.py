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
    subprocess.run(['pip', 'install', str(temp_dir)], check=True, stdout=subprocess.DEVNULL)
    pytest_command = [
        '--tb=no', 
        '-q', 
        '--report-log', 
        f"{here/'experiment'/config['name']/f'temp{id}'}/log.json"
    ]
    pytest_command.append(str(temp_dir/'tests'))
    exit_code = subprocess.run(['pytest'] + pytest_command)
    logging.debug(f'Exit code: {exit_code}')
    subprocess.run(['pip', 'uninstall', '-y', config['name']], check=True, stdout=subprocess.DEVNULL)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--id', type=int, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    run_tests(config, args.id)