import argparse
import json
import os
import random
import subprocess
from distutils import dir_util
from pathlib import Path
import traceback
import virtualenv
from run_tests import run_tests
from coder.utils import run_query

CURSOR = '<CURSOR>'

def prepare(config, mode, ids=[], noTests=False):
    global CURSOR
    
    orig_results = {"tests": 0, "errors": 0, "failures": 0, "skipped": 0, "id": 0}
    okay = []
    here = Path(__file__).resolve().parent
    dir_util.mkpath(str(here/'experiment'/config['name']/mode))
    env_session = virtualenv.cli_run([str(here/'experiment'/config['name']/mode/'venv')])
    with open(str(here/'experiment'/config['name']/mode/'interpreter.txt'), 'w') as f:
        f.write(env_session.interpreter.executable)
    for i in config['evaluations']:
        if i['id'] > 0 and len(ids) > 0 and i['id'] not in ids:
            continue
        if len(okay) == 21:
            sample = okay
            break
        print(f'Preparing {i["id"]}')
        dir_util.mkpath(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
        temp_dir = here/'experiment'/config['name']/mode/f'temp{i["id"]}'/config['project_root']
        dir_util.copy_tree(str(here/config['project_root']), str(temp_dir))
        dir_util.remove_tree(str(temp_dir/config['tests_path']))
        if i['id'] == 0 and not noTests:
            orig_results, best = run_tests(config, 0, mode, env_session.interpreter.executable)
        if len(i['file']) == 0:
            continue
        # exclude = []
        # for j in i['remove']:
        #     exclude.append([i['file'], j['start_line'], j['start_column'], j['end_line'], j['end_column']])
        # with open(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'/'exclude.csv'), 'w') as f:
        #     for j in exclude:
        #         f.write(','.join([str(k) for k in j]) + '\n')
        with open(temp_dir/i["file"]) as f:
            code = f.readlines()
        new_code = []
        if not noTests:
            cursor = 'with open("' + str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'/'checkTest.txt') + '", "w") as f: f.write("here")\n'
            for l in range(len(code)):
                temp = code[l]
                for j in i['remove']:
                    if j['description'] == 'imports':
                        continue
                    if j['start_line'] - 1 <= l <= j['end_line'] - 1:
                        if j['start_line'] == j['end_line']:
                            temp = code[l][:j['start_column']] + (cursor if j['description'] != 'imports' else '') + code[l][j['end_column'] - 1:]
                        else:
                            if l == j['start_line'] - 1:
                                temp = code[l][:j['start_column']] + (cursor if j['description'] != 'imports' else '')
                            elif l == j['end_line'] - 1:
                                temp = code[l][j['end_column'] - 1:]
                            else:
                                temp = None
                if temp:
                    new_code.append(temp)
            with open(temp_dir/i["file"], 'w') as f:
                f.writelines(new_code)
            
            test_results, best = run_tests(config, i['id'], mode, env_session.interpreter.executable)
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
            for k, v in test_results.items():
                if k not in orig_results or orig_results[k] != v:
                    different = True
                    break
            if not different:
                print('Test is trivial')
                dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
                continue
            okay.append(i['id'])
        new_code = []
        cursor = CURSOR
        for l in range(len(code)):
            temp = code[l]
            for j in i['remove']:
                if j['description'] == 'imports':
                    continue
                if j['start_line'] - 1 <= l <= j['end_line'] - 1:
                    if j['start_line'] == j['end_line']:
                        temp = code[l][:j['start_column']] + (cursor if j['description'] != 'imports' else '') + code[l][j['end_column'] - 1:]
                    else:
                        if l == j['start_line'] - 1:
                            temp = code[l][:j['start_column']] + (cursor if j['description'] != 'imports' else '')
                        elif l == j['end_line'] - 1:
                            temp = code[l][j['end_column'] - 1:]
                        else:
                            temp = None
            if temp:
                new_code.append(temp)
        with open(temp_dir/i["file"], 'w') as f:
            f.writelines(new_code)
    # if len(okay) > 20:
    #     sample = random.sample(okay, 20)
    #     for id in okay:
    #         if id not in sample:
    #             dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{id}'))
    # else:
    #     sample = okay
    if len(okay) <= 21:
        sample = okay
    if mode == 'base':
        database = here/'experiment'/config['name']/'codeqldb'
        if not database.exists():
            dir_util.copy_tree(str(here/'CodeQLDBs'/config['name']/'codeql_db'), str(database/'..'/'codeqldb'))
        run_query(database, 'functionContext.ql', 'functionRes.csv', str(database/'..'))
        run_query(database, 'classContext.ql', 'classRes.csv', str(database/'..'))
    return env_session.interpreter.executable, orig_results, sample

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    print(prepare(config, args.mode))