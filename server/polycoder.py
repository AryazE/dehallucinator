from transformers import AutoTokenizer, AutoModelForCausalLM

class PolyCoder():
    def __init__(self):
        self.tokenizer = None
        self.model = None

    def load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained("NinedayWang/PolyCoder-2.7B", device_map='auto')
        self.model = AutoModelForCausalLM.from_pretrained("NinedayWang/PolyCoder-2.7B", device_map='auto')

    def get_completion(self, context):
        if self.model is None:
            self.load_model()
        inputs = self.tokenizer(context, return_tensors="pt").to('cuda')
        sample = self.model.generate(**inputs, max_new_tokens=256, num_beams=1, num_return_sequences=1)
        return self.tokenizer.decode(sample[0][inputs.input_ids.shape[1]:], truncate_before_pattern=["\n\n\n", "def ", "class "])

    def unload_model(self):
        del self.model
        del self.tokenizer
        self.model = None
        self.tokenizer = None
    
    def is_active(self):
        return self.model is not None