from typing import Dict, Any, List
import os
import sys
from distutils import dir_util
import subprocess
import json
import argparse
from pathlib import Path
from read_test_results import read_test_results
from coverage import Coverage
from coverage.data import CoverageData

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
    test_result = [{} for _ in range(len(temp_dirs))]
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
        dontRun = False
        if id != 0 or mode != 'base':
            # run only tests that cover the function
            for x in config['evaluations']:
                if x['id'] == id:
                    this = x
                    break
            cov = Coverage(data_file=str(here/'experiment'/config['name']/'.coverage'))
            cov.load()
            cov_data = cov.get_data()
            line = this['remove'][0]['start_line']
            file_parts = str(temp_dir/config["project_root"]/this['file']).split(f'temp{id}')
            if file_parts[1].startswith('-'):
                file_parts[1] = '/' + '/'.join(file_parts[1].split('/')[1:])
            file = (file_parts[0] + 'temp0' + file_parts[1]).replace(f'/{mode}/', '/base/')
            tests_per_line = cov_data.contexts_by_lineno(file)
            tests = []
            print(tests_per_line.keys())
            if line not in tests_per_line:
                print('No test covers this line.')
                dontRun = True
            else:
                dontRun = False
                for t in tests_per_line[line]:
                    print(f'####### {t}')
                    if ']' in t or '[' in t:
                        tmp = t[t.find('['):]
                        parts = tmp[0].split('.')
                    else:
                        tmp = ''
                        parts = t.split('.')
                    tests.append(f'{str(temp_dir/config["project_root"])}/{("/".join(parts[:-3]) + "/") if len(parts) > 3 else ""}{parts[-3]}.py::{parts[-2]}::{parts[-1]}{tmp}')
            pytest_command += tests
        else:
            pytest_command.append(str(temp_dir/config['project_root']/config['tests_path']))
        if not dontRun:
            try:
                if id == 0 and mode == 'base':
                    with open(str(here/'experiment'/config['name']/'.coveragerc'), 'w') as f:
                        f.write('[run]\n' f'source = {str(temp_dir/config["project_root"])}\n' f'data_file = {str(here/"experiment"/config["name"]/".coverage")}\n' 'dynamic_context = test_function')
                    test_res = subprocess.run(['coverage', 'run', f'--rcfile={str(here/"experiment"/config["name"]/".coveragerc")}', '-m', 'pytest'] + pytest_command, capture_output=True, timeout=600)
                    print(f'!!!!\n{test_res.stderr.decode("utf-8")}\n!!!!\n{test_res.stdout.decode("utf-8")}\n!!!!')
                else:
                    test_res = subprocess.run([executable, '-m', 'pytest'] + pytest_command, capture_output=True, timeout=600)
                if test_res.returncode != 0:
                    print(test_res.stderr.decode('utf-8'))
            except subprocess.TimeoutExpired:
                print('Timeout at 10 minutes: Tests take too long to run.')
                (temp_dir/'results.xml').unlink(missing_ok=True)
        uninstall_res = subprocess.run([executable, '-m', 'pip', 'uninstall', '-y', config['name']], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if (temp_dir/'results.xml').exists():
            temp_result = read_test_results(str(temp_dir/'results.xml'), id)
        else:
            temp_result = {}
        if len(temp_dirs) > 1:
            test_result[int(str(temp_dir).split(f'temp{id}-')[1].rstrip('/'))] = temp_result
        else:
            test_result[0] = temp_result
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