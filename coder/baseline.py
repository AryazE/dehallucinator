from .utils import get_completion_safely, get_indentation, postprocess

def completion(model, completor, prompt):
    indent_style, indent_count = get_indentation(prompt)
    comp = get_completion_safely(model, completor, '', prompt)
    comp = postprocess(comp, indent_style, indent_count)
    return prompt, comp