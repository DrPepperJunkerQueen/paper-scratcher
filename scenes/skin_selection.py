import pygame
import constants

class SkinSelectionScene:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.Font(constants.TITLE_FONT_PATH, 72)
        self.button_font = pygame.font.SysFont("Comic Sans MS", 36)
        self.next_scene = None

        # Wczytanie i skalowanie skórek
        self.skin_paths = constants.SKIN_IMAGE_PATHS
        self.skins = []
        self.skin_display_size = 250  # rozmiar kwadratowy
        for path in self.skin_paths:
            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.smoothscale(image, (self.skin_display_size, self.skin_display_size))
            self.skins.append(image)
        self.current_index = 0

        # Trójkątne przyciski po bokach
        self.left_button = pygame.Rect(40, (constants.SCREEN_HEIGHT - 60) // 2, 60, 60)
        self.right_button = pygame.Rect(constants.SCREEN_WIDTH - 100, (constants.SCREEN_HEIGHT - 60) // 2, 60, 60)

        # Przyciski dolne
        self.button_set = pygame.Rect((constants.SCREEN_WIDTH - 200) // 2, 580, 200, 60)
        self.button_back = pygame.Rect((constants.SCREEN_WIDTH - 200) // 2, 660, 200, 60)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.left_button.collidepoint(event.pos):
                self.current_index = (self.current_index - 1) % len(self.skins)
            elif self.right_button.collidepoint(event.pos):
                self.current_index = (self.current_index + 1) % len(self.skins)
            elif self.button_set.collidepoint(event.pos):
                from scenes.game import GameScene
                self.next_scene = GameScene(self.screen)
            elif self.button_back.collidepoint(event.pos):
                from scenes.main_menu import MainMenu
                self.next_scene = MainMenu(self.screen)

    def update(self):
        pass

    def draw(self):
        self.screen.fill((0, 0, 0))

        # Tytuł
        title = self.title_font.render("Choose Skin", True, (0, 255, 0))
        self.screen.blit(title, ((constants.SCREEN_WIDTH - title.get_width()) / 2, 60))

        # Obrazek skina (wycentrowany między strzałkami)
        current_skin = self.skins[self.current_index]
        skin_rect = current_skin.get_rect(center=(constants.SCREEN_WIDTH / 2, constants.SCREEN_HEIGHT / 2))
        self.screen.blit(current_skin, skin_rect)

        # Przyciski tekstowe
        for rect, label in [(self.button_set, "Select"), (self.button_back, "Return")]:
            pygame.draw.rect(self.screen, (0, 255, 0), rect)
            text = self.button_font.render(label, True, (0, 0, 0))
            self.screen.blit(text, (
                rect.centerx - text.get_width() / 2,
                rect.centery - text.get_height() / 2
            ))

        # Trójkąty (strzałki)
        pygame.draw.polygon(self.screen, (0, 255, 0), [
            (self.left_button.right, self.left_button.top),
            (self.left_button.right, self.left_button.bottom),
            (self.left_button.left, self.left_button.centery)
        ])

        pygame.draw.polygon(self.screen, (0, 255, 0), [
            (self.right_button.left, self.right_button.top),
            (self.right_button.left, self.right_button.bottom),
            (self.right_button.right, self.right_button.centery)
        ])