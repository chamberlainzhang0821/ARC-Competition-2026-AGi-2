import os
import ollama
# Note: On Kaggle, you will typically need to import the transformers library, while locally we use ollama.

# 🚀 Automated environment detection switch
IS_KAGGLE = os.path.exists("/kaggle/working")

def generate_answer(prompt_content):
    if IS_KAGGLE:
        # ====== Online Kaggle Execution Logic ======
        # TODO: Implement Kaggle offline model loading logic later for submission
        pass
    else:
        # ====== Local Mac Execution Logic ======
        # Seamlessly call your locally configured Ollama service
        response = ollama.chat(
            model='llama3:8b',
            messages=[{'role': 'user', 'content': prompt_content}]
        )
        return response['message']['content']

# Test execution
if __name__ == "__main__":
    sample_prompt = "Please explain what the ARC competition is."
    result = generate_answer(sample_prompt)
    print(result)