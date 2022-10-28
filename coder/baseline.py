from coder.backend import get_completion

def completion(context):
    return get_completion('Codex', context)