import ollama

def test_local_model():
    print("requesting local llama3 model...")
    
    # Here we are sending a request to the local Ollama service to process a prompt in Chinese.
    response = ollama.chat(
        model='llama3:8b', 
        messages=[
            {
                'role': 'user',
                'content': 'Here is a 2x2 matrix [[1, 2], [3, 4]]. Please multiply each number by 2 and return only the final JSON matrix result.'
            }
        ]
    )
    
    print("\n--- Model Response ---")
    print(response['message']['content'])

if __name__ == "__main__":
    test_local_model()