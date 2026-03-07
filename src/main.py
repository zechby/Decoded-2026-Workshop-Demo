import pygame
import sys
from groq import Groq
from api_call import call_llama_4_gm, api_key

pygame.init()

WIDTH, HEIGHT = 600, 400


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simple Dialogue Demo")


client = Groq(api_key=api_key)
input_buffer = ""

text_font = pygame.font.SysFont("Comic Sans", 25)
name_font = pygame.font.SysFont("Comic Sans", 10)



input_box = pygame.Rect(50,320,500,40)

current_line = 0

button_rect = pygame.Rect(WIDTH - 120, HEIGHT - 60, 100, 40)


# use this to store texts, and therefore the chat as a whole
chat_history = [
    {
        "User": "AI",
        "Text": "hi babes",
        "pos": (55, 255)
    }
]


# ts function just removes the pos value from all of chat history, makes it easier for the ai to parse
def strip_chat_history(chat_history):
    actual_chats = []
    for i in chat_history:
        actual_chats.append({
            "User": i["User"],
            "Text": i["Text"]
        })
        
    return actual_chats

users = {
        "AI": {
            "personality": "you are a character in a dating simulator, respond in less than 50 characters and be cute, flirty and eager to converse",
            "pfp_path": "assets/smile.png",
            "display_name": "big yahu"
        },
        "User": {
            "personality": None,
            "pfp_path": "assets/brian.jpg",
            "display_name": "brian"
        }
    }

def send_text(text_dict):
    rendered_content = text_font.render(text_dict["Text"], True, (255, 255, 255), wraplength=485)
    # we need to render the text before drawing the background textbox
    
    text_width = rendered_content.get_width()
    text_height = rendered_content.get_height()
    text_box = pygame.Rect(text_dict["pos"][0] - 5, text_dict["pos"][1], text_width + 10, text_height)
    pygame.draw.rect(screen, (50, 50, 70), text_box, border_radius = 7)
    # draws the background textbox
    
    screen.blit(rendered_content, text_dict["pos"])
    # sends the actual contents of the text
    
    sender_pfp = pygame.transform.scale(pygame.image.load(users[text_dict["User"]]["pfp_path"]).convert_alpha(), (30, 30))
    image_rect = sender_pfp.get_rect()
    screen.blit(sender_pfp, (text_dict["pos"][0] - 45, text_dict["pos"][1]))
    # drawing the senders pfp
    
    rendered_name = name_font.render(users[text_dict["User"]]["display_name"], True, (255,255,0))
    screen.blit(rendered_name, (text_dict["pos"][0] - 55, text_dict["pos"][1] + 30))
    # renders the name just under the profile picture
    

    
def draw_input_box(input):
    rendered = text_font.render(input, True, (255,255,255))
    screen.blit(rendered, (input_box.x + 5, input_box.y + 5))

running = True
while running:
    screen.fill((30, 30, 40))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                input_buffer = input_buffer[:-1]
            elif event.key == pygame.K_RETURN:
                
                # clears input buffer and add the new text to history
                chat_history.append({
                    "User": "User",
                    "Text": input_buffer,
                    "pos": (55, 305)
                })
                input_buffer = ""
                
                
                response = call_llama_4_gm(history = strip_chat_history(chat_history)[:-1],
                system_prompt = users["AI"]["personality"], 
                player_action = chat_history[len(chat_history) - 1]["Text"])
        
                response = response.replace('"', '')
                chat_history.append({
            "User": "AI",
            "Text": response,
            "pos": (55, 355)
        })

                
                for text in chat_history:
                    text["pos"] = (text["pos"][0], text["pos"][1] - text_font.render(chat_history[-1]["Text"], True, (255,255,255), wraplength=485).get_height() - 65)
                    
            else:
                # if the text takes up more space than is available in the textbox don't let people add more
                # potential change in future could be to make the input box resizeable
                if(text_font.render(input_buffer, True, (255, 255, 255)).get_width() < 485):
                    input_buffer += event.unicode
                    
    
    # sends (renders) all the texts available in history that are not wayyy off screen
    for text in chat_history:
        if text["pos"][1] > -1000:
            send_text(text)
        
    
        
    
    pygame.draw.rect(screen, (70, 70, 100), input_box, border_radius=7)
    draw_input_box(input_buffer)
    
    pygame.display.flip()


pygame.quit()


for i in chat_history:
    print(i)



sys.exit()
