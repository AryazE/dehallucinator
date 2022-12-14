import subprocess
from pathlib import Path
import sys
import time

if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    for config in here.glob('*.json'):
        print(f'Running {config}')
        start = time.time()
        subprocess.run([
            sys.executable, (here/'run_project.py').as_posix(),
            '--config', str(config),
            '--mode', 'baseline'
        ])
        print(f'Baseline took {time.time() - start} seconds, i.e {(time.time() - start) / 60} minutes')
        start = time.time()
        subprocess.run([
            sys.executable, (here/'run_project.py').as_posix(),
            '--config', str(config),
            '--mode', 'simple'
        ])
        print(f'Simple took {time.time() - start} seconds, i.e {(time.time() - start) / 60} minutes')