from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("NinedayWang/PolyCoder-2.7B")
model = AutoModelForCausalLM.from_pretrained("NinedayWang/PolyCoder-2.7B").to(0)

def get_completion(context):
    inputs = tokenizer.encode(context, return_tensors="pt")
    sample = model.generate(inputs, max_new_tokens=500, num_beams=4, num_return_sequences=1)
    return tokenizer.decode(sample[0], truncate_before_pattern=["\n\n^#", "^'''", "\n\n\n"])