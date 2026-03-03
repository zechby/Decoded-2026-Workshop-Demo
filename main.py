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

        if event.type == pygame.MOUSEBUTTONDOWN:
            if button_rect.collidepoint(event.pos):
                if current_line < len(dialogue) - 1:
                    current_line += 1
                else:
                    running = False  # Quit when finished

    pygame.draw.rect(screen, (50, 50, 70), (50, 250, 500, 100))
    draw_text(dialogue[current_line], 70, 290)

    if current_line < len(dialogue) - 1:
        button_text = "Next"
    else:
        button_text = "Quit"

    pygame.draw.rect(screen, (100, 100, 200), button_rect)
    draw_text(button_text, button_rect.x + 25, button_rect.y + 10)

    pygame.display.flip()

pygame.quit()
sys.exit()