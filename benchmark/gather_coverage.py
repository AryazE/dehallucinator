import subprocess
from pathlib import Path
import shutil
import argparse
import sys


if __name__ == "__main__":
    here = Path(__file__).parent.resolve()
    with open(str(here/"repo_list.txt"), "r") as f:
        lines = f.read().splitlines()
    for line in lines[41:]:
        parts = line.split(' ')
        url = parts[0]
        owner = url.split('/')[-2]
        repo = url.split('/')[-1][:-4]
        tests = parts[-1]
        req = parts[2]

        project_root = f"GitHubProjects/{owner}_{repo}"
        name = f"{owner}_{repo}"
        print(name)
        shutil.copytree(str(here/project_root), str(here/"temp_conf"/name))
        if req is not None:
            res = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(here/"temp_conf"/name/req)], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode != 0:
                print(res.stderr.decode('utf-8'))
            else:
                print(res.stdout.decode('utf-8'))
        if (here/"temp_conf"/name/'requirements.txt').exists():
            res = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(here/"temp_conf"/name/'requirements.txt')], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode != 0:
                print(res.stderr.decode('utf-8'))
            else:
                print(res.stdout.decode('utf-8'))
        try:
            install_res = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', str(here/"temp_conf"/name)], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if install_res.returncode != 0:
                print(install_res.stderr.decode('utf-8'))
            else:
                print(install_res.stdout.decode('utf-8'))
        except subprocess.CalledProcessError as e:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--pre', '-e', str(here/"temp_conf"/name)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(str(here/'temp_conf'/name/'.coveragerc'), 'w') as f:
            f.write('[run]\n' f'source = {str(here/"temp_conf"/name)}\n' f'data_file = {str(here/"temp_conf"/name/".coverage")}\n' 'dynamic_context = test_function')
        test_res = subprocess.run(['coverage', 'run', f'--rcfile={str(here/"temp_conf"/name/".coveragerc")}', '-m', 'pytest', str(here/"temp_conf"/name)], capture_output=True, timeout=600)
        print(f'!!!!\n{test_res.stderr.decode("utf-8")}\n!!!!\n{test_res.stdout.decode("utf-8")}\n!!!!')