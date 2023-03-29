import argparse
from .backend import Completion
from . import baseline
from .utils import DELIMITER
from .simple import SimpleCompletion
from .explicit import ExplicitCompletion
from .cstSimple import CSTSimpleCompletion
from .docstring import DocstringCompletion
from .swSim import SWSim
import logging
from pathlib import Path

def is_local_import(line: str, file: str) -> bool:
    l = line.strip()
    if not l.startswith('import ') and not l.startswith('from '):
        return False
    if l.startswith('import .') or l.startswith('from .'):
        return True
    possible_pkgs = file.split('/')
    for pkg in possible_pkgs:
        if l.startswith(f'import {pkg}') or l.startswith(f'from {pkg}'):
            return True
    return False

def main(project_root: str, prompt: str, mode: str, 
        model: str, func: str, file: str, sLine: int, sCol: int, 
        eLine: int, eCol: int, output: str, log: str, k=4, t=0.5, c=4):
    logging.basicConfig(level=logging.INFO,filename=f'benchmark/{project_root.split("/")[-1]}-{mode}{log}.log', filemode='a')
    # prompt = prompt.replace('\\n', '\n')
    prompt_lines = prompt.splitlines()
    prompt = '\n'.join([l for l in prompt_lines if not is_local_import(l, file)])
    completor = Completion()
    if mode.startswith('baseline'):
        context, completions = baseline.completion(model, completor, prompt, k=k)
        with open(str(Path(project_root)/'..'/'..'/'artifact.md'), 'w') as f:
            f.write(f'prompt:\n```python\n{prompt}\n```\ncompletion:\n```python\n{DELIMITER.join(completions)}\n```\n')
    else:
        loc = {
            'file': file,
            'start_line': sLine,
            'start_column': sCol,
            'end_line': eLine,
            'end_column': eCol
        }
        if mode.startswith('simple'):
            completion_model = SimpleCompletion(project_root, model=model, location=loc, t=t, c=c)
        elif mode.startswith('cstSimple'):
            completion_model = CSTSimpleCompletion(project_root, model=model, location=loc, t=t, c=c)
        elif mode.startswith('explicit'):
            completion_model = ExplicitCompletion(project_root, model=model, location=loc, t=t, c=c)
        elif mode.startswith('docstring'):
            completion_model = DocstringCompletion(project_root, model=model, func=func, location=loc, t=t, c=c)
        elif mode.startswith('sw'):
            completion_model = SWSim(project_root, model=model, func=func, location=loc, similarity_threshold=t)
        else:
            raise ValueError(f'Unknown mode: {mode}')
        context, completions = completion_model.completion(completor, prompt, k=k)
    with open(output, 'w') as f:
        f.write(DELIMITER.join(completions))
    with open(output.split('.')[0] + '.context', 'w') as f:
        f.write(context)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='baseline', help='baseline or simple')
    parser.add_argument('--model', type=str, default='Codex', help='CodeGen or Codex')
    parser.add_argument("--project-root", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--prompt", help="The context to complete", type=str)
    parser.add_argument("--file", help="The file path", type=str, default='')
    parser.add_argument("--sLine", help="The start line number of the cursor", type=int, default=-1)
    parser.add_argument("--sCol", help="The start column number of the cursor", type=int, default=-1)
    parser.add_argument("--eLine", help="The end line number of the cursor", type=int, default=-1)
    parser.add_argument("--eCol", help="The end column number of the cursor", type=int, default=-1)
    parser.add_argument("--log", help="The log file suffix", type=str, default='')
    args = parser.parse_args()
    main(args.project_root, args.prompt, args.mode, args.model, args.file, args.sLine, args.sCol, args.eLine, args.eCol, args.output, args.log)