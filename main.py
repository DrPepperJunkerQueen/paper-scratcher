import pygame
from scenes.splash import SplashScreen
from scenes.main_menu import MainMenu
from scenes.game import GameScene

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Paper.io")

clock = pygame.time.Clock()

# Sceny
splash = SplashScreen(screen)
menu = MainMenu(screen)
game = GameScene(screen)

# Stan początkowy
current_scene = splash

# Główna pętla
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        current_scene.handle_event(event)

    current_scene.update()
    current_scene.draw()

    # Sprawdź, czy scena się zmieniła
    if current_scene.next_scene:
        current_scene = current_scene.next_scene

    pygame.display.flip()
    clock.tick(60)
