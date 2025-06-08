import pygame
from scenes.splash import SplashScreen
from scenes.main_menu import MainMenu
from scenes.game import GameScene
import constants

pygame.init()
screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
pygame.display.set_caption("Paper Scratcher")

clock = pygame.time.Clock()

splash = SplashScreen(screen)
menu = MainMenu(screen)
game = GameScene(screen)

current_scene = splash

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        current_scene.handle_event(event)

    current_scene.update()
    current_scene.draw()

    if current_scene.next_scene:
        current_scene = current_scene.next_scene

    pygame.display.flip()
    clock.tick(60)