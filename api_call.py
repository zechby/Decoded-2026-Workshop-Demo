import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROK_API_KEY")

client = Groq(api_key=api_key)

def call_llama_4_gm(player_action, history=""):
    # 2. Call the model
    # Model ID for Llama 4 Maverick: "meta-llama/llama-4-maverick-17b-128e-instruct"
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a professional RPG Game Master. Keep track of the story and player stats. Be descriptive and creative."
            },
            {
                "role": "user",
                "content": f"Game History: {history}\n\nPlayer Action: {player_action}"
            }
        ],
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        temperature=0.7,  # Higher = more creative, Lower = more consistent
        max_tokens=500,    
    )

    # 3. Return the text response
    return chat_completion.choices[0].message.content

# Example usage:
# response = call_llama_4_gm("I enter the dark cave and light a torch.")
# print(f"GM: {response}")
