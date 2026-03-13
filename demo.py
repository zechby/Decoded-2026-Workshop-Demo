# imports & initialisation
import pygame
import sys

pygame.init()

# window; assets; images; scaling
# game window setup
screen = pygame.display.set_mode((1000, 500))
pygame.display.set_caption("NPC Chat Demo")
# background
background = pygame.image.load("assets/background.png")
background = pygame.transform.scale(background, (1000, 500))
# npc sprite
npc = pygame.image.load("assets/npc.png")
npc = pygame.transform.scale(npc, (400, 400))

# positioning UI; rect objects; centering objects
# chatbox
chat_panel = pygame.Rect(0, 0, 700, 180)
chat_panel.centerx = screen.get_width() // 2
chat_panel.bottom = screen.get_height() - 40
# npc repositioning
npc_rect = npc.get_rect()
npc_rect.centerx = screen.get_width() // 2
npc_rect.bottom = chat_panel.y + 100

# define colours, font, and clock
black = (0, 0, 0)
white = (255, 255, 255)
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

# game state vars
messages = ["NPC: Hello! What's your name?"]
player_input = ""

# main game loop (60 fps as per clock)
running = True
while running:
    
    # 1. handle events (keyboard input, capturing text, etc.)
    for event in pygame.event.get():
        
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_BACKSPACE:
                player_input = player_input[:-1]

            elif event.key == pygame.K_RETURN:
                messages.append("> " + player_input)

                npc_response = "NPC: Nice to meet you " + player_input
                messages.append(npc_response)

                player_input = ""

            else:
                player_input += event.unicode

    # 2. rendering/drawing
    # background
    screen.blit(background, (0,0))
    # npc
    screen.blit(npc, npc_rect)
    # chat box
    pygame.draw.rect(screen, black, chat_panel)
    # dialogue
    y = chat_panel.y + 10
    for msg in messages:
        text_surface = font.render(msg, True, white)
        screen.blit(text_surface, (chat_panel.x + 10, y))
        y += 30
    # player input (dynamic text)
    input_surface = font.render("> " + player_input, True, white)
    screen.blit(input_surface, (chat_panel.x + 10, y))

    # 3. updating the screen
    pygame.display.flip()
    clock.tick(60)

# clean exit
pygame.quit()
sys.exit()



# setup
# create game objects
# game loop (input, update, render, repeat)
# exit
