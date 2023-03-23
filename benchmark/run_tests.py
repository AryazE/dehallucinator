from typing import Dict, Any, List
import sys
from distutils import dir_util
import subprocess
import json
import argparse
from pathlib import Path
from read_test_results import read_test_results

def run_tests(config: Dict[str, Any], id: int, mode: str, executable: str) -> List[Dict]:
    here = Path(__file__).resolve().parent
    with open(here/'repo_list.txt') as f:
        content = f.read().splitlines()
    req = None
    for i in content:
        parts = i.strip().split(' ')
        if config['name'] == parts[0][19:-4].replace('/', '_'):
            if 'r' in parts[1]:
                req = parts[2]
                test = parts[3]
            else:
                test = parts[2]
            break
    temp_dirs = list((here/'experiment'/config['name']/mode).glob(f'temp{id}-*/'))
    if len(temp_dirs) == 0:
        temp_dirs = [here/'experiment'/config['name']/mode/f'temp{id}']
    test_result = []
    best = -1
    # temp_dir = here/'experiment'/config['name']/mode/f'temp{id}'/config['project_root']
    for temp_dir in temp_dirs:
        dir_util.copy_tree(str(here/config['project_root']/config['tests_path']), str(temp_dir/config['project_root']/config['tests_path']))
        
        if (temp_dir/config['project_root']/'requirements.txt').exists():
            res = subprocess.run([executable, '-m', 'pip', 'install', '-r', str(temp_dir/config['project_root']/'requirements.txt')], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # if res.returncode != 0:
            #     print(res.stderr.decode('utf-8'))
            # else:
            #     print(res.stdout.decode('utf-8'))
        elif req is not None:
            res = subprocess.run([executable, '-m', 'pip', 'install', '-r', str(temp_dir/config['project_root']/req)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # if res.returncode != 0:
            #     print(res.stderr.decode('utf-8'))
            # else:
            #     print(res.stdout.decode('utf-8'))
        try:
            install_res = subprocess.run([executable, '-m', 'pip', 'install', str(temp_dir/config['project_root'])], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # if install_res.returncode != 0:
            #     print(install_res.stderr.decode('utf-8'))
            # else:
            #     print(install_res.stdout.decode('utf-8'))
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
            if test_res.returncode != 0:
                print(test_res.stderr.decode('utf-8'))
        except subprocess.TimeoutExpired:
            print('Timeout at 10 minutes: Tests take too long to run.')
            (temp_dir/'results.xml').unlink(missing_ok=True)
        uninstall_res = subprocess.run([executable, '-m', 'pip', 'uninstall', '-y', config['name']], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        temp_result = read_test_results(str(temp_dir/'results.xml'), id)
        test_result.append(temp_result)
    return test_result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    print(run_tests(config, args.id, args.mode, sys.executable))