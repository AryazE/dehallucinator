import argparse
from pathlib import Path
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', type=str, required=True, help='Path to results generated by process_results.py')
    args = parser.parse_args()

    with open(Path(args.results)/'complete.json', 'r') as f:
        results = json.load(f)
    
    abs_ng = {}
    abs_ap = {}
    baseline = ''
    for mode in results.keys():
        if mode.startswith('baseline'):
            baseline = mode
            break
    for mode, sub_res in results.items():
        ng_imp = 0
        ap_imp = 0
        ng_it = 0
        ap_it = 0
        ng_dicoder_better = 0
        ap_dicoder_better = 0
        abs_ng[mode] = [(0, 0)] * 4
        abs_ap[mode] = [(0, 0)] * 4
        for id, res in sub_res.items():
            if id == 0:
                continue
            ngram = [float(x[0]) for x in res]
            for i in range(len(ngram)):
                abs_ng[mode][i] = ((abs_ng[mode][i][0] * abs_ng[mode][i][1] + ngram[i]) / (abs_ng[mode][i][1] + 1), abs_ng[mode][i][1] + 1)
            api = [float(x[1]) for x in res]
            for i in range(len(api)):
                abs_ap[mode][i] = ((abs_ap[mode][i][0] * abs_ap[mode][i][1] + api[i]) / (abs_ap[mode][i][1] + 1), abs_ap[mode][i][1] + 1)
            ng_count = 0
            ap_count = 0
            for i in range(1, len(res)):
                if ngram[i] > ngram[i-1]:
                    ng_count += 1
                if api[i] > api[i-1]:
                    ap_count += 1
            if not mode.startswith('baseline'):
                if ngram[-1] > float(results[baseline][id][0][0]):
                    ng_dicoder_better += 1
                if api[-1] > float(results[baseline][id][0][1]):
                    ap_dicoder_better += 1
            if ng_count > 0:
                ng_imp += 1
            if ap_count > 0:
                ap_imp += 1
            if ng_count > 1:
                ng_it += 1
            if ap_count > 1:
                ap_it += 1
        print(f'For mode {mode}:')
        print(f'N-gram improvement: {ng_imp}')
        print(f'API improvement: {ap_imp}')
        print(f'N-gram improvement (iterative): {ng_it}')
        print(f'API improvement (iterative): {ap_it}')
        if not mode.startswith('baseline'):
            print(f'N-gram improvement (dicoder better): {ng_dicoder_better}')
            print(f'API improvement (dicoder better): {ap_dicoder_better}')
        print(f'N-gram similarity (absolute): {[i[0] for i in abs_ng[mode]]}')
        print(f'API similarity (absolute): {[i[0] for i in abs_ap[mode]]}')