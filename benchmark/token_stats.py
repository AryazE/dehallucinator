import numpy as np
from pathlib import Path
from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
here = Path(__file__).resolve().parent
with open(here/'repo_list.txt', 'r') as f:
    lines = f.read().splitlines()
total_tokens = 0
for line in lines:
    parts = line.split(' ')
    url = parts[0]
    owner = url.split('/')[-2]
    repo = url.split('/')[-1][:-4]
    files = [f for f in (here/'GitHubProjects'/f'{owner}_{repo}').glob('**/*.py') if f.is_file()]
    repo_tokens = []
    for f in files:
        with open(f, 'r') as f:
            code = f.readlines()
        tokens = 0
        for i in range(len(code)):
            if len(code[i]) > 2000:
                for j in code[i].split(' '):
                    tokens += len(tokenizer(j)['input_ids'])
            else:
                tokens += len(tokenizer(code[i])['input_ids'])
        # print(tokens)
        repo_tokens.append(tokens)
    large_files = [f for f in repo_tokens if f > 8001]
    tmp = np.array(repo_tokens)
    print(f'{owner}/{repo} {tmp.sum()} {tmp.mean()} {tmp.std()} {len(large_files)}')
    # print('-----------------')
    total_tokens += tmp.sum()
print(f'Total tokens: {total_tokens}')