import argparse
import coder.baseline as baseline
from coder.simple import SimpleCompletion

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='baseline', help='baseline or simple')
    parser.add_argument("--project-root", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--prompt", help="The context to complete", type=str)
    args = parser.parse_args()
    prompt = args.prompt.replace('\\n', '\n')
    if args.mode == 'baseline':
        completion = baseline.completion(prompt)
    else:
        simple_completion = SimpleCompletion(args.project_root)
        completion = simple_completion.completion(prompt)
    with open(args.output, 'w') as f:
        f.write(completion)