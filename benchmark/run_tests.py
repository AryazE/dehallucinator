import sys
import shutil
import subprocess
import json
import argparse
import logging
from distutils import dir_util
from pathlib import Path
import xml.etree.ElementTree as ET

def run_tests(config, id):
    here = Path(__file__).resolve().parent
    temp_dir = here/'experiment'/config['name']/f'temp{id}'/config['project_root']
    dir_util.copy_tree(str(here/config['project_root']/'tests'), str(temp_dir/'tests'))
    shutil.copyfile(str(here/config['project_root']/'setup.py'), str(temp_dir/'setup.py'))
    if (temp_dir/'requirements.txt').exists():
        subprocess.run(['pip', 'install', '-r', str(temp_dir/'requirements.txt')], check=True, stdout=subprocess.DEVNULL)
    install_res = subprocess.run([sys.executable, '-m', 'pip', 'install', str(temp_dir)], check=True, stdout=subprocess.DEVNULL)
    pytest_command = [
        '--tb=no', 
        '-q', 
        '--junitxml', 
        f"{here/'experiment'/config['name']/f'temp{id}'}/results.xml",
    ]
    pytest_command.append(str(temp_dir/'tests'))
    test_res = subprocess.run([sys.executable, '-m', 'pytest'] + pytest_command, capture_output=True)
    uninstall_res = subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', config['name']], check=True, stdout=subprocess.DEVNULL)
    results = dict()
    tree = ET.parse(here/'experiment'/config['name']/f'temp{id}'/'results.xml')
    root = tree.getroot()
    for child in list(root):
        if child.tag == 'testsuite':
            results.update({
                'tests': int(child.attrib['tests']),
                'errors': int(child.attrib['errors']),
                'failures': int(child.attrib['failures']),
                'skipped': int(child.attrib['skipped'])
            })
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--id', type=int, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    print(run_tests(config, args.id))