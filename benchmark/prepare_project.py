import argparse
import csv
import time
import json
import Levenshtein
import shutil
import random
import subprocess
from distutils import dir_util
from pathlib import Path
import traceback
import virtualenv
from run_tests import run_tests
from coder.utils import run_query, embeddings
from coder.utils import get_completion_safely, postprocess
from coder.backend import Completion
from run_completion import filter_external, as_module
import libcst as cst
from libcst import matchers
import numpy as np
from sklearn.neighbors import BallTree
import pickle

CURSOR = '<CURSOR>'
API_regex = r'(\w+\.)*\w+\(.*\)'

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
        end = time.process_time_ns()
        with open(str(here/'experiment'/config['name']/mode/'preprocessing_time.txt'), 'w') as f:
            f.write(f'{end - start} ns')

    project_apis = set()
    with open(here/'experiment'/config["name"]/'functionRes.csv', newline='') as f:
        csv_reader = csv.DictReader(f)
        for line in csv_reader:
            project_apis.add(line['name'])
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
        # if i['id'] == 0 and mode == 'base':
        #     temp_dir = here/'experiment'/config['name']/mode/f'temp0'
        #     start = time.process_time_ns()
        #     all_py_files = sorted((temp_dir/config['project_root']).glob('**/*.py'))
        #     embd = []
        #     lens = []
        #     for fi in all_py_files:
        #         with open(fi, 'r') as f:
        #             content = f.read()
        #             lines = content.splitlines(keepends=True)
        #         lens.append(len(lines))
        #         windows = [''.join(lines[i:i+5]) for i in range(len(lines) - 4)]
        #         embd.extend(embeddings(windows))
        #         with open(temp_dir/'all.py', 'a') as f:
        #             f.write(content)
        #             if not content.endswith('\n'):
        #                 f.write('\n')
        #     with open(temp_dir/'all.files', 'w') as f:
        #         f.write('\n'.join([f'{str(all_py_files[i])} {lens[i]}' for i in range(len(all_py_files))]))
        #     tree = BallTree(np.array(embd))
        #     with open(temp_dir/'tree.pkl', 'wb') as f:
        #         pickle.dump(tree, f)
        #     end = time.process_time_ns()
        #     with open(temp_dir/'BallTree_time.txt', 'w') as f:
        #         f.write(str((end - start)/1000))
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
            continue
        elif Levenshtein.ratio(init_comp, ground_truth) < 0.1:
            print('Function is too hard to complete')
            dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
            continue

        if not noTests:
            cursor = 'with open("' + str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'/'checkTest.txt') + '", "w") as f: f.write("here")\n'

            temp_new_code = new_code.replace(CURSOR, cursor)
            
            with open(temp_dir/i["file"], 'w') as f:
                f.write(''.join(temp_new_code))
            
            test_results = run_tests(config, i['id'], mode, env_session.interpreter.executable)
            try:
                with open(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'/'checkTest.txt'), 'r') as f:
                    content = f.read()
            except Exception as e:
                print('Test not covering function')
                print(traceback.format_exc())
                dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
                continue
            if content != 'here':
                print('Test not executing code in function')
                dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
                continue
            different = False
            for k, v in test_results[0].items():
                if k not in orig_results or orig_results[k] != v:
                    different = True
                    break
            if not different:
                print('Test is trivial')
                dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
                continue
            okay.append(i['id'])
        else:
            okay.append(i['id'])
        
        with open(temp_dir/i["file"], 'w') as f:
            f.writelines(new_code)

    if len(okay) > 10:
        sample = random.sample(okay, 10)
        for id in okay:
            if id not in sample:
                dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{id}'))
    else:
        sample = okay
    if len(okay) < 10:
        sample = okay
    # sample = okay
    return env_session.interpreter.executable, orig_results, sample

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    print(prepare(config, args.mode))
