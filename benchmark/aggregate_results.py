import numpy as np
import argparse
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--glob', type=str, required=True)
    args = parser.parse_args()
    csv_files = Path(__file__).resolve().parent.glob(args.glob)
    results = []
    for file in csv_files:
        with open(file, 'r') as f:
            lines = f.read().splitlines()
        for line in lines[1:]:
            results.append([float(i) for i in line.split(',')[1:]])
    headers = lines[0].split(',')[1:]
    cols = []
    for i in len(results[0]):
        cols.append([results[j][i] for j in len(results)])
    with open('aggregate.csv', 'w') as f:
        print('col, min, mean, max, std')
        f.write('col, min, mean, max, std\n')
        for i in range(len(cols)):
            print(f'{headers[i]}, {np.min(cols[i])}, {np.mean(cols[i])}, {np.max(cols[i])}, {np.std(cols[i])}')
            f.write(f'{headers[i]}, {np.min(cols[i])}, {np.mean(cols[i])}, {np.max(cols[i])}, {np.std(cols[i])}\n')
