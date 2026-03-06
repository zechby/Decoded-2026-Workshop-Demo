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

chat_history = [
    {
        "User": "AI",
        "Text": "Hello",
        "pos": (55, 255)
    }
]

users = {
        "AI": {
            "personality": "",
            "pfp_path": "smile.png",
            "display_name": "cute waifu"
        },
        "User": {
            "personality": None,
            "pfp_path": "smile.png",
            "display_name": "123"
        }
    }

def send_text(text_dict):
    rendered_content = text_font.render(text_dict["Text"], True, (255, 255, 255))
    screen.blit(rendered_content, text_dict["pos"])
    # sends the actual contents of the text
    
    sender_pfp = pygame.transform.scale(pygame.image.load(users[text_dict["User"]]["pfp_path"]).convert_alpha(), (30, 30))
    image_rect = sender_pfp.get_rect()
    screen.blit(sender_pfp, (text_dict["pos"][0] - 45, text_dict["pos"][1]))
    # drawing the senders pfp
    
    rendered_name = name_font.render(users[text_dict["User"]]["display_name"], True, (255,255,0))
    screen.blit(rendered_name, (text_dict["pos"][0] - 55, text_dict["pos"][1] + 30))
    

    
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
                chat_history.append({
                    "User": "User",
                    "Text": input_buffer,
                    "pos": (55, 300)
                })
                input_buffer = ""
                for text in chat_history:
                    text["pos"] = (text["pos"][0], text["pos"][1] - 50)
                # clear input for next line
            else:
                if(len(input_buffer) < 35):
                    input_buffer += event.unicode
    
    pygame.draw.rect(screen, (50, 50, 70), input_box)
    for text in chat_history:
        send_text(text)

    # Draw input box
    pygame.draw.rect(screen, (70, 70, 100), input_box)
    draw_input_box(input_buffer)
    
    pygame.display.flip()


pygame.quit()


for i in chat_history:
    print(i)



sys.exit()
