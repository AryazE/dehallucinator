from pathlib import Path
import argparse
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=str, required=True, help='Path to experiment directory of the project')
    parser.add_argument('--modes', nargs='+', type=str, default=['simple'])
    args = parser.parse_args()
    final = []
    results = dict()
    ids = set()
    for mode in args.modes:
        test_result_path = Path(__file__).resolve().parent/args.project/mode/'test_results.json'
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
        final.append(final_row)
        if id > 0 and final_row != final[0]:
            print(f'Bad completion on {id}: {final_row}')
        for i in range(len(final_row) - 1):
            if final_row[i][1:] != final_row[i + 1][1:]:
                print(f'Different results for {id} : {final_row[i]} vs {final_row[i + 1]}')
    print('id, ' + ', '.join(args.modes))
    for k, v in report.items():
        print(f'{k}, ' + ', '.join([str(x) for x in v]))
    
    

    