from pathlib import Path
import shutil
import argparse
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=str, required=True, help='Path to experiment directory of the project')
    parser.add_argument('--modes', nargs='+', type=str, default=['baseline'])
    parser.add_argument('--output', type=str, default='report')
    args = parser.parse_args()
    final = []
    results = dict()
    ids = set()
    here = Path(__file__).resolve().parent
    for mode in args.modes:
        test_result_path = here/args.project/mode/'test_results.json'
        with open(test_result_path, 'r') as f:
            res_list = json.load(f)
        results[mode] = {x['id']: (x['tests'], x['errors'], x['failures'], x['skipped']) for x in res_list}
        ids.update(set([x['id'] for x in res_list]))
    ids = sorted(list(ids))
    report = dict()
    for id in ids:
        final_row = []
        if id > 0:
            report[id] = []
        for mode in args.modes:
            if id not in results[mode]:
                final_row.append((mode, 0, 0, 0, 0))
            else:
                final_row.append((mode,) + results[mode][id])
            if id > 0:
                if final_row[-1][1] != final[0][len(final_row)-1][1]:
                    report[id].append(-2)
                elif final_row[-1][2] != final[0][len(final_row)-1][2]:
                    report[id].append(-1)
                else:
                    report[id].append(final_row[-1][3] - final[0][len(final_row)-1][3])
            if (here/args.project/mode/f'temp{id}'/'best.md').exists():
                with open(here/args.project/mode/f'temp{id}'/'best.md') as f:
                    similarity = float(f.read().split(' from ')[0][11:])
                report[id][-1] = (report[id][-1], similarity)
            elif id > 0:
                report[id][-1] = (report[id][-1], 0)
        final.append(final_row)
        if id > 0 and final_row != final[0]:
            print(f'Bad completion on {id}: {final_row}')
        for i in range(len(final_row) - 1):
            if final_row[i][1:] != final_row[i + 1][1:]:
                print(f'Different results for {id} : {final_row[i]} vs {final_row[i + 1]}')
    print('id, ' + ', '.join(args.modes))
    (here/args.output).mkdir(parents=True, exist_ok=True)
    for k, v in report.items():
        print(f'{k}, ' + ', '.join([str(x) for x in v]))
        if (here/args.project/mode/f'temp{k}'/'gt.md').exists():
            shutil.copy(str(here/args.project/mode/f'temp{k}'/'gt.md'), str(here/args.output/f'gt-{k}.md'))
        if k != 0:
            for i, mode in enumerate(args.modes):
                if (here/args.project/mode/f'temp{k}'/'best.md').exists():
                    shutil.copy(str(here/args.project/mode/f'temp{k}'/'best.md'), str(here/args.output/f'best-{mode}-{k}.md'))
                try:
                    shutil.copy(str(here/args.project/mode/f'temp{k}'/'artifact.md'), str(here/args.output/f'{mode}-{k}.md'))
                except FileNotFoundError:
                    shutil.copy(str(here/args.project/mode/f'temp{k}'/'artifacts.md'), str(here/args.output/f'{mode}-{k}.md'))
    
    with open(here/args.output/'README.md', 'w') as f:
        f.write('| id | ' + ' | '.join([args.modes[int(i/2)] for i in range(2*len(args.modes))]) + ' | ground truth ' + ' |\n')
        f.write('| --- | ' + ' | '.join(['---'] * (2*len(args.modes) + 1)) + ' |\n')
        for k, v in report.items():
            f.write(f'| {k} | ' + ' | '.join([f'[{v[x][0]}]({args.modes[x]}-{k}.md) | [{v[x][1]:.2f}](best-{args.modes[x]}-{k}.md)' for x in range(len(v))]) + f' | [0](gt-{k}.md)' + ' |\n')

    try:
        from grip import serve
        serve(str(here/args.output), port=5000)
    except ImportError:
        print('Done! You can install grip to serve the report')