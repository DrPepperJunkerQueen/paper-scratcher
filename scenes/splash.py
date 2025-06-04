import pygame

class SplashScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 48)
        self.start_time = pygame.time.get_ticks()
        self.next_scene = None

    def handle_event(self, event):
        pass  # Splash screen nie reaguje na mysz

    def update(self):
        if pygame.time.get_ticks() - self.start_time > 2000:
            from scenes.main_menu import MainMenu
            self.next_scene = MainMenu(self.screen)

    def draw(self):
        self.screen.fill((50, 150, 255))
        text = self.font.render("Witaj w Paper.io!", True, (255, 255, 255))
        self.screen.blit(text, (220, 250))
