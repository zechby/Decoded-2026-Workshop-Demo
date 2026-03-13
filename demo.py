# imports & initialisation
import pygame
import sys

pygame.init()
pygame.mixer.init()

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
# music
pygame.mixer.music.load("assets/music.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# positioning UI; rect objects; centering objects
# chatbox
chat_panel = pygame.Rect(0, 0, 700, 130)
chat_panel.centerx = screen.get_width() // 2
chat_panel.bottom = screen.get_height() - 20
# npc repositioning
npc_rect = npc.get_rect()
npc_rect.centerx = screen.get_width() // 2
npc_rect.bottom = chat_panel.y + 100
# namebox
name_panel = pygame.Rect(0, 0, chat_panel.width, 40)
name_panel.centerx = screen.get_width() // 2
name_panel.top = 20

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
frozen = False
while running:
    
    # 1. handle events (keyboard input, capturing text, etc.)
    for event in pygame.event.get():
        
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:

            if not frozen:
                if event.key == pygame.K_BACKSPACE:
                    player_input = player_input[:-1]

                elif event.key == pygame.K_RETURN:
                    messages.append("> " + player_input)

                    npc_response = "NPC: Nice to meet you " + player_input
                    messages.append(npc_response)

                    frozen = True

                    player_input = ""

                else:
                    player_input += event.unicode

    # 2. rendering/drawing
    # background
    screen.blit(background, (0,0))
    # npc
    screen.blit(npc, npc_rect)
    # npc name box
    pygame.draw.rect(screen, black, name_panel)
    npc_name = "Jerry"
    name_surface = font.render(npc_name, True, white)
    name_rect = name_surface.get_rect(center=name_panel.center)
    screen.blit(name_surface, name_rect)
    # chat box
    pygame.draw.rect(screen, black, chat_panel)
    # dialogue
    y = chat_panel.y + 10
    for msg in messages:
        text_surface = font.render(msg, True, white)
        screen.blit(text_surface, (chat_panel.x + 10, y))
        y += 30
    # player input (dynamic text)
    if frozen:
        input_surface = font.render("", True, white)
    else:
        input_surface = font.render("> " + player_input, True, white)
    screen.blit(input_surface, (chat_panel.x + 10, y))

    # 3. updating the screen
    pygame.display.flip()
    clock.tick(60)

# clean exit
pygame.mixer.music.stop()
pygame.quit()
sys.exit()
