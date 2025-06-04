import pygame
import constants

class GameScene:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 36)
        self.next_scene = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from scenes.main_menu import MainMenu
            self.next_scene = MainMenu(self.screen)

    def update(self):
        pass

    def draw(self):
        self.screen.fill((180, 255, 180))
        text = self.font.render("Tryb gry (tu będzie gameplay)", True, (0, 0, 0))
        self.screen.blit(text, (constants.SCREEN_WIDTH / 2, 250))
