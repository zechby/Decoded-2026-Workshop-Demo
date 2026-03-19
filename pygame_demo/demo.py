#--------------------------
# imports & initialisation
#--------------------------
import pygame
import sys

#initialise all pygame modules (graphics, input, etc.)
pygame.init()
#initialise pygame's mixer for playing sound/music
pygame.mixer.init()

#--------------------------------
# window, assets and image setup
#--------------------------------
#create game window of width 1000 height 500
screen = pygame.display.set_mode((1000, 500))
#set the title of the window
pygame.display.set_caption("NPC Chat Demo")

#load world background image
world_background = pygame.image.load("pygame_demo/assets/world_background.png")
world_background = pygame.transform.scale(world_background, (1000, 500))
#load chat background image
chat_background = pygame.image.load("pygame_demo/assets/chat_background.png")
chat_background = pygame.transform.scale(chat_background, (1000, 500))

#load npc sprite
npc_image = pygame.image.load("pygame_demo/assets/npc.png")
npc_world = pygame.transform.scale(npc_image, (50, 50))
npc_chat = pygame.transform.scale(npc_image, (400, 400))
#
world_npc_rect = npc_world.get_rect() #create a rectangle from the loaded npc image
world_npc_rect.centerx = screen.get_width() // 2 #center horizontally
world_npc_rect.bottom = chat_panel.y + 100 #slightly above the chat panel
#
chat_npc_rect = npc_chat.get_rect()
chat_npc_rect.centerx = screen.get_width() // 2
chat_npc_rect.bottom = chat_panel.y + 100

#
chat_panel = pygame.Rect(0, 0, 700, 130) #create a rectangle manually
chat_panel.centerx = screen.get_width() // 2 #center horizontally
chat_panel.bottom = screen.get_height() - 20 #place near bottom
#
name_panel = pygame.Rect(0, 0, chat_panel.width, 40)
name_panel.centerx = screen.get_width() // 2
name_panel.top = 20 #place at top of the screen
npc_name = "Jerry"
name_surface = font.render(npc_name, True, white)
name_rect = name_surface.get_rect(center=name_panel.center)

#player sprite
player = pygame.Rect(100, 300, 50, 50)
player_speed = 5

#load background music, set volume, and play in loop
pygame.mixer.music.load("pygame_demo/assets/music.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1) #-1 means loop indefinitely

#--------------------------------
# define colours, font, and clock
#--------------------------------
black = (0, 0, 0)
white = (255, 255, 255)
#default font for displaying text
font = pygame.font.Font(None, 36)
#clock for controlling frame rate (i.e. how fast the game loop runs)
clock = pygame.time.Clock()

#------------
# game state
#------------
game_state = "world"
frozen = False #freeze input after player responds once

#messages to display in chat panel (starting with the default npc greeting)
messages = ["NPC: Hello! What's your name?"]
#player's current typed input
player_input = ""

#------------
# functions
#------------

def handle_player_movement(keys):
    if keys[pygame.K_LEFT]:
        player.x -= player_speed
    if keys[pygame.K_RIGHT]:
        player.x += player_speed
    if keys[pygame.K_UP]:
        player.y -= player_speed
    if keys[pygame.K_DOWN]:
        player.y += player_speed
    
    #keep player inside screen
    player.x = max(0, min(player.x, screen.get_width() - player.width))
    player.y = max(0, min(player.y, screen.get_height() - player.height))


def check_npc_interaction(keys):
    global game_state
    if player.colliderect(world_npc_rect):
        if keys[pygame.K_e]:
            game_state = "chat"


def draw_world():
    screen.blit(world_background, (0,0))
    #draw npc sprite
    screen.blit(npc_world, world_npc_rect)

    pygame.draw.rect(screen, (0,0,255), player)

    if player.colliderect(world_npc_rect):
        popup = font.render("Press E to talk", True, white)
        popup_rect = popup.get_rect(center=(world_npc_rect.centerx, world_npc_rectnpc_rect.top-20))
        screen.blit(popup, popup_rect)

def draw_chat():
    screen.blit(chat_background, (0,0))
    #draw the npc sprite
    screen.blit(npc_chat, chat_npc_rect)

    #draw chat panel for showing messages
    pygame.draw.rect(screen, black, chat_panel)

    #draw npc's name panel
    pygame.draw.rect(screen, black, name_panel)
    screen.blit(name_surface, name_rect)

    #draw all messages in the chat panel
    y = chat_panel.y + 10
    for msg in messages:
        text_surface = font.render(msg, True, white)
        screen.blit(text_surface, (chat_panel.x + 10, y))
        y += 30 #move down for next line

    #draw player input text dynamically
    if frozen:
        input_surface = font.render("", True, white)
    else:
        input_surface = font.render("> " + player_input, True, white)
    screen.blit(input_surface, (chat_panel.x + 10, y))


#----------------
# main game loop
#----------------
running = True #loop continues until window is closed
while running:

    keys = pygame.key.get_pressed()

    #-----------------------------------------
    # event handling (quit, keyboard, etc.)
    #-----------------------------------------
    for event in pygame.event.get():
        
        #close window if user clicks the close button
        if event.type == pygame.QUIT:
            running = False
        
        #detect key presses
        if event.type == pygame.KEYDOWN:
            
            # ESC to exit chat
            if game_state == "chat" and event.key == pygame.K_ESCAPE:
                game_state = "world"

            if game_state == "chat" and not frozen: #only allow typing if not frozen
                #deleting last character
                if event.key == pygame.K_BACKSPACE:
                    player_input = player_input[:-1]
                #entering input
                elif event.key == pygame.K_RETURN:
                    messages.append("> " + player_input) #adds player's message to chat history
                    #simple npc response
                    npc_response = "NPC: Nice to meet you " + player_input
                    messages.append(npc_response) #adds npc's message to chat history
                    frozen = True #now that player has responded, we want to stop the game
                    player_input = "" #clear input field

                else:
                    #add typed character to current input
                    player_input += event.unicode

    #--------------
    # world update
    #--------------
    if game_state == "world":
        frozen = False
        handle_player_movement(keys)
        check_npc_interaction(keys)

    #------
    # draw
    #------
    if game_state == "world":
        draw_world()
    else:
        draw_chat()

    #----------------------------------------
    # update the display and control fps
    #----------------------------------------
    pygame.display.flip()
    clock.tick(60) #60 fps is standard

#------------
# clean exit
#------------
pygame.mixer.music.stop()
pygame.quit()
sys.exit()
