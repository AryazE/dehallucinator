from transformers import AutoTokenizer, AutoModelForCausalLM

class PolyCoder():
    def __init__(self):
        self.tokenizer = None
        self.model = None

    def load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained("NinedayWang/PolyCoder-2.7B")
        self.model = AutoModelForCausalLM.from_pretrained("NinedayWang/PolyCoder-2.7B").to(0)

    def get_completion(self, context):
        if self.model is None:
            self.load_model()
        inputs = self.tokenizer(context, return_tensors="pt").to(0)
        sample = self.model.generate(**inputs, max_new_tokens=128, num_beams=4, num_return_sequences=1)
        return self.tokenizer.decode(sample[0])

    def unload_model(self):
        del self.model
        del self.tokenizer
        self.model = None
        self.tokenizer = None
    
    def is_active(self):
        return self.model is not None