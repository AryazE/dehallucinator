from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-350M-mono")
model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-350M-mono").to(0)

def get_completion(context):
    inputs = tokenizer(context, return_tensors="pt").to(0)
    sample = model.generate(**inputs, max_new_tokens=500)
    return tokenizer.decode(sample[0], truncate_before_pattern=["\n\n^#", "^'''", "\n\n\n"])
