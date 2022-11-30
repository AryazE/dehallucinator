import logging
import subprocess
from os import path
from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained('gpt2')

def clip_prompt(prompt, prompt_limit=500):
    global tokenizer
    tokens = tokenizer(prompt)['input_ids']
    logging.debug(f'Prompt length: {len(tokens)}')
    lines = prompt.splitlines()
    if len(tokens) > prompt_limit:
        lines = lines[-int(len(lines)*prompt_limit/len(tokens)):]
    return '\n'.join(lines)

def run_query(database, ql_file, res_file, tmp_dir):
    subprocess.run(['codeql', 'query', 'run',
        f'--database={database}',
        f'--output={path.join(tmp_dir, res_file.split(".")[0] + ".bqrs")}',
        '--', f'{path.join(path.dirname(__file__), "ql", ql_file)}'], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['codeql', 'bqrs', 'decode',
        '--format=csv',
        '--no-titles',
        f'--output={path.join(tmp_dir, res_file)}',
        '--result-set=#select',
        '--', f'{path.join(tmp_dir, res_file.split(".")[0] + ".bqrs")}'], check=True, stdout=subprocess.DEVNULL)