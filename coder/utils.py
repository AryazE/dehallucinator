import subprocess
from typing import List
from os import path
import ast
import re
from numpy import dot
from numpy.linalg import norm
import libcst as cst
import libcst.matchers as matchers
import openai
from sentence_transformers import SentenceTransformer
from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

similarity_model = SentenceTransformer('flax-sentence-embeddings/st-codesearch-distilroberta-base')

def embeddings(batch: List[str]) -> List[List[float]]:
    return similarity_model.encode(batch, show_progress_bar=False)

def clip_prompt(prompt: str, prompt_limit=1500):
    '''
    Clip prompt from the beginning to fit in prompt_limit.
    '''
    prompt_lines = prompt.splitlines(keepends=True)
    tokenized = 0
    for prompt_line in prompt_lines:
        tokenized += len(tokenizer(prompt_line)['input_ids'])
    if tokenized > prompt_limit:
        new_len_prompt = len(prompt_lines) * prompt_limit / tokenized
        prompt = ''.join(prompt_lines[-int(new_len_prompt):])
    return prompt

def run_query(database, ql_file, res_file, tmp_dir):
    subprocess.run(['codeql', 'query', 'run',
        f'--database={database}',
        f'--output={path.join(tmp_dir, res_file.split(".")[0] + ".bqrs")}',
        '--', f'{path.join(path.dirname(__file__), "ql", ql_file)}'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['codeql', 'bqrs', 'decode',
        '--format=csv',
        f'--output={path.join(tmp_dir, res_file)}',
        '--result-set=#select',
        '--', f'{path.join(tmp_dir, res_file.split(".")[0] + ".bqrs")}'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def same_location(line, location):
    if len(location['file']) == 0:
        return False
    for i in ['start_line', 'end_line', 'start_column', 'end_column']:
        if location[i] == -1:
            return False
    line_parts = line['file'].split('/')
    location_parts = location['file'].split('/')
    if line_parts[-2:] != location_parts[-2:]:
        return False
    if int(line['start_line']) > location['end_line']:
        return False
    if int(line['end_line']) < location['start_line']-10:
        return False
    if int(line['start_line']) == location['end_line'] and int(line['start_column']) > location['end_column']:
        return False
    if int(line['end_line']) == location['start_line'] and int(line['end_column']) < location['start_column']:
        return False
    return True

def postprocess(code, indent_style='\t', indent_count=0, mode = ''):
    if mode.endswith('l') or mode.endswith('line'):
        return code.splitlines(True)[0]
    elif mode.endswith('api'):
        bracket = 0
        res = 0
        i = 0
        while i < len(code):
            ch = code[i]
            res += 1
            if ch == '#':
                while i < len(code) and code[i] != '\n':
                    i += 1
                res = i
            elif ch == '(':
                bracket += 1
            elif ch == ')':
                bracket -= 1
            elif ch == '\n':
                if bracket == 0:
                    break
            i += 1
        return code[:res]
    if '\n' not in code or code.endswith('\n'):
        return code
    prefix = (indent_style * indent_count) + 'def foo():\n' + (indent_style * (indent_count+1))
    extra = len(indent_style) * indent_count
    code = prefix + code
    temp_lines = code.splitlines()
    for l in range(1, len(temp_lines)):
        if (len(temp_lines[l]) - len(temp_lines[l].lstrip())) // len(indent_style) <= indent_count:
            temp_lines = temp_lines[:l]
            break
    lines = [l[extra:] for l in temp_lines]
    while len(lines) > 1:
        try:
            ast.parse('\n'.join(lines))
            return lines[1][len(indent_style):] + '\n' + '\n'.join([(indent_style * indent_count)+l for l in lines[2:]])
        except:
            lines.pop()
    return ''

def get_completion_safely(model: str, completor, prompt, k=4):
        if model == 'GPT3.5':
            prompt_size = 3500
        else:
            prompt_size = 1750
        clipped_prompt = prompt
        while prompt_size > 0:
            clipped_prompt = clip_prompt(clipped_prompt, prompt_size)
            try:
                completion = completor.get_completion(model, clipped_prompt, k=k)
                break
            except openai.error.InvalidRequestError as e:
                print(e)
                prompt_size -= 10
                continue
            except Exception as e:
                print(e)
                prompt_size -= 10
                continue
        return completion

def dedent(code):
    lines = code.splitlines(keepends=True)
    indents = [re.match('^\s*', i).group(0) for i in lines]
    indent_style = ' '*100
    indent_count = 10000
    for i in range(len(indents)):
        if len(indents[i]) > 0 and len(indent_style) > len(indents[i]) and '\n' not in indents[i]:
            indent_style = indents[i]
    for i in range(1, len(indents)):
        if len(lines[i]) - len(indents[i]) == 0 or len(lines[i-1]) - len(indents[i-1]) == 0:
            continue
        if len(lines[i-1]) > 0 and len(indents[i]) > len(indents[i - 1]) and not re.match('^\s*#', lines[i]) and not re.match('^\s*#', lines[i-1]):
            if len(indent_style) > len(indents[i][len(indents[i - 1]):]) and '\n' not in indents[i]:
                indent_style = indents[i][len(indents[i - 1]):]
        elif len(lines[i]) > 0 and len(indents[i]) < len(indents[i - 1]) and not re.match('^\s*#', lines[i]) and not re.match('^\s*#', lines[i-1]):
            if len(indent_style) > len(indents[i-1][len(indents[i]):]) and '\n' not in indents[i-1]:
                indent_style = indents[i-1][len(indents[i]):]
    for i in range(len(indents)):
        if '\n' not in indents[i]:
            indent_count = min(indent_count, len(indents[i]) // len(indent_style))
    return ''.join([l[len(indent_style)*indent_count:] for l in lines])

def get_indentation(prompt):
    if len(prompt) == 0:
        return '', 0
    lines = prompt.splitlines()
    indents = [re.match('^\s*', i).group(0) for i in lines]
    indent_style = ' '*100
    indent_count = 0
    for i in range(1, len(indents)):
        if len(indents[i]) > 0 and len(indent_style) > len(indents[i]):
            indent_style = indents[i]
    for i in range(1, len(indents)):
        if len(lines[i-1]) > 0 and len(indents[i]) > len(indents[i - 1]) and not re.match('^\s*#', lines[i]) and not re.match('^\s*#', lines[i-1]):
            if len(indent_style) > len(indents[i][len(indents[i - 1]):]):
                indent_style = indents[i][len(indents[i - 1]):]
        elif len(lines[i]) > 0 and len(indents[i]) < len(indents[i - 1]) and not re.match('^\s*#', lines[i]) and not re.match('^\s*#', lines[i-1]):
            if len(indent_style) > len(indents[i-1][len(indents[i]):]):
                indent_style = indents[i-1][len(indents[i]):]
    indent_count = len(indents[-1]) // len(indent_style) - 1
    return indent_style, indent_count

def cos_sim(emb_a: List[float], emb_b: List[float]) -> float:
    return dot(emb_a, emb_b) / (norm(emb_a) * norm(emb_b))

def merge(project_root: str, file: str) -> str:
    p_r = project_root.split('/')
    f = file.split('/')
    max_common = 0
    for i in range(1, min(len(p_r), len(f))):
        if '/'.join(p_r[-i:]) == '/'.join(f[:i]):
            max_common = i
    return '/'.join(p_r[:-max_common] + f)

DELIMITER = '--------=======DiCoder=======--------'

def equal_apis(a: cst.CSTNode, b: cst.CSTNode) -> bool:
    if (matchers.matches(a, matchers.Call()) and matchers.matches(b, matchers.Call())):
        if (matchers.matches(a.func, matchers.Attribute()) and matchers.matches(b.func, matchers.Attribute())):
            result = a.func.attr.deep_equals(b.func.attr)
        elif (matchers.matches(a.func, matchers.Name()) and matchers.matches(b.func, matchers.Name())):
            result = a.func.value == b.func.value
        else:
            result = a.func.deep_equals(b.func)
        if not result:
            return False
        if len(a.args) != len(b.args):
            return False
        comparison = lambda x: x.keyword.value if x.keyword is not None else ''
        a_args = sorted(a.args, key=comparison)
        b_args = sorted(b.args, key=comparison)
        for i in range(len(a_args)):
            if type(a_args[i].value) is not type(b_args[i].value):
                return False
        return True
    elif (matchers.matches(a, matchers.Attribute()) and matchers.matches(b, matchers.Attribute())):
        return a.attr.deep_equals(b.attr)
    return False