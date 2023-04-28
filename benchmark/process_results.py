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
    here = Path(__file__).resolve().parent.parent
    for mode in args.modes:
        test_result_path = here/args.project/mode/'test_results.json'
        with open(test_result_path, 'r') as f:
            res_list = json.load(f)
        results[mode] = {x['id']: (x['tests'], x['errors'], x['failures'], x['skipped']) for x in res_list}
        ids.update(set([x['id'] for x in res_list]))
    ids = sorted(list(ids))
    complete = dict()
    (here/args.output).mkdir(parents=True, exist_ok=True)
    for mode in args.modes:
        complete[mode] = dict()
        for id in ids:
            if id == 0:
                continue
            result_path = here/args.project/mode/f'temp{id}'/'res_numbers.txt'
            k_res = []
            with open(result_path, 'r') as f:
                res = f.read().splitlines()
            for k in range(len(res)):
                k_res.append(res[k].split(' '))
            complete[mode][id] = k_res
    with open(here/args.output/'complete.json', 'w') as f:
        json.dump(complete, f)
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
                    lines = f.readlines()
                
                ngram_similarity = lines[0].split(' from ')[0][len('N-gram similarity '):].strip()
                if ngram_similarity.startswith('['):
                    ngram_similarity = max([float(ns.strip()) for ns in ngram_similarity[1:-1].split(',')])
                api_similarity = lines[1].split(' from ')[0][len('API similarity '):].strip()
                if api_similarity.startswith('['):
                    api_similarity = max([float(ap.strip()) for ap in api_similarity[1:-1].split(',')])
                api_count = int(lines[1].split('local APIs ')[1].strip())
                report[id][-1] = (report[id][-1], ngram_similarity, api_similarity, api_count)
            elif id > 0:
                report[id][-1] = (report[id][-1], 0, 0, 0)
        final.append(final_row)
        if id > 0 and final_row != final[0]:
            print(f'Bad completion on {id}: {final_row}')
        for i in range(len(final_row) - 1):
            if final_row[i][1:] != final_row[i + 1][1:]:
                print(f'Different results for {id} : {final_row[i]} vs {final_row[i + 1]}')
    print('id, ' + ', '.join(args.modes))
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
    
    headers = ['Test results', 'N-gram similarity', 'API similarity']
    with open(here/args.output/'README.md', 'w') as f:
        f.write('| id | ' + ' | '.join([args.modes[int(i/3)] + headers[i%3] for i in range(3*len(args.modes))]) + ' | ground truth | local APIs |\n')
        f.write('| --- | ' + ' | '.join(['---'] * (3*len(args.modes) + 2)) + ' |\n')
        for k, v in report.items():
            f.write(f'| {k} | ' + ' | '.join([f'[{v[x][0]}]({args.modes[x]}-{k}.md) | [{v[x][1]:.2f}](best-{args.modes[x]}-{k}.md) | [{v[x][2]:.2f}](best-{args.modes[x]}-{k}.md)' for x in range(len(v))]) + f' | [0](gt-{k}.md)' + f' | {v[-1][3]} ' + ' |\n')

    with open(here/f'x_{args.output}.csv', 'w') as f:
        f.write('id,' + ','.join([args.modes[int(i/3)] + headers[i%3] for i in range(3*len(args.modes))]) + ',local APIs\n')
        for k, v in report.items():
            f.write(f'{k},' + ','.join([f'{v[x][0]},{v[x][1]:.2f},{v[x][2]:.2f}' for x in range(len(v))]) + f',{v[-1][3]}\n')

    try:
        from grip import serve
        serve(str(here/args.output), port=5000)
    except ImportError:
        print('Done! You can install grip to serve the report')
