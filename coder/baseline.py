from .utils import get_completion_safely, get_indentation, postprocess

def completion(model, completor, prompt, k=4):
    indent_style, indent_count = get_indentation(prompt)
    comp = get_completion_safely(model, completor, prompt, k=k)
    comp = [postprocess(i, indent_style, indent_count) for i in comp]
    return prompt, comp