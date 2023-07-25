from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModel
from nltk import edit_distance
from pathlib import Path
import random
import json
import re
from coder.utils import find_apis

tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen25-7b-mono", trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen25-7b-mono", device_map='auto', load_in_4bit=True)

def truncate(prompt):
    prompt_limit = 1500
    prompt_lines = prompt.splitlines(keepends=True)
    tokenized = 0
    for prompt_line in prompt_lines:
        tokenized += len(tokenizer(prompt_line)['input_ids'])
    if tokenized > prompt_limit:
        new_len_prompt = len(prompt_lines) * prompt_limit / tokenized
        prompt = ''.join(prompt_lines[-int(new_len_prompt):])
    return prompt

def measure(gt, comp):
    # API_regex = r'(?=((?:\w+\.)*\w+\(.*\)))'
    # gt_apis = re.findall(API_regex, gt)
    gt_apis = find_apis(gt)
    if len(gt_apis) == 0:
        return 0, 0
    # completion_apis = re.findall(API_regex, comp)
    completion_apis = find_apis(comp)
    matches = 0
    for j in range(len(gt_apis)):
        if gt_apis[j] in completion_apis:
            matches += 1
    api_matches = matches/len(gt_apis)
    a = tokenizer(gt)['input_ids']
    b = tokenizer(comp)['input_ids']
    return 1 - edit_distance(a, b) / max(len(a), len(b)), api_matches

def evaluate(config):
    CURSOR = '<CURSOR>'
    results = []
    codes = []
    evals = config['evaluations'][0:1]#[1:]
    if len(evals) > 10:
        evals = random.sample(evals, 10)
    for i in evals:
        with open(here/config["project_root"]/i["file"], "r") as f:
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
        pre_context = truncate(pre_context)
        inputs = tokenizer(pre_context, return_tensors="pt").to('cuda')
        sample = model.generate(**inputs, max_new_tokens=256)
        completion = tokenizer.decode(sample[0][inputs.input_ids.shape[1]:], truncate_before_pattern=["\n\n\n", "def ", "class "])
        # bracket = 0
        # res = 0
        # i = 0
        # while i < len(completion):
        #     ch = completion[i]
        #     res += 1
        #     if ch == '#':
        #         while i < len(completion) and completion[i] != '\n':
        #             i += 1
        #         res = i
        #     elif ch == '(':
        #         bracket += 1
        #     elif ch == ')':
        #         bracket -= 1
        #     elif ch == '\n':
        #         if bracket == 0:
        #             break
        #     i += 1
        # final_completion = completion[:res]
        # if '\n' not in completion or completion.endswith('\n'):
        #     final_completion = completion
        final_completion = completion
        codes.append((i["id"], pre_context, ground_truth, completion))
        # results.append((config["name"], *measure(ground_truth, final_completion)))
    return results, codes

if __name__ == "__main__":
    here = Path(__file__).parent.resolve()
    with open(here/"repo_list_3.txt", "r") as f:
        repos = [r.split(" ")[0][19:-4].replace("/", "_") for r in f.read().split("\n")]
    # (here/"preliminary_study").mkdir()
    for repo in repos:
        with open(here/"benchmark_configs"/f"{repo}.json", "r") as f:
            config = json.load(f)
        results, codes = evaluate(config)
        # (here/"preliminary_study"/repo).mkdir()
        for (_id, prompt, gt, comp) in codes:
            report = f"{_id}:\nPrompt:\n```python\n{prompt}\n```\nCompletion:\n```python\n{comp}\n```\nGround truth:\n```python\n{gt}\n```\n"
            with open(here/"preliminary_study"/repo/f"{_id}.md", "w") as f:
                f.write(report)
        # with open(here/"study_results.csv", "a") as f:
        #     f.write("\n".join([f"{r[0]}, {r[1]}, {r[2]}" for r in results]) + "\n")