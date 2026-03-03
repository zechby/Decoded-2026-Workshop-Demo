import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simple Dialogue Demo")

font = pygame.font.SysFont(None, 28)

dialogue = [
    "yo",
    "gurt",
    "sybau"
]

user_input = ""

input_box = pygame.Rect(50,320,500,40)

current_line = 0

button_rect = pygame.Rect(WIDTH - 120, HEIGHT - 60, 100, 40)

def draw_text(text, x, y):
    rendered = font.render(text, True, (255, 255, 255))
    screen.blit(rendered, (x, y))

running = True
while running:
    screen.fill((30, 30, 40))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                user_input = user_input[:-1]
            elif event.key == pygame.K_RETURN:
                # "Submit" input → go to next dialogue line
                if current_line < len(dialogue) - 1:
                    current_line += 1
                    user_input = ""  # clear input for next line
                else:
                    running = False
            else:
                user_input += event.unicode
    pygame.draw.rect(screen, (50, 50, 70), (50, 250, 500, 60))
    draw_text(dialogue[current_line], 70, 265)

    # Draw input box
    pygame.draw.rect(screen, (70, 70, 100), input_box)
    draw_text(user_input, input_box.x + 5, input_box.y + 10)

    pygame.display.flip()

pygame.quit()
sys.exit()