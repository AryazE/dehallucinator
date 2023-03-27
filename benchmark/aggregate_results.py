import numpy as np
import argparse
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--glob', type=str, required=True)
    args = parser.parse_args()
    csv_files = Path(__file__).resolve().parent.glob(args.glob)
    results = []
    max_fails = []
    ind = 0
    jj = []
    for file in csv_files:
        with open(file, 'r') as f:
            lines = f.read().splitlines()
        max_f = 0
        for line in lines[1:]:
            results.append([float(i) for i in line.split(',')[1:]])
            max_f = max(max_f, int(results[-1][0]), int(results[-1][3]))
            jj.append(ind)
        max_fails.append(max_f)
        ind += 1
    headers = lines[0].split(',')[1:]
    cols = []
    for i in range(len(results[0])):
        cols.append([results[j][i]/max_fails[jj[j]] if results[j][i] > -1 else 1 for j in range(len(results))])
    with open('aggregate.csv', 'w') as f:
        print('col, min, mean, max, std')
        f.write('col, min, mean, max, std\n')
        for i in range(len(cols)):
            print(f'{headers[i]}, {np.min(cols[i])}, {np.mean(cols[i])}, {np.max(cols[i])}, {np.std(cols[i])}')
            f.write(f'{headers[i]}, {np.min(cols[i])}, {np.mean(cols[i])}, {np.max(cols[i])}, {np.std(cols[i])}\n')
