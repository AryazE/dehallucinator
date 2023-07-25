import time
from pathlib import Path
import os
import argparse
import json
import logging
import traceback
import shutil
from prepare_project import prepare
from run_completion import run_completion
from run_tests import run_tests
from read_test_results import read_test_results
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModel
from dotenv import dotenv_values
from huggingface_hub import login

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='Codex', help='CodeGen or Codex')
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--mode', type=str, required=True)
    parser.add_argument('--ids', nargs='*', type=int, default=[])
    parser.add_argument('--fromId', type=int, default=0)
    parser.add_argument('--log', type=str, default='')
    parser.add_argument('--noTests', action='store_true')
    parser.add_argument('--k', type=int, default=4)
    parser.add_argument('--t', type=float, default=0.5)
    parser.add_argument('--c', type=int, default=4)
    args = parser.parse_args()
    env_vars = dotenv_values('.env')
    hf_token = env_vars['hf-token']
    login(token=hf_token)
    print(time.perf_counter())
    with open(args.config, 'r') as f:
        config = json.load(f)
    print(time.perf_counter())
    ids = args.ids
    if len(ids) == 0 and args.fromId > 0:
        for i in config['evaluations']:
            if i['id'] >= args.fromId:
                ids.append(i['id'])
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    logging.basicConfig(level=logging.INFO,filename=f'benchmark/logs/{config["project_root"].split("/")[-1]}-{args.mode}{args.log}.log', filemode='a')
    logger = logging.getLogger(__name__)
    here = Path(__file__).resolve().parent
    if args.model.startswith('l'):
        if args.model == 'lCodeGen':
            llm_tok = AutoTokenizer.from_pretrained("Salesforce/codegen-2B-mono")
            llm = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-2B-mono", device_map='auto')
        elif args.model == 'lCodeGen25':
            llm_tok = AutoTokenizer.from_pretrained("Salesforce/codegen25-7b-mono", trust_remote_code=True)
            llm = AutoModelForCausalLM.from_pretrained("Salesforce/codegen25-7b-mono", device_map='auto', load_in_4bit=True)
        elif args.model =='lUniXcoder':
            llm_tok = AutoTokenizer.from_pretrained("microsoft/unixcoder-base")
            llm = AutoModel.from_pretrained("microsoft/unixcoder-base")
        elif args.model == 'lStarCoderPlus':
            llm_tok = AutoTokenizer.from_pretrained("bigcode/starcoderplus", token=hf_token)
            llm = AutoModelForCausalLM.from_pretrained("bigcode/starcoderplus", token=hf_token, device_map='auto')

    if not (here/'experiment'/config['name']/'base').exists() or any([not (here/'experiment'/config['name']/'base'/f'temp{i}').exists() for i in ids]):
        print('Base or some eval are missing. Creating...')
        print(time.perf_counter())
        executable, orig_results, sample = prepare(config, 'base', ids, args.noTests, args.model, llm=llm, llm_tok=llm_tok)
        print(time.perf_counter())
        if len(sample) < len(ids):
            new_eval = []
            for i in config['evaluations']:
                if i['id'] in sample or i['id'] == 0:
                    new_eval.append(i)
            config['evaluations'] = new_eval
            Path(args.config).unlink()
            with open(args.config, 'w') as f:
                json.dump(config, f, indent=2)
    else:
        if args.noTests:
            orig_results = {"tests": 0, "errors": 0, "failures": 0, "skipped": 0, "id": 0}
        else:
            orig_results = read_test_results(str(here/'experiment'/config['name']/'base'/'temp0'/'results.xml'), 0)
        with open(str(here/'experiment'/config['name']/'base'/'interpreter.txt'), 'r') as f:
            executable = f.read()
    print(time.perf_counter())
    if (here/'experiment'/config['name']/args.mode).exists():
        shutil.rmtree(str(here/'experiment'/config['name']/args.mode))
    shutil.copytree(str(here/'experiment'/config['name']/'base'), str(here/'experiment'/config['name']/args.mode), ignore=shutil.ignore_patterns('codeqldb'))
    print(time.perf_counter())
    print(f'original: {orig_results}')
    if not (here/'experiment'/config['name']/args.mode/'test_results.json').exists():
        with open(here/'experiment'/config['name']/args.mode/'test_results.json', 'w') as f:
            json.dump([orig_results], f)
    results = []
    for i in config["evaluations"]:
        if (len(i['file']) == 0) or (len(ids) > 0 and i['id'] not in ids):
            continue
        if not (here/'experiment'/config['name']/args.mode/f'temp{i["id"]}').exists():
            continue
        print(f'Running {i["id"]}')
        try:
            # best_context, possible_context, given_context = run_completion(args.model, config, i["id"], args.mode, args.log)
            start = time.perf_counter_ns()
            completions = run_completion(args.model, config, i["id"], args.mode, args.log, k=args.k, t=args.t, c=args.c, llm=llm, llm_tok=llm_tok)
            end = time.perf_counter_ns()
            with open(here/'experiment'/config['name']/args.mode/'completion_times_ns.txt', 'a') as f:
                f.write(f'{end-start}\n')
            # if best_context > -1:
            #     logger.info(f'best_context: {best_context}, possible_context: {possible_context}, given_context: {given_context}')
            print(time.perf_counter())
            if not args.noTests:
                tmp_res = run_tests(config, i["id"], args.mode, executable)
                new_res = tmp_res[0]
                best = 0
                for r in range(1, len(tmp_res)):
                    if new_res['tests'] > tmp_res[r]['tests'] or (new_res['failures'] > tmp_res[r]['failures'] and new_res['tests'] == tmp_res[r]['tests']):
                        new_res = tmp_res[r]
                        best = r
                with open(here/'experiment'/config['name']/args.mode/f'temp{i["id"]}'/'res_numbers.txt', 'r') as f:
                    content = f.read().splitlines()
                with open(here/'experiment'/config['name']/args.mode/f'temp{i["id"]}'/'res_numbers.txt', 'w') as f:
                    for l in range(len(content)):
                        f.write(f"{content[l]} {tmp_res[l]['tests']} {tmp_res[l]['errors']} {tmp_res[l]['failures']} {tmp_res[l]['skipped']}\n")
            else:
                new_res = {"tests": 0, "errors": 0, "failures": 0, "skipped": 0, "id": i["id"]}
                best = -1
            print(time.perf_counter())
            with open(here/'experiment'/config['name']/args.mode/'test_results.json', 'r') as f:
                results = json.load(f)
            #print(f'test results: {results}')
            print(f'new_res: {new_res}')
            if new_res['id'] not in [j['id'] for j in results]:
                results.append(new_res)
            with open(here/'experiment'/config['name']/args.mode/'test_results.json', 'w') as f:
                json.dump(results, f)
            with open(here/'experiment'/config['name']/args.mode/f'temp{i["id"]}'/'best.md', 'a') as f:
                f.write(f'best test:  \n```python\n{completions[int(best)]}\n```\n')
            print(f'{new_res} -> {best}')
            print(time.perf_counter())
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            
