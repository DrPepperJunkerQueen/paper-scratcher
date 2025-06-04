import pygame

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 36)
        self.button_rect = pygame.Rect(300, 300, 200, 60)
        self.next_scene = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_rect.collidepoint(event.pos):
                from scenes.game import GameScene
                self.next_scene = GameScene(self.screen)

    def update(self):
        pass

    def draw(self):
        self.screen.fill((255, 255, 255))
        text = self.font.render("Menu Główne", True, (0, 0, 0))
        self.screen.blit(text, (280, 150))

        pygame.draw.rect(self.screen, (200, 200, 200), self.button_rect)
        start_text = self.font.render("Start", True, (0, 0, 0))
        self.screen.blit(start_text, (370, 310))
