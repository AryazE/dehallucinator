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
    best_ng = {}
    best_ap = {}
    baseline = ''
    other_mode = ''
    for mode in results.keys():
        if mode.startswith('baseline'):
            baseline = mode
            break
    N = 0
    K = 5
    better = {}
    for mode, sub_res in results.items():
        if mode == baseline:
            continue
        else:
            other_mode = mode
        for _id, nums in sub_res.items():
            base_res = [int(x) for x in results[baseline][_id][0][2:]]
            better[_id] = -1000000
            for resi in range(len(nums)):
                num_res = [int(x) for x in nums[resi][2:]]
                if num_res[0] == base_res[0]:
                    if num_res[1] == base_res[1] and num_res[2] == base_res[2]:
                        better[_id] = max(better[_id], 0)
                    else:
                        better[_id] = max(better[_id], base_res[1] - num_res[1] + base_res[2] - num_res[2])
                elif num_res[0] < base_res[0]:
                    better[_id] = max(better[_id], -base_res[0])
                else:
                    better[_id] = max(better[_id], num_res[0])
    output = ""
    for _id, diff in better.items():
        output += f"{other_mode}, {args.results.split('/')[-1]}, {_id}, {better[_id]}, {', '.join(results[baseline][_id][0])}"
        for i in results[other_mode][_id]:
            output += f", {', '.join(i)}"
        output += "\n"
    with open(Path(__file__).parent.resolve()/"results_comparing_tests.csv", "a") as f:
        f.write(output)

                    