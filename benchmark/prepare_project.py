import argparse
import csv
import time
import json
import random
from distutils import dir_util
from pathlib import Path
import traceback
import virtualenv
from run_tests import run_tests
from coder.utils import run_query, embeddings, parse_results_into_context
from coder.utils import get_completion_safely, postprocess
from coder.backend import Completion
import numpy as np
from sklearn.preprocessing import normalize
from sklearn.neighbors import BallTree
import pickle

CURSOR = '<CURSOR>'
API_regex = r'(?:\w+\.)*\w+\(.*\)'

def prepare(config, mode, ids=[], noTests=False, model='GPT3.5', llm=None, llm_tok=None):
    global CURSOR
    
    orig_results = {"tests": 0, "errors": 0, "failures": 0, "skipped": 0, "id": 0}
    okay = []
    here = Path(__file__).resolve().parent
    dir_util.mkpath(str(here/'experiment'/config['name']/mode))
    env_session = virtualenv.cli_run([str(here/'experiment'/config['name']/mode/'venv')])
    with open(str(here/'experiment'/config['name']/mode/'interpreter.txt'), 'w') as f:
        f.write(env_session.interpreter.executable)
    if mode == 'base':
        database = here/'experiment'/config['name']/'codeqldb'
        if not database.exists():
            dir_util.copy_tree(str(here/'CodeQLDBs'/config['name']/'codeql_db'), str(database/'..'/'codeqldb'))
            start = time.process_time_ns()
            run_query(database, 'functionContext.ql', 'functionRes.csv', str(database/'..'))
            run_query(database, 'classContext.ql', 'classRes.csv', str(database/'..'))
            temp_dir = here/'experiment'/config['name']/mode/f'temp0'
            additional_context = dict()
            additional_context.update(parse_results_into_context(database/'..'/'functionRes.csv'))
            additional_context.update(parse_results_into_context(database/'..'/'classRes.csv'))
            embds = []
            everything = []
            for k, v in additional_context.items():
                everything.extend(v)
                if len(everything) > 20:
                    for e in v:
                        embds.extend(embeddings([e]))
                else:
                    embds.extend(embeddings(v))
            with open(here/'experiment'/config["name"]/'all.json', 'w') as f:
                json.dump(everything, f)
            embds = normalize(np.array(embds))
            tree = BallTree(embds, metric='euclidean')
            with open(here/'experiment'/config["name"]/'tree.pkl', 'wb') as f:
                pickle.dump(tree, f)
            end = time.process_time_ns()
            with open(str(here/'experiment'/config['name']/mode/'preprocessing_time.txt'), 'w') as f:
                f.write(f'{end - start} ns\n')

    project_apis = set()
    with open(here/'experiment'/config["name"]/'functionRes.csv', newline='') as f:
        csv_reader = csv.DictReader(f)
        for line in csv_reader:
            project_apis.add(line['name'])
    easy_completions = 0
    trivial_tests = 0
    not_covered_by_tests = 0
    for i in config['evaluations']:
        if len(okay) >= 10:
            break
        if i['id'] > 0 and len(ids) > 0 and i['id'] not in ids:
            continue
        print(f'Preparing {i["id"]}')
        dir_util.mkpath(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
        temp_dir = here/'experiment'/config['name']/mode/f'temp{i["id"]}'/config['project_root']
        dir_util.copy_tree(str(here/config['project_root']), str(temp_dir))
        try:
            dir_util.remove_tree(str(temp_dir/config['tests_path']))
        except:
            pass
        if i['id'] == 0 and not noTests:
            orig_results = run_tests(config, 0, mode, env_session.interpreter.executable)[0]
        
        if len(i['file']) == 0:
            continue
        # exclude = []
        # for j in i['remove']:
        #     exclude.append([i['file'], j['start_line'], j['start_column'], j['end_line'], j['end_column']])
        # with open(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'/'exclude.csv'), 'w') as f:
        #     for j in exclude:
        #         f.write(','.join([str(k) for k in j]) + '\n')
        with open(temp_dir/i["file"]) as f:
            orig_code = f.read()
        code = orig_code.splitlines(keepends=True)
        new_code = []
        pre_context = ''
        post_context = ''

        new_code = []
        cursor = CURSOR
        for l in range(len(code)):
            temp = code[l]
            for j in i['remove']:
                if j['description'] == 'imports':
                    continue
                if j['start_line'] - 1 <= l <= j['end_line'] - 1:
                    if j['start_line'] == j['end_line']:
                        temp = code[l][:j['start_column']] + (cursor if j['description'] != 'imports' else '') + code[l][j['end_column']:]
                        pre_context = ''.join(new_code + [code[l][:j['start_column']]])
                        post_context = code[l][j['end_column']:]
                    else:
                        if l == j['start_line'] - 1:
                            temp = code[l][:j['start_column']] + (cursor if j['description'] != 'imports' else '')
                            pre_context = ''.join(new_code + [code[l][:j['start_column']]])
                        elif l == j['end_line'] - 1:
                            temp = code[l][j['end_column']:]
                            post_context = code[l][j['end_column']:]
                        else:
                            temp = None
            if temp:
                new_code.append(temp)
        post_context = ''.join([post_context] + code[i['remove'][-1]['end_line']:])
        ground_truth = orig_code[len(pre_context):-len(post_context)]

        # try:
        #     gt_apis = matchers.findall(cst.parse_module(as_module(ground_truth)), matchers.Call() | matchers.Attribute())
        #     gt_apis = filter_external(gt_apis, project_apis)
        #     if len(gt_apis) == 0:
        #         print('Function does not call any APIs')
        #         dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
        #         continue
        # except Exception as e:
        #     pass

        init_comp = get_completion_safely(model, Completion(model=llm, tokenizer=llm_tok), pre_context, k=1)[0]
        init_comp = postprocess(init_comp, mode='api')
        if init_comp.startswith(ground_truth):
            print('Function is too easy to complete')
            dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
            easy_completions += 1
            continue

        if not noTests:
            tab = ground_truth[:-len(ground_truth.lstrip())]
            cursor = tab + 'bool(True)\n'

            temp_new_code = [(nc.replace(CURSOR, cursor) if CURSOR in nc else nc) for nc in new_code]
            
            with open(temp_dir/i["file"], 'w') as f:
                f.write(''.join(temp_new_code))
            
            test_results = run_tests(config, i['id'], mode, env_session.interpreter.executable)
            # try:
            #     with open(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'/'checkTest.txt'), 'r') as f:
            #         content = f.read()
            # except Exception as e:
            #     with open(str(here/'experiment'/config['name']/mode/"removed_coverage_tests.txt"), "a") as f:
            #         f.write(f"================\n{pre_context[-500:]}\n{ground_truth}\n")
            #     print('Test not covering function')
            #     print(traceback.format_exc())
            #     dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
            #     not_covered_by_tests += 1
            #     continue
            # if content != 'here':
            #     with open(str(here/'experiment'/config['name']/mode/"removed_execution_tests.txt"), "a") as f:
            #         f.write(f"================\n{pre_context[-500:]}\n{ground_truth}\n")
            #     print('Test not executing code in function')
            #     dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
            #     not_covered_by_tests += 1
            #     continue
            different = False
            for k, v in test_results[0].items():
                if k not in orig_results or orig_results[k] != v:
                    different = True
                    break
            if not different:
                print('Test is trivial')
                dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
                trivial_tests += 1
                continue
            okay.append(i['id'])
        else:
            okay.append(i['id'])
        
        with open(temp_dir/i["file"], 'w') as f:
            f.writelines(new_code)

    if len(okay) > 50:
        sample = random.sample(okay, 50)
        for id in okay:
            if id not in sample:
                dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{id}'))
    else:
        sample = okay
    if len(okay) < 50:
        sample = okay
    # sample = okay
    with open(str(here/'experiment'/config['name']/'dataset_report.txt'), "w") as f:
        f.write(f"Easy completions: {easy_completions}\nNot covered by any test: {not_covered_by_tests}\nTrivial tests: {trivial_tests}\n")
    return env_session.interpreter.executable, orig_results, sample

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    print(prepare(config, args.mode))
