import pygame
import constants

class SkinSelectionScene:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.Font(constants.TITLE_FONT_PATH, 72)
        self.button_font = pygame.font.SysFont("Comic Sans MS", 36)
        self.small_font = pygame.font.SysFont("Comic Sans MS", 24)
        self.next_scene = None

        # Wczytanie i skalowanie skórek
        self.skin_paths = constants.SKIN_IMAGE_PATHS
        self.skins = []
        self.skin_display_size = 250  # rozmiar kwadratowy
        for path in self.skin_paths:
            try:
                image = pygame.image.load(path).convert_alpha()
                image = pygame.transform.smoothscale(image, (self.skin_display_size, self.skin_display_size))
                self.skins.append(image)
            except pygame.error:
                # Jeśli nie udało się wczytać skina, stwórz placeholder
                placeholder = pygame.Surface((self.skin_display_size, self.skin_display_size))
                placeholder.fill((128, 128, 128))
                self.skins.append(placeholder)
        
        self.current_index = constants.SELECTED_SKIN_INDEX

        # Trójkątne przyciski po bokach
        self.left_button = pygame.Rect(40, (constants.SCREEN_HEIGHT - 60) // 2, 60, 60)
        self.right_button = pygame.Rect(constants.SCREEN_WIDTH - 100, (constants.SCREEN_HEIGHT - 60) // 2, 60, 60)

        # Przyciski dolne - przesunięte niżej
        self.button_select = pygame.Rect((constants.SCREEN_WIDTH - 200) // 2, 650, 200, 60)
        self.button_back = pygame.Rect((constants.SCREEN_WIDTH - 200) // 2, 730, 200, 60)
        
        # Status message
        self.status_message = ""
        self.status_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.left_button.collidepoint(event.pos):
                self.current_index = (self.current_index - 1) % len(self.skins)
            elif self.right_button.collidepoint(event.pos):
                self.current_index = (self.current_index + 1) % len(self.skins)
            elif self.button_select.collidepoint(event.pos):
                # Ustaw wybrany skin
                constants.SELECTED_SKIN_INDEX = self.current_index
                self.status_message = f"Skin {self.current_index + 1} selected!"
                self.status_timer = 120  # Pokaż wiadomość przez 2 sekundy (60 FPS)
            elif self.button_back.collidepoint(event.pos):
                from scenes.main_menu import MainMenu
                self.next_scene = MainMenu(self.screen)

    def update(self):
        if self.status_timer > 0:
            self.status_timer -= 1

    def draw(self):
        self.screen.fill((0, 0, 0))

        # Tytuł
        title = self.title_font.render("Choose Skin", True, (0, 255, 0))
        self.screen.blit(title, ((constants.SCREEN_WIDTH - title.get_width()) / 2, 60))

        # Obrazek skina (wycentrowany między strzałkami)
        if self.skins:
            current_skin = self.skins[self.current_index]
            skin_rect = current_skin.get_rect(center=(constants.SCREEN_WIDTH / 2, constants.SCREEN_HEIGHT / 2))
            self.screen.blit(current_skin, skin_rect)

        # Informacja o aktualnie wybranym skinie - przesunięta niżej
        current_info = self.small_font.render(f"Skin {self.current_index + 1} of {len(self.skins)}", True, (255, 255, 255))
        self.screen.blit(current_info, ((constants.SCREEN_WIDTH - current_info.get_width()) / 2, 540))

        # Pokazuj który skin jest obecnie aktywny - przesunięte niżej
        if self.current_index == constants.SELECTED_SKIN_INDEX:
            active_text = self.small_font.render("(Currently Active)", True, (0, 255, 0))
            self.screen.blit(active_text, ((constants.SCREEN_WIDTH - active_text.get_width()) / 2, 570))

        # Przyciski tekstowe
        button_color = (0, 255, 0)
        for rect, label in [(self.button_select, "Select"), (self.button_back, "Return")]:
            pygame.draw.rect(self.screen, button_color, rect)
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

        # Status message - przesunięte niżej
        if self.status_timer > 0:
            status_text = self.small_font.render(self.status_message, True, (0, 255, 0))
            self.screen.blit(status_text, ((constants.SCREEN_WIDTH - status_text.get_width()) / 2, 600))