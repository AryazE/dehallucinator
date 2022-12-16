from pathlib import Path
import argparse
import json
from distutils import dir_util
from prepare_project import prepare
from run_completion import run_completion
from run_tests import run_tests

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--mode', type=str, required=True)
    parser.add_argument('--ids', nargs='*', type=int, default=[])
    parser.add_argument('--fromId', type=int, default=0)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    here = Path(__file__).resolve().parent
    executable = prepare(config, args.mode, args.ids)
    orig_results = run_tests(config, 0, args.mode, executable)
    print(f'original: {orig_results}')
    if args.fromId == 0:
        with open(here/'experiment'/config['name']/args.mode/'test_results.json', 'w') as f:
            json.dump([orig_results], f)
    results = []
    for i in config["evaluations"]:
        if (len(i['file']) == 0) or (args.fromId > i['id']) or (len(args.ids) > 0 and i['id'] not in args.ids):
            continue
        try:
            run_completion(config, i["id"], args.mode)
            new_res = run_tests(config, i["id"], args.mode, executable)
            with open(here/'experiment'/config['name']/args.mode/'test_results.json', 'r') as f:
                results = json.load(f)
            if new_res['id'] not in [j['id'] for j in results]:
                results.append(new_res)
            with open(here/'experiment'/config['name']/args.mode/'test_results.json', 'w') as f:
                json.dump(results, f)
            print(new_res)
        except Exception as e:
            print(e.with_traceback())
            pass