import argparse
import logging
from coder.backend import Completion
import coder.baseline as baseline
from coder.simple import SimpleCompletion

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='baseline', help='baseline or simple')
    parser.add_argument("--project-root", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--imports", type=str, required=True)
    parser.add_argument("--prompt", help="The context to complete", type=str)
    parser.add_argument("--file", help="The file path", type=str, default='')
    parser.add_argument("--sLine", help="The start line number of the cursor", type=int, default=-1)
    parser.add_argument("--sCol", help="The start column number of the cursor", type=int, default=-1)
    parser.add_argument("--eLine", help="The end line number of the cursor", type=int, default=-1)
    parser.add_argument("--eCol", help="The end column number of the cursor", type=int, default=-1)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,filename=f'benchmark/{args.project_root.split("/")[-1]}-{args.mode}.log', filemode='a')
    prompt = args.prompt.replace('\\n', '\n')
    prompt_lines = prompt.splitlines()
    prompt = '\n'.join([l for l in prompt_lines if not (l.strip().startswith('import ') or l.strip().startswith('from '))])
    completor = Completion()
    if args.mode == 'baseline':
        imports, completion = baseline.completion(completor, prompt)
    else:
        loc = {
            'file': args.file,
            'start_line': args.sLine,
            'start_column': args.sCol,
            'end_line': args.eLine,
            'end_column': args.eCol
        }
        simple_completion = SimpleCompletion(args.project_root, model='Codex', location=loc)
        imports, completion = simple_completion.completion(completor, prompt)
    with open(args.output, 'w') as f:
        f.write(completion)
    with open(args.imports, 'w') as f:
        f.write(imports)