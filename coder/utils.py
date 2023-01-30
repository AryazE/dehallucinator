import subprocess
from typing import List
from os import path
import openai
from sentence_transformers import SentenceTransformer

similarity_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def embeddings(batch: List[str]) -> List[List[float]]:
    return similarity_model.encode(batch)

def clip_prompt(context: str, prompt: str, prompt_limit=500, alpha=0.5):
    '''
    Clip context from the beginning and prompt from the end 
    to fit in prompt_limit with ratio alpha:1-alpha (context:prompt).
    Return clipped prompt + clipped context.
    '''
    alpha = len(context) / (len(context) + len(prompt))
    if len(context) > 0:
        c_lines = context.splitlines()
        c_lines = c_lines[:int(len(c_lines)*prompt_limit*alpha*3/len(context))]
    else:
        c_lines = []
    if len(prompt) > 0:
        p_lines = prompt.splitlines()
        p_lines = p_lines[-int(len(p_lines)*prompt_limit*(1-alpha)*3/len(prompt)):]
    else:
        p_lines = []
    return '\n'.join(p_lines + c_lines)

def run_query(database, ql_file, res_file, tmp_dir, exclusion_file=None):
    if exclusion_file is None:
        with open(path.join(tmp_dir, 'empty.csv'), 'w') as f:
            f.write('')
        exclusion_file = path.join(tmp_dir, 'empty.csv')
    subprocess.run(['codeql', 'query', 'run',
        f'--database={database}',
        f'--external=dontLook={exclusion_file}',
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

def postprocess(code):
    if code.endswith('\n') or '\n' not in code:
        return code
    code = code[:code.rfind('\n')]
    if code.endswith(':'):
        code = code[:code.rfind('\n')]
    return code

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