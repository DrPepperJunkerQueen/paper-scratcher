import pygame
import constants

class SplashScreen:
    def __init__(self, screen):
        self.screen = screen
        self.next_scene = None
        self.logo = pygame.image.load(constants.SPLASH_IMAGE_PATH).convert_alpha()
        self.logo = pygame.transform.scale(self.logo, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        self.alpha = 0
        self.fade_in = True
        self.timer = pygame.time.get_ticks()

        # Wczytaj i odtwórz dźwięk
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound(constants.SPLASH_SOUND_PATH)
        self.sound.set_volume(0.05)
        self.sound.play()

    def handle_event(self, event):
        pass  # Splash screen nie reaguje na kliknięcia

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.timer

        if self.fade_in:
            self.alpha += 5
            if self.alpha >= 255:
                self.alpha = 255
                self.fade_in = False
                self.timer = now  # resetuj timer
        else:
            if elapsed > 2000:  # zacznij fade out po 1s
                self.alpha -= 5
                if self.alpha <= 0:
                    self.alpha = 0
                    from scenes.main_menu import MainMenu
                    self.next_scene = MainMenu(self.screen)

    def draw(self):
        self.screen.fill((0, 0, 0))
        temp_logo = self.logo.copy()
        temp_logo.set_alpha(self.alpha)
        rect = temp_logo.get_rect(center=(constants.SCREEN_WIDTH / 2, constants.SCREEN_HEIGHT / 2))
        self.screen.blit(temp_logo, rect)
