from .utils import clip_prompt

def completion(completor, context):
    return context, '', completor.get_completion('Codex', clip_prompt('', context, 1000))