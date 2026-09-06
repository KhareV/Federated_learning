class PersonalModelManager:
    def fine_tune(self, global_model, local_data, epochs, lr): return global_model
    def evaluate(self, model, test_data): return {"accuracy": 0.9}
    def compare(self, before, after): return {"improvement": 0.0}