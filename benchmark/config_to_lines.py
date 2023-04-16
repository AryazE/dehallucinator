import argparse
import json
from copy import deepcopy

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    args = parser.parse_args()
    with open(args.config) as f:
        config = json.load(f)
    new_config = deepcopy(config)
    new_config['evaluations'] = []
    for e in config['evaluations']:
        if e['id'] == 0:
            new_config['evaluations'].append(e)
            continue
        j = 0
        for i in range(e['start_line'], e['end_line'] + 1):
            new_config['evaluations'].append({
                'id': e['id']+j,
                'file': e['file'],
                'function': e['function'],
                'remove': [{
                    'description': 'code',
                    'start_line': i,
                    'end_line': i+1,
                    'start_column': e['start_column'],
                    'end_column': 1
                }]
            })
            j += 1
    with open(args.config[:-5] + '-lines.json', 'w') as f:
        json.dump(new_config, f, indent=2)