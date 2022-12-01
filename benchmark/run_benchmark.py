import subprocess
from pathlib import Path
import sys

if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    for config in here.glob('*.json'):
        print(f'Running {config}')
        subprocess.run([
            sys.executable, (here/'run_project.py').as_posix(),
            '--config', str(config),
            '--mode', 'baseline'
        ])
        subprocess.run([
            sys.executable, (here/'run_project.py').as_posix(),
            '--config', str(config),
            '--mode', 'simple'
        ])