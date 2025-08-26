import pygame
import sys
import random

# Initialize pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CET Glitch")

# Clock
clock = pygame.time.Clock()
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GREEN = (0, 255, 0)

# Font
font = pygame.font.SysFont("consolas", 50)

# Glitchy text render
def draw_glitchy_text(text, x, y):
    base = font.render(text, True, WHITE)
    screen.blit(base, (x, y))
    # Random glitch offsets
    for color in [CYAN, MAGENTA, GREEN]:
        offset_x = random.randint(-2, 2)
        offset_y = random.randint(-2, 2)
        glitch = font.render(text, True, color)
        screen.blit(glitch, (x + offset_x, y + offset_y))

# Main menu
def main_menu():
    while True:
        screen.fill(BLACK)
        draw_glitchy_text("CET GLITCH", WIDTH//2 - 180, HEIGHT//2 - 100)
        draw_glitchy_text("Press ENTER to Start", WIDTH//2 - 250, HEIGHT//2 + 50)
        draw_glitchy_text("Press ESC to Quit", WIDTH//2 - 220, HEIGHT//2 + 120)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    game_loop()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()
        clock.tick(FPS)

# Placeholder game loop
def game_loop():
    running = True
    while running:
        screen.fill(BLACK)
        draw_glitchy_text("Dhwani Night...", WIDTH//2 - 200, HEIGHT//2 - 50)
        draw_glitchy_text("Press ESC to Return", WIDTH//2 - 260, HEIGHT//2 + 80)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        pygame.display.flip()
        clock.tick(FPS)

# Run the menu
main_menu()
