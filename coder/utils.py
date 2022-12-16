import subprocess
from os import path

def clip_prompt(prompt, prompt_limit=500):
    lines = prompt.splitlines()
    if len(prompt)/3 > prompt_limit:
        lines = lines[-int(len(lines)*prompt_limit*3/len(prompt)):]
    return '\n'.join(lines)

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