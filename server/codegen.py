from transformers import AutoTokenizer, AutoModelForCausalLM

class CodeGen():
    def __init__(self):
        self.tokenizer = None
        self.model = None

    def get_completion(self, context):
        if self.model is None:
            self.load_model()
        inputs = self.tokenizer(context, return_tensors="pt").to(0)
        sample = self.model.generate(**inputs, max_length=128)
        res = self.tokenizer.decode(sample[0])#, truncate_before_pattern=["\n\n\n", "def ", "class "])
        return res
    
    def load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-2B-mono")
        self.model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-2B-mono").to(0)
    
    def unload_model(self):
        del self.model
        del self.tokenizer
        self.model = None
        self.tokenizer = None
    
    def is_active(self):
        return self.model is not None
