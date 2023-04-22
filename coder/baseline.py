from .utils import get_completion_safely, get_indentation, postprocess

def completion(model, completor, prompt, k=4, mode=''):
    indent_style, indent_count = get_indentation(prompt)
    comp = get_completion_safely(model, completor, prompt, k=1)
    tmp = get_completion_safely(model, completor, prompt, k=k)
    if comp[0] in tmp:
        comp = tmp
    else:
        comp.extend(tmp[:-1])
    comp = [postprocess(i, indent_style, indent_count, mode) for i in comp]
    return prompt, comp