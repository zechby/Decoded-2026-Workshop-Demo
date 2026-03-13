from groq import Groq
from dotenv import load_dotenv
import os



# to start we need some kind of authorization to use the API
# this often comes in the form of an "API key"
# this is to prevent users from fraudulently spamming the API

# get your API key at https://console.groq.com/keys after making an account

# we then put our api key in a new file named ".env"
# this allows us to isolate our API key from our actual code
# .env is a special file that we can store and load environment specific variables from

# after inserting the following line 
# GROK_API_KEY = 'YOUR API KEY HERE'
# in your newly created .env file, we can begin to actually code


load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
# this just retrieves our api key from the .env file

system_prompt = """
you are a helpful ai
"""
# this is the system prompt, which basically dictates how we want the AI to behave
# it is one of many settings you can mess around with to control how the AI responds

client = Groq(api_key = api_key)
# fills in the api key so we can make requests without inserting a key every time
# creates a "client" that can repeatedly make requests to the API


chat_history = [
        {
            "role":"system",
            "content": system_prompt
        }
]
# we create a global list that stores our conversation so far
# this is actually a list of dictionaries where we list out each message's author and content
# each time we want to send a message, we call the below function

def call_groq(player_input: str, chat_history: list) -> str:
    chat_history.append({
        "role": "user",
        "content": player_input
    })
    # adding a new message to the chat, where the sender is marked as "user" and their message is the content
    
    chat_response = client.chat.completions.create(
        messages=chat_history,
        model = "llama-3.3-70b-versatile",
        temperature= 0.5,
        max_tokens= 200,
    )
    
    # we make the api request, using the client we created earlier
    # because this api doesn't remember your affection, we need to pass the conversation through the AI every time
    
    # feel free to play around with the model, temperature and max_tokens
    # model: what AI model you are calling, generally more parameters means slower models with higher quality responses
    # temperature: how variant do you want the responses to be? basically how wild/wacky the ai can get
    # max_tokens: how long can the response be? tokens are approximately one word, but can be very tricky to measure
    
    
    chat_history.append(chat_response.choices[0].message)
    # we add the AI response to the chat_history from before, storing it in the global conversation array
    return chat_history[-1].content
     
