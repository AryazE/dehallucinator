from pathlib import Path
import argparse
import json
import logging
import shutil
from prepare_project import prepare
from run_completion import run_completion
from run_tests import run_tests
from read_test_results import read_test_results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='Codex', help='CodeGen or Codex')
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--mode', type=str, required=True)
    parser.add_argument('--ids', nargs='*', type=int, default=[])
    parser.add_argument('--fromId', type=int, default=0)
    parser.add_argument('--log', type=str, default='')
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    logging.basicConfig(level=logging.INFO,filename=f'benchmark/{config["project_root"].split("/")[-1]}-{args.mode}{args.log}.log', filemode='a')
    logger = logging.getLogger(__name__)
    here = Path(__file__).resolve().parent
    if not (here/'experiment'/config['name']/'base').exists():
        executable, orig_results = prepare(config, 'base', [])
    else:
        orig_results = read_test_results(str(here/'experiment'/config['name']/'base'/'temp0'/'results.xml'), 0)
        with open(str(here/'experiment'/config['name']/'base'/'interpreter.txt'), 'r') as f:
            executable = f.read()
    shutil.copy_tree(str(here/'experiment'/config['name']/'base'), str(here/'experiment'/config['name']/args.mode), ignore=shutil.ignore_patterns('codeqldb'))
    print(f'original: {orig_results}')
    if args.fromId == 0 and len(args.ids) == 0:
        with open(here/'experiment'/config['name']/args.mode/'test_results.json', 'w') as f:
            json.dump([orig_results], f)
    results = []
    for i in config["evaluations"]:
        if (len(i['file']) == 0) or (args.fromId > i['id']) or (len(args.ids) > 0 and i['id'] not in args.ids):
            continue
        if not (here/'experiment'/config['name']/args.mode/f'temp{i["id"]}').exists():
            continue
        print(f'Running {i["id"]}')
        try:
            best_context, possible_context, given_context = run_completion(args.model, config, i["id"], args.mode, args.log)
            if best_context > -1:
                logger.info(f'best_context: {best_context}, possible_context: {possible_context}, given_context: {given_context}')
            new_res = run_tests(config, i["id"], args.mode, executable)
            with open(here/'experiment'/config['name']/args.mode/'test_results.json', 'r') as f:
                results = json.load(f)
            if new_res['id'] not in [j['id'] for j in results]:
                results.append(new_res)
            with open(here/'experiment'/config['name']/args.mode/'test_results.json', 'w') as f:
                json.dump(results, f)
            print(new_res)
        except Exception as e:
            print(e)