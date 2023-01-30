from .utils import get_completion_safely

def completion(model, completor, prompt):
    comp = get_completion_safely(model, completor, '', prompt)
    return prompt, comp