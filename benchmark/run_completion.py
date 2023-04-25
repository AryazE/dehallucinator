import csv
import argparse
from pathlib import Path
import logging
import json
import re
import traceback
import Levenshtein
import libcst as cst
import libcst.matchers as matchers
from distutils import dir_util
from pygments.lexers.python import PythonLexer
from crystalbleu import corpus_bleu, SmoothingFunction
# from autoimport import fix_code
from coder.utils import clip_prompt, DELIMITER, dedent, equal_apis
from coder.main import main

API_regex = r'(?:\w+\.)*\w+\(.*\)'

PROMPT_LIMIT = 1750
logger = logging.getLogger(__name__)
sm_func = SmoothingFunction().method1

with open(Path(__file__).resolve().parent/'python_top_500.json') as f:
    content = json.load(f)
    trivially_shared_ngrams = {tuple(i[0]): i[1] for i in content}

def similarity_evaluation(ground_truth, completions):
    result = []
    # tok_ground_truth = [t[1] for t in PythonLexer().get_tokens(ground_truth)]
    # for i in range(len(completions)):
    #     tokenized = [t[1] for t in PythonLexer().get_tokens(completions[i])]
    #     result.append(corpus_bleu([[tok_ground_truth]], [tokenized], ignoring=trivially_shared_ngrams, smoothing_function=sm_func))
    # return result
    for i in range(len(completions)):
        result.append(Levenshtein.ratio(ground_truth, completions[i]))
    return result

def as_module(code: str) -> str:
    lines = code.splitlines(keepends=True)
    if len(lines) <= 1:
        return code
    if lines[0].startswith('if ') or lines[0].startswith('for ') or lines[0].startswith('while '):
        tmp = dedent(''.join(lines[1:])).splitlines(keepends=True)
        if not (tmp[0].startswith(' ') or tmp[0].startswith('\t')):
            return lines[0] + ''.join([('    ' + l) for l in tmp])
    return lines[0] + dedent(''.join(lines[1:]))

def as_statement(code: str) -> str:
    if len(code) == 0:
        return code
    lines = code.splitlines(True)
    ind = len(lines[0]) - len(lines[0].lstrip())
    curr = ''
    i = 0
    while i < len(lines):
        curr += lines[i][ind:]
        try:
            cst.parse_module(curr)
            break
        except cst.ParserSyntaxError:
            i += 1
    return curr

def filter_external(apis, project_apis):
    for node in apis:
        if matchers.matches(node, matchers.Call()):
            if matchers.matches(node.func, matchers.Name()):
                if node.func.value is None or node.func.value not in project_apis:
                    apis.remove(node)
            elif matchers.matches(node.func, matchers.Attribute()):
                if node.func.attr is None or node.func.attr.value not in project_apis:
                    apis.remove(node)
    return apis

def API_similarity(ground_truth, completions, project_apis):
    # try:
    #     # gt_apis = matchers.findall(cst.parse_module(as_module(ground_truth)), matchers.Call() | matchers.Attribute())
    #     gt_apis = matchers.findall(cst.parse_module(as_statement(ground_truth)), matchers.Call() | matchers.Attribute())
    #     gt_apis = filter_external(gt_apis, project_apis)
    # except Exception as e:
    #     gt_apis = []
    #     print(ground_truth)
    #     print(e)
    #     print(traceback.format_exc())
    
        # tmp_result = 0
        # try:
        #     # apis = matchers.findall(cst.parse_module(as_module(completions[i])), matchers.Call() | matchers.Attribute())
        #     apis = matchers.findall(cst.parse_module(as_statement(completions[i])), matchers.Call() | matchers.Attribute())
        #     apis = filter_external(apis, project_apis)
        # except Exception as e:
        #     apis = []
        #     print(completions[i])
        #     print(e)
        #     print(traceback.format_exc())
        # copy_apis = gt_apis.copy()
        # for api in apis:
        #     for ind in range(len(copy_apis)):
        #         if equal_apis(api, copy_apis[ind]): #api.deep_equals(gt_api):
        #             tmp_result += 1
        #             copy_apis.pop(ind)
        #             break
        # if tmp_result == 0:
        #     f1 = 0
        # else:
        #     recall = tmp_result / len(gt_apis)
        #     precision = tmp_result / len(apis)
        #     f1 = 2 * recall * precision / (recall + precision)
        # result.append(f1)
        
    gt_apis = re.findall(API_regex, ground_truth)
    completion_apis = [re.findall(API_regex, c) for c in completions]
    api_matches = []
    for i in range(len(completion_apis)):
        matches = 0
        for j in range(len(gt_apis)):
            if gt_apis[j] in completion_apis[i]:
                matches += 1
        api_matches.append(matches/len(gt_apis))
    return api_matches, len(gt_apis)

