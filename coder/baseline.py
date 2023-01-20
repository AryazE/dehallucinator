from .utils import clip_prompt, postprocess

def completion(model, completor, context):
    comp = postprocess(completor.get_completion(model, clip_prompt('', context, 1500)))
    return context, comp