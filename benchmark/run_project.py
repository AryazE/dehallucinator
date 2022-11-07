from pathlib import Path
import argparse
import json
from distutils import dir_util
from prepare_project import prepare
from run_completion import run_completion
from run_tests import run_tests

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--mode', type=str, required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    here = Path(__file__).parent
    try:
        dir_util.remove_tree(here/'experiment'/config['name'])
    except:
        pass
    prepare(config)
    for i in config["evaluations"]:
        run_completion(config, i["id"], args.mode)
        run_tests(config, i["id"])
