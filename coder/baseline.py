from coder.backend import get_completion
from .utils import clip_prompt

def completion(context):
    return get_completion('Codex', clip_prompt(context, 1000))