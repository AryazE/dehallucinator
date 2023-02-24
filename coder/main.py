import argparse
from .backend import Completion
from . import baseline
from .simple import SimpleCompletion
from .explicit import ExplicitCompletion
from .cstSimple import CSTSimpleCompletion
from .docstring import DocstringCompletion
import logging
from pathlib import Path

def main(project_root: str, prompt: str, mode: str, 
        model: str, file: str, sLine: int, sCol: int, 
        eLine: int, eCol: int, output: str, log: str):
    logging.basicConfig(level=logging.INFO,filename=f'benchmark/{project_root.split("/")[-1]}-{mode}{log}.log', filemode='a')
    prompt = prompt.replace('\\n', '\n')
    prompt_lines = prompt.splitlines()
    prompt = '\n'.join([l for l in prompt_lines if not (l.strip().startswith('import ') or l.strip().startswith('from '))])
    completor = Completion()
    if mode == 'baseline':
        context, completion = baseline.completion(model, completor, prompt)
        with open(str(Path(project_root)/'..'/'..'/'artifact.md'), 'w') as f:
            f.write(f'prompt:\n```python\n{prompt}\n```\ncompletion:\n```python\n{completion}\n```\n')
    else:
        loc = {
            'file': file,
            'start_line': sLine,
            'start_column': sCol,
            'end_line': eLine,
            'end_column': eCol
        }
        if mode.startswith('simple'):
            completion_model = SimpleCompletion(project_root, model=model, location=loc)
        elif mode.startswith('cstSimple'):
            completion_model = CSTSimpleCompletion(project_root, model=model, location=loc)
        elif mode.startswith('explicit'):
            completion_model = ExplicitCompletion(project_root, model=model, location=loc)
        elif mode.startswith('docstring'):
            completion_model = DocstringCompletion(project_root, model=model, location=loc)
        else:
            raise ValueError(f'Unknown mode: {mode}')
        context, completion = completion_model.completion(completor, prompt)
    with open(output, 'w') as f:
        f.write(completion)
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