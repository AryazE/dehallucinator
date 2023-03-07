from typing import Dict, Any, Tuple
import sys
from distutils import dir_util
import subprocess
import json
import argparse
from pathlib import Path
from read_test_results import read_test_results

projects_with_special_setup = ['fastapi']

def project_specific(project: str, project_dir: str):
    if project == 'fastapi':
        return [['uvicorn[standard]'],
            ['-e', f'{project_dir}"[dev,doc,test]"']]


def run_tests(config: Dict[str, Any], id: int, mode: str, executable: str) -> Tuple[Dict[str, int], str]:
    here = Path(__file__).resolve().parent
    temp_dirs = list((here/'experiment'/config['name']/mode).glob(f'temp{id}-*/'))
    if len(temp_dirs) == 0:
        temp_dirs = [here/'experiment'/config['name']/mode/f'temp{id}']
    test_result = None
    best = -1
    # temp_dir = here/'experiment'/config['name']/mode/f'temp{id}'/config['project_root']
    for temp_dir in temp_dirs:
        dir_util.copy_tree(str(here/config['project_root']/config['tests_path']), str(temp_dir/config['project_root']/config['tests_path']))
        special = None
        if config['name'] in projects_with_special_setup:
            special = project_specific(config['name'], str(temp_dir/config['project_root']))
        if special and len(special) == 2:
            subprocess.run([executable, '-m', 'pip', 'install'] + special[0], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            special.pop(0)
        if (temp_dir/config['project_root']/'requirements.txt').exists():
            subprocess.run([executable, '-m', 'pip', 'install', '-r', str(temp_dir/config['project_root']/'requirements.txt')], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            if special:
                install_res = subprocess.run([executable, '-m', 'pip', 'install'] + special[0], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                install_res = subprocess.run([executable, '-m', 'pip', 'install', str(temp_dir/config['project_root'])], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            subprocess.run([executable, '-m', 'pip', 'install', '--pre', str(temp_dir/config['project_root'])], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pytest_command = [
            '--tb=no', 
            '-q', 
            '--junitxml', 
            str(temp_dir/'results.xml'),
        ]
        pytest_command.append(str(temp_dir/config['project_root']/config['tests_path']))
        try:
            test_res = subprocess.run([executable, '-m', 'pytest'] + pytest_command, capture_output=True, timeout=600)
        except subprocess.TimeoutExpired:
            print('Timeout at 10 minutes: Tests take too long to run.')
            (temp_dir/'results.xml').unlink(missing_ok=True)
        if test_res.returncode != 0:
            print(test_res.stderr.decode('utf-8'))
        uninstall_res = subprocess.run([executable, '-m', 'pip', 'uninstall', '-y', config['name']], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        temp_result = read_test_results(str(temp_dir/'results.xml'), id)
        if test_result is None or (test_result['failures'] > temp_result['failures'] and test_result['tests'] <= temp_result['tests']):
            test_result = temp_result
            best = str(temp_dir).split('-')[-1].replace('/', '')
    return test_result, best

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    print(run_tests(config, args.id, args.mode, sys.executable))