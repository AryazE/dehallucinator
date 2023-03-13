import argparse
from pathlib import Path
import logging
import json
import traceback
import libcst as cst
import libcst.matchers as matchers
from distutils import dir_util
from pygments.lexers.python import PythonLexer
from crystalbleu import corpus_bleu
# from autoimport import fix_code
from coder.utils import clip_prompt, DELIMITER, dedent, equal_apis
from coder.main import main

PROMPT_LIMIT = 1500
logger = logging.getLogger(__name__)

with open(Path(__file__).resolve().parent/'python_top_500.json') as f:
    content = json.load(f)
    trivially_shared_ngrams = {tuple(i[0]): i[1] for i in content}

def similarity_evaluation(ground_truth, completions):
    result = 0
    best = 0
    tok_ground_truth = [t[1] for t in PythonLexer().get_tokens(ground_truth)]
    for i in range(len(completions)):
        tokenized = [t[1] for t in PythonLexer().get_tokens(completions[i])]
        tmp_result = corpus_bleu([[tok_ground_truth]], [tokenized], ignoring=trivially_shared_ngrams)
        if tmp_result > result:
            result = tmp_result
            best = i
    return result, best

def as_module(code: str) -> str:
    lines = code.splitlines(keepends=True)
    if len(lines) <= 1:
        return code
    return lines[0] + dedent(''.join(lines[1:]))

def API_similarity(ground_truth, completions):
    result = 0
    best = 0
    try:
        gt_apis = matchers.findall(cst.parse_module(as_module(ground_truth)), matchers.Call() | matchers.Attribute())
    except Exception as e:
        gt_apis = []
        print(ground_truth)
        print(e)
        print(traceback.format_exc())
    for i in range(len(completions)):
        tmp_result = 0
        try:
            apis = matchers.findall(cst.parse_module(as_module(completions[i])), matchers.Call() | matchers.Attribute())
        except Exception as e:
            apis = []
            print(completions[i])
            print(e)
            print(traceback.format_exc())
        for api in apis:
            for gt_api in gt_apis:
                if equal_apis(api, gt_api): #api.deep_equals(gt_api):
                    tmp_result += 1
        if tmp_result == 0:
            f1 = 0
        else:
            recall = tmp_result / len(gt_apis)
            precision = tmp_result / len(apis)
            f1 = 2 * recall * precision / (recall + precision)
        if f1 > result:
            result = f1
            best = i
    return result, best

def run_completion(model, config, id, mode, log_suffix=''):
    global PROMPT_LIMIT
    here = Path(__file__).resolve().parent
    project_root = here/'experiment'/config["name"]/mode/f'temp{id}'/config['project_root']
    with open(project_root/config["evaluations"][id]["file"]) as f:
        code = f.read()
    splited_code = code.split('<CURSOR>')
    prompt = clip_prompt(splited_code[0], PROMPT_LIMIT)
    with open(here/config['project_root']/config["evaluations"][id]["file"], 'r') as f:
        orig_code = f.read()
    ground_truth = orig_code[len(splited_code[0]):-len(splited_code[1])]
    with open(here/'experiment'/config["name"]/mode/f'temp{id}'/'gt.md', 'w') as f:
        f.write(f'prompt:\n```python\n{prompt}\n```\nground truth:\n```python\n{ground_truth}\n```\n')
    logger.info(f'Running completion for {config["name"]} {id} with prompt: \n{prompt}')
    main(str(project_root), prompt, mode, model, 
        file=config["project_root"] + '/' + config["evaluations"][id]["file"],
        sLine=int(config["evaluations"][id]["remove"][0]["start_line"]),
        sCol=int(config["evaluations"][id]["remove"][0]["start_column"]),
        eLine=int(config["evaluations"][id]["remove"][0]["end_line"]),
        eCol=int(config["evaluations"][id]["remove"][0]["end_column"]),
        output=str(project_root/f'completion.out'), log=log_suffix)
    with open(project_root/f'completion.out') as f:
        completions = f.read().split(DELIMITER)

    token_similarity, token_best = similarity_evaluation(ground_truth, completions)
    api_similarity, api_best = API_similarity(ground_truth, completions)
    print(f'Best token similarity: {token_similarity} -> {token_best}')
    with open(here/'experiment'/config["name"]/mode/f'temp{id}'/'best.md', 'w') as f:
        f.write(f'N-gram similarity {token_similarity} from completion number {token_best}  \n'
                f'API similarity {api_similarity} from completion number {api_best}  \n'
                f'prompt:\n```python\n{prompt}\n```\n'
                f'ground truth:\n```python\n{ground_truth}\n```\n'
                f'best n-gram:\n```python\n{completions[token_best]}\n```\n'
                f'best API:\n```python\n{completions[api_best]}\n```\n')
    
    for i in range(len(completions)):
        final_code = splited_code[0] + completions[i] + '\n' + splited_code[1]
        fixed_code = final_code #fix_code(final_code)
        dir_util.copy_tree(str(here/'experiment'/config["name"]/mode/f'temp{id}'), str(here/'experiment'/config["name"]/mode/f'temp{id}-{i}'))
        with open(here/'experiment'/config["name"]/mode/f'temp{id}-{i}'/config['project_root']/config["evaluations"][id]["file"], 'w') as f:
            f.write(fixed_code)
    return completions
    # with open(project_root/f'completion.context') as f:
    #     context = f.read()
    # best_context = 0
    # possible_context = 0
    # if 'best_context' in config["evaluations"][id] or 'possible_context' in config["evaluations"][id]:
    #     for l in context.splitlines():
    #         best_temp = 0
    #         for c in config["evaluations"][id]["best_context"]:
    #             if c in l and len(c) > best_temp:
    #                 best_temp = len(c)
    #         if best_temp > 0:
    #             best_context += 1
    #         best_temp = 0
    #         for c in config["evaluations"][id]["possible_context"]:
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