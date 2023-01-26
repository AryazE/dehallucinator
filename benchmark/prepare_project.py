import argparse
import json
import os
import subprocess
from distutils import dir_util
from pathlib import Path
import venv
import virtualenv
from run_tests import run_tests
from coder.utils import run_query

CURSOR = '<CURSOR>'

def prepare(config, mode, ids=[]):
    global CURSOR

    here = Path(__file__).resolve().parent
    dir_util.mkpath(str(here/'experiment'/config['name']/mode))
    env_session = virtualenv.cli_run([str(here/'experiment'/config['name']/mode/'venv')])
    with open(str(here/'experiment'/config['name']/mode/'interpreter.txt'), 'w') as f:
        f.write(env_session.interpreter.executable)
    for i in config['evaluations']:
        if i['id'] > 0 and len(ids) > 0 and i['id'] not in ids:
            continue
        dir_util.mkpath(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
        temp_dir = here/'experiment'/config['name']/mode/f'temp{i["id"]}'/config['project_root']
        dir_util.copy_tree(str(here/config['project_root']), str(temp_dir))
        dir_util.remove_tree(str(temp_dir/'tests'))
        # os.remove(str(temp_dir/'setup.py'))
        if i['id'] == 0:
            orig_results = run_tests(config, 0, mode, env_session.interpreter.executable)
        if len(i['file']) == 0:
            continue
        exclude = []
        for j in i['remove']:
            exclude.append([i['file'], j['start_line'], j['start_column'], j['end_line'], j['end_column']])
        with open(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'/'exclude.csv'), 'w') as f:
            for j in exclude:
                f.write(','.join([str(k) for k in j]) + '\n')
        with open(temp_dir/i["file"]) as f:
            code = f.readlines()
        new_code = []
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
        test_results = run_tests(config, i['id'], mode, env_session.interpreter.executable)
        try:
            with open(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'/'checkTest.txt'), 'r') as f:
                content = f.read()
        except:
            dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
            continue
        if content != 'here':
            dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
            continue
        different = False
        for k, v in test_results.items():
            if k not in orig_results or orig_results[k] != v:
                different = True
                break
        if not different:
            dir_util.remove_tree(str(here/'experiment'/config['name']/mode/f'temp{i["id"]}'))
            continue
        database = temp_dir/'..'/'..'/'codeqldb'
        working_dir = os.getcwd()
        os.chdir(str(temp_dir))
        subprocess.run(['codeql', 'database', 'create',
                        '--language=python',
                        '--overwrite',
                        '--threads=0',
                        '--', str(database)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir(working_dir)
        run_query(database, 'functionContext.ql', 'functionRes.csv', str(database/'..'), str(database/'..'/'exclude.csv'))
        run_query(database, 'classContext.ql', 'classRes.csv', str(database/'..'), str(database/'..'/'exclude.csv'))
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
    return env_session.interpreter.executable, orig_results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    print(prepare(config, args.mode))