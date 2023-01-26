import sys
import shutil
import subprocess
import json
import argparse
# import logging
from distutils import dir_util
from pathlib import Path
import xml.etree.ElementTree as ET
from read_test_results import read_test_results

def run_tests(config, id, mode, executable):
    here = Path(__file__).resolve().parent
    temp_dir = here/'experiment'/config['name']/mode/f'temp{id}'/config['project_root']
    dir_util.copy_tree(str(here/config['project_root']/'tests'), str(temp_dir/'tests'))
    # shutil.copyfile(str(here/config['project_root']/'setup.py'), str(temp_dir/'setup.py'))
    if (temp_dir/'requirements.txt').exists():
        subprocess.run([executable, '-m', 'pip', 'install', '-r', str(temp_dir/'requirements.txt')], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        install_res = subprocess.run([executable, '-m', 'pip', 'install', str(temp_dir)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # logging.info(f"Installing {config['name']} in {temp_dir}: {install_res.returncode}")
    except subprocess.CalledProcessError as e:
        subprocess.run([executable, '-m', 'pip', 'install', '--pre', str(temp_dir)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pytest_command = [
        '--tb=no', 
        '-q', 
        '--junitxml', 
        f"{here/'experiment'/config['name']/mode/f'temp{id}'}/results.xml",
    ]
    pytest_command.append(str(temp_dir/config['tests_path']))
    test_res = subprocess.run([executable, '-m', 'pytest'] + pytest_command, capture_output=True)
    if test_res.returncode != 0:
        print(test_res.stderr.decode('utf-8'))
        # logging.error(test_res.stderr.decode('utf-8'))
        # logging.error(test_res.stdout.decode('utf-8'))
    uninstall_res = subprocess.run([executable, '-m', 'pip', 'uninstall', '-y', config['name']], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return read_test_results(str(here/'experiment'/config['name']/mode/f'temp{id}'/'results.xml'), id)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    print(run_tests(config, args.id, args.mode, sys.executable))