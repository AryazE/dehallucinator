import logging
from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained('gpt2')

def clip_prompt(prompt, prompt_limit=500):
    global tokenizer
    tokens = tokenizer(prompt)['input_ids']
    logging.debug(f'Prompt length: {len(tokens)}')
    lines = prompt.splitlines()
    if len(tokens) > prompt_limit:
        lines = lines[-int(len(lines)*prompt_limit/len(tokens)):]
    return '\n'.join(lines)