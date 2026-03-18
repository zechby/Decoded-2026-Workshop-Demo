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
#load background image and scale to fit the window
background = pygame.image.load("pygame_demo/assets/background.png")
background = pygame.transform.scale(background, (1000, 500))
#load npc sprite and scale it
npc = pygame.image.load("pygame_demo/assets/npc.png")
npc = pygame.transform.scale(npc, (400, 400))
#load background music, set volume, and play in loop
pygame.mixer.music.load("pygame_demo/assets/music.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1) #-1 means loop indefinitely

#------------------------------------
# positioning UI elements using Rects
#------------------------------------
#chat panel for showing messages
chat_panel = pygame.Rect(0, 0, 700, 130) #create a rectangle manually
chat_panel.centerx = screen.get_width() // 2 #center horizontally
chat_panel.bottom = screen.get_height() - 20 #place near bottom
#npc sprite rectangle for positioning
npc_rect = npc.get_rect() #create a rectangle from the loaded npc image
npc_rect.centerx = screen.get_width() // 2 #center horizontally
npc_rect.bottom = chat_panel.y + 100 #slightly above the chat panel
#name panel to display npc's name
name_panel = pygame.Rect(0, 0, chat_panel.width, 40)
name_panel.centerx = screen.get_width() // 2
name_panel.top = 20 #place at top of the screen

#--------------------------------
# define colours, font, and clock
#--------------------------------
black = (0, 0, 0)
white = (255, 255, 255)
#default font for displaying text
font = pygame.font.Font(None, 36)
#clock for controlling frame rate (i.e. how fast the game loop runs)
clock = pygame.time.Clock()

#---------------------
# game state variables
#---------------------
#messages to display in chat panel (starting with the default npc greeting)
messages = ["NPC: Hello! What's your name?"]
#player's current typed input
player_input = ""

#----------------
# main game loop
#----------------
running = True #loop continues until window is closed
frozen = False #freeze input after player responds once

while running:

    #-----------------------------------------
    # 1. event handling (quit, keyboard, etc.)
    #-----------------------------------------
    for event in pygame.event.get():
        
        #close window if user clicks the close button
        if event.type == pygame.QUIT:
            running = False
        
        #detect key presses
        if event.type == pygame.KEYDOWN:

            if not frozen: #only allow typing if not frozen

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

    #----------------------------------
    # 2. rendering / drawing everything
    #----------------------------------
    #draw background first (<destination>.blit(<what to draw>, <where to draw>))
    screen.blit(background, (0,0)) 

    #draw the npc sprite at its rectangle position
    screen.blit(npc, npc_rect)

    #draw npc's name panel
    pygame.draw.rect(screen, black, name_panel)
    npc_name = "Jerry"
    name_surface = font.render(npc_name, True, white)
    name_rect = name_surface.get_rect(center=name_panel.center)
    screen.blit(name_surface, name_rect)

    #draw chat panel
    pygame.draw.rect(screen, black, chat_panel)

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

    #----------------------------------------
    # 3. updating the display and control fps
    #----------------------------------------
    pygame.display.flip()
    clock.tick(60) #60 fps is standard

#------------
# clean exit
#------------
pygame.mixer.music.stop()
pygame.quit()
sys.exit()
