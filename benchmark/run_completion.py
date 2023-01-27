import argparse
from pathlib import Path
import logging
import json
# from autoimport import fix_code
from coder.utils import clip_prompt
from coder.main import main

PROMPT_LIMIT = 1200
logger = logging.getLogger(__name__)

def run_completion(model, config, id, mode, log_suffix=''):
    global PROMPT_LIMIT
    here = Path(__file__).resolve().parent
    project_root = here/'experiment'/config["name"]/mode/f'temp{id}'/config['project_root']
    with open(project_root/config["evaluations"][id]["file"]) as f:
        code = f.read()
    splited_code = code.split('<CURSOR>')
    prompt = clip_prompt('', splited_code[0], PROMPT_LIMIT)
    logger.info(f'Running completion for {config["name"]} {id} with prompt: \n{prompt}')
    main(str(project_root), prompt, mode, model, 
        file=config["project_root"] + '/' + config["evaluations"][id]["file"],
        sLine=int(config["evaluations"][id]["remove"][0]["start_line"]),
        sCol=int(config["evaluations"][id]["remove"][0]["start_column"]),
        eLine=int(config["evaluations"][id]["remove"][0]["end_line"]),
        eCol=int(config["evaluations"][id]["remove"][0]["end_column"]),
        output=str(project_root/f'completion.out'), log=log_suffix)
    with open(project_root/f'completion.out') as f:
        completion = f.read()
    final_code = splited_code[0] + completion + '\n' + splited_code[1]
    fixed_code = final_code #fix_code(final_code)
    with open(project_root/config["evaluations"][id]["file"], 'w') as f:
        f.write(fixed_code)
    with open(project_root/f'completion.context') as f:
        context = f.read()
    best_context = 0
    possible_context = 0
    if 'best_context' in config["evaluations"][id] or 'possible_context' in config["evaluations"][id]:
        for l in context.splitlines():
            best_temp = 0
            for c in config["evaluations"][id]["best_context"]:
                if c in l and len(c) > best_temp:
                    best_temp = len(c)
            if best_temp > 0:
                best_context += 1
            best_temp = 0
            for c in config["evaluations"][id]["possible_context"]:
                if c in l and len(c) > best_temp:
                    best_temp = len(c)
            if best_temp > 0:
                possible_context += 1
        return best_context, possible_context, len(context.splitlines())
    return -1, -1, -1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='Codex')
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--mode', type=str, required=True)
    parser.add_argument('--log', type=str, default='')
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = json.load(f)
    bc, pc, l = run_completion(args.model, config, args.id, args.mode, args.log)
    print(f'Best context: {bc}, possible context: {pc}, total context: {l}')