import openai
from .utils import clip_prompt, postprocess

def completion(model, completor, context):
    prompt_size = 1500
    while True:
        try:
            comp = postprocess(completor.get_completion(model, clip_prompt('', context, prompt_size)))
            break
        except openai.error.InvalidRequestError:
            prompt_size -= 100
            continue
    return context, comp