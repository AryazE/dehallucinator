import argparse
from coder.backend import get_completion

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("context", help="The context to complete", type=str)
    args = parser.parse_args()
    print(get_completion(args.context))