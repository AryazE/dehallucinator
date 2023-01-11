from .utils import clip_prompt

def completion(model, completor, context):
    return context, '', completor.get_completion(model, clip_prompt('', context, 1000))