def run_completion(model, config, id, mode, log_suffix='', k=4, t=0.5, c=4, llm=None, llm_tok=None):
    global PROMPT_LIMIT
    here = Path(__file__).resolve().parent
    project_root = here/'experiment'/config["name"]/mode/f'temp{id}'/config['project_root']
    for x in config['evaluations']:
        if x['id'] == id:
            this = x
            break
    with open(project_root/this["file"]) as f:
        code = f.read()
    splited_code = code.split('<CURSOR>')
    if model == 'GPT3.5':
        PROMPT_LIMIT = 3500
    prompt = clip_prompt(splited_code[0], PROMPT_LIMIT)
    with open(here/config['project_root']/this["file"], 'r') as f:
        orig_code = f.read()
    ground_truth = orig_code[len(splited_code[0]):-len(splited_code[1])]
    with open(here/'experiment'/config["name"]/mode/f'temp{id}'/'gt.md', 'w') as f:
        f.write(f'prompt:\n```python\n{prompt}\n```\nground truth:\n```python\n{ground_truth}\n```\n')
    logger.info(f'Running completion for {config["name"]} {id} with prompt: \n{prompt}')
    main(str(project_root), prompt, mode, model, 
        func=this['function'],
        file=config["project_root"] + '/' + this["file"],
        sLine=int(this["remove"][0]["start_line"]),
        sCol=int(this["remove"][0]["start_column"]),
        eLine=int(this["remove"][0]["end_line"]),
        eCol=int(this["remove"][0]["end_column"]),
        output=str(project_root/f'completion.out'), log=log_suffix, k=k, t=t, c=c,
        llm=llm, llm_tok=llm_tok)
    with open(project_root/f'completion.out') as f:
        completions = f.read().split(DELIMITER)

    project_apis = set()
    with open(here/'experiment'/config["name"]/'functionRes.csv', newline='') as f:
        csv_reader = csv.DictReader(f)
        for line in csv_reader:
            project_apis.add(line['name'])
    token_similarity = similarity_evaluation(ground_truth, completions)
    api_similarity, n_apis = API_similarity(ground_truth, completions, project_apis)
    token_best = token_similarity.index(max(token_similarity))
    api_best = api_similarity.index(max(api_similarity))
    print(f'Best token similarity: {token_similarity} -> {token_best}')
    with open(here/'experiment'/config["name"]/mode/f'temp{id}'/'best.md', 'w') as f:
        f.write(f'N-gram similarity {token_similarity} from completion number {token_best}  \n'
                f'API similarity {api_similarity} from completion number {api_best} local APIs {n_apis} \n'
                f'prompt:\n```python\n{prompt}\n```\n'
                f'ground truth:\n```python\n{ground_truth}\n```\n'
                f'best n-gram:\n```python\n{completions[token_best]}\n```\n'
                f'best API:\n```python\n{completions[api_best]}\n```\n')
    
    with open(here/'experiment'/config["name"]/mode/f'temp{id}'/'res_numbers.txt', 'w') as f:
        for i in range(len(completions)):
            f.write(f'{token_similarity[i]} {api_similarity[i]}\n')
    for i in range(len(completions)):
        final_code = splited_code[0] + completions[i] + '\n' + splited_code[1]
        fixed_code = final_code #fix_code(final_code)
        dir_util.copy_tree(str(here/'experiment'/config["name"]/mode/f'temp{id}'), str(here/'experiment'/config["name"]/mode/f'temp{id}-{i}'))
        with open(here/'experiment'/config["name"]/mode/f'temp{id}-{i}'/config['project_root']/this["file"], 'w') as f:
            f.write(fixed_code)
    return completions
    # with open(project_root/f'completion.context') as f:
    #     context = f.read()
    # best_context = 0
    # possible_context = 0
    # if 'best_context' in this or 'possible_context' in this:
    #     for l in context.splitlines():
    #         best_temp = 0
    #         for c in this["best_context"]:
    #             if c in l and len(c) > best_temp:
    #                 best_temp = len(c)
    #         if best_temp > 0:
    #             best_context += 1
    #         best_temp = 0
    #         for c in this["possible_context"]:
    #             if c in l and len(c) > best_temp:
    #                 best_temp = len(c)
    #         if best_temp > 0:
    #             possible_context += 1
    #     return best_context, possible_context, len(context.splitlines())
    # return -1, -1, -1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='Codex')
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--mode', type=str, required=True)
    parser.add_argument('--log', type=str, default='')
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    bc, pc, l = run_completion(args.model, config, args.id, args.mode, args.log)
    print(f'Best context: {bc}, possible context: {pc}, total context: {l}')