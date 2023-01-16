import argparse
from coder.backend import Completion
import coder.baseline as baseline
from coder.simple import SimpleCompletion
import logging

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
    logging.basicConfig(level=logging.INFO,filename=f'benchmark/{args.project_root.split("/")[-1]}-{args.mode}{args.log}.log', filemode='a')
    prompt = args.prompt.replace('\\n', '\n')
    prompt_lines = prompt.splitlines()
    prompt = '\n'.join([l for l in prompt_lines if not (l.strip().startswith('import ') or l.strip().startswith('from '))])
    completor = Completion()
    if args.mode == 'baseline':
        context, completion = baseline.completion(args.model, completor, prompt)
    else:
        loc = {
            'file': args.file,
            'start_line': args.sLine,
            'start_column': args.sCol,
            'end_line': args.eLine,
            'end_column': args.eCol
        }
        simple_completion = SimpleCompletion(args.project_root, model=args.model, location=loc)
        context, completion = simple_completion.completion(completor, prompt)
    with open(args.output, 'w') as f:
        f.write(completion)
    with open(args.output.split('.')[0] + '.context', 'w') as f:
        f.write(context)