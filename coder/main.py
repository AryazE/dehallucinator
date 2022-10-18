import argparse
import coder.baseline as baseline
from coder.simple import SimpleCompletion

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=str, required=True)
    parser.add_argument("--important-files", nargs='+', required=True)
    parser.add_argument("--file", type=str, required=True)
    parser.add_argument("--context", help="The context to complete", type=str)
    args = parser.parse_args()
    simple_completion = SimpleCompletion(args.project_root, args.important_files)
    print(simple_completion.completion(args.context, args.file))