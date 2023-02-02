import subprocess
from typing import List
from os import path
import ast
import re
from numpy import dot
from numpy.linalg import norm
import openai
from sentence_transformers import SentenceTransformer

similarity_model = SentenceTransformer('flax-sentence-embeddings/st-codesearch-distilroberta-base')

def embeddings(batch: List[str]) -> List[List[float]]:
    return similarity_model.encode(batch, show_progress_bar=False)

def clip_prompt(context: str, prompt: str, prompt_limit=500, alpha=0.5):
    '''
    Clip context from the beginning and prompt from the end 
    to fit in prompt_limit with ratio alpha:1-alpha (context:prompt).
    Return clipped prompt + clipped context.
    '''
    alpha = len(context) / (len(context) + len(prompt))
    if len(context) > 0:
        c_lines = context.splitlines()
        c_lines = c_lines[:min(16, int(len(c_lines)*prompt_limit*alpha*3/len(context)))]
    else:
        c_lines = []
    if len(prompt) > 0:
        p_lines = prompt.splitlines()
        p_lines = p_lines[-int(len(p_lines)*prompt_limit*(1-alpha)*3/len(prompt)):]
    else:
        p_lines = []
    return '\n'.join(p_lines + c_lines)

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
    if not line['file'].endswith(location['file']):
        return False
    if int(line['start_line']) > location['end_line']:
        return False
    if int(line['end_line']) < location['start_line']:
        return False
    if int(line['start_line']) == location['end_line'] and int(line['start_column']) > location['end_column']:
        return False
    if int(line['end_line']) == location['start_line'] and int(line['end_column']) < location['start_column']:
        return False
    return True

def postprocess(code, indent_style='\t', indent_count=0):
    if '\n' not in code or code.endswith('\n'):
        return code
    prefix = (indent_style * indent_count) + 'def foo():\n' + (indent_style * (indent_count+1))
    extra = len(indent_style) * indent_count
    code = prefix + code
    temp_lines = code.splitlines()
    lines = [l[extra:] for l in temp_lines]
    while len(lines) > 1:
        try:
            ast.parse('\n'.join(lines))
            return lines[1][len(indent_style):] + '\n' + '\n'.join([(indent_style * indent_count)+l for l in lines[2:]])
        except:
            lines.pop()
    return ''

def get_completion_safely(model, completor, context, prompt):
        prompt_size = 1500
        while prompt_size > 0:
            try:
                completion = completor.get_completion(model, clip_prompt(context, prompt, prompt_size))
                break
            except openai.error.InvalidRequestError as e:
                print(e)
                prompt_size -= 100
                continue
            except Exception as e:
                print(e)
                prompt_size -= 100
                continue
        return completion

def get_indentation(prompt):
    lines = prompt.splitlines()
    indents = [re.match('^\s*', i).group(0) for i in lines]
    indent_style = ''
    indent_count = 0
    for i in range(1, len(indents)):
        if len(lines[i-1]) > 0 and len(indents[i]) > len(indents[i - 1]) and not re.match('^\s*#', lines[i]) and not re.match('^\s*#', lines[i-1]):
            indent_style = indents[i][len(indents[i - 1]):]
            break
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