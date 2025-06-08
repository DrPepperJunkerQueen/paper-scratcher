import pygame
import constants


class SettingsScene:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.Font(constants.TITLE_FONT_PATH, 72)
        self.button_font = pygame.font.SysFont("Comic Sans MS", 36)
        self.small_font = pygame.font.SysFont("Comic Sans MS", 24)
        self.info_font = pygame.font.SysFont("Comic Sans MS", 18)
        self.next_scene = None

        # Przyciski ustawień
        self.hull_toggle_button = pygame.Rect((constants.SCREEN_WIDTH - constants.SETTINGS_BUTTONS_WITDH) // 2, 180, constants.SETTINGS_BUTTONS_WITDH, 50)
        self.triangulation_toggle_button = pygame.Rect((constants.SCREEN_WIDTH - constants.SETTINGS_BUTTONS_WITDH) // 2, 240, constants.SETTINGS_BUTTONS_WITDH, 50)
        self.alpha_decrease_button = pygame.Rect((constants.SCREEN_WIDTH - 400) // 2, 330, 60, 50)
        self.alpha_increase_button = pygame.Rect((constants.SCREEN_WIDTH - 400) // 2 + 340, 330, 60, 50)
        self.smoothing_toggle_button = pygame.Rect((constants.SCREEN_WIDTH - constants.SETTINGS_BUTTONS_WITDH) // 2, 420, constants.SETTINGS_BUTTONS_WITDH, 50)
        self.back_button = pygame.Rect((constants.SCREEN_WIDTH - 200) // 2, 480, 200, 50)

        # Status message
        self.status_message = ""
        self.status_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hull_toggle_button.collidepoint(event.pos):
                # Przełącz typ otoczki (tylko jeśli triangulacja wyłączona)
                if not constants.USE_TRIANGULATION:
                    constants.USE_CONCAVE_HULL = not constants.USE_CONCAVE_HULL
                    hull_type = "Concave (Realistic)" if constants.USE_CONCAVE_HULL else "Convex (Simple)"
                    self.status_message = f"Hull type changed to: {hull_type}"
                    self.status_timer = 180
                else:
                    self.status_message = "Disable Triangulation first!"
                    self.status_timer = 120

            elif self.triangulation_toggle_button.collidepoint(event.pos):
                # Przełącz triangulację
                constants.USE_TRIANGULATION = not constants.USE_TRIANGULATION
                triangulation_type = "Triangulated" if constants.USE_TRIANGULATION else "Standard"
                self.status_message = f"Hull method changed to: {triangulation_type}"
                self.status_timer = 180

            elif self.alpha_decrease_button.collidepoint(
                    event.pos) and constants.USE_CONCAVE_HULL and not constants.USE_TRIANGULATION:
                # Zmniejsz alpha (bardziej szczegółowa otoczka)
                constants.CONCAVE_ALPHA = max(0.5, constants.CONCAVE_ALPHA - 0.5)
                self.status_message = f"Alpha set to: {constants.CONCAVE_ALPHA:.1f}"
                self.status_timer = 180

            elif self.alpha_increase_button.collidepoint(
                    event.pos) and constants.USE_CONCAVE_HULL and not constants.USE_TRIANGULATION:
                # Zwiększ alpha (mniej szczegółowa otoczka)
                constants.CONCAVE_ALPHA = min(5.0, constants.CONCAVE_ALPHA + 0.5)
                self.status_message = f"Alpha set to: {constants.CONCAVE_ALPHA:.1f}"
                self.status_timer = 180

            elif self.smoothing_toggle_button.collidepoint(event.pos):
                # Przełącz wygładzanie obszarów
                constants.AREA_SMOOTHING = not constants.AREA_SMOOTHING
                smoothing_type = "Smooth Areas" if constants.AREA_SMOOTHING else "Sharp Areas"
                self.status_message = f"Area style changed to: {smoothing_type}"
                self.status_timer = 180

            elif self.back_button.collidepoint(event.pos):
                from scenes.main_menu import MainMenu
                self.next_scene = MainMenu(self.screen)

    def update(self):
        if self.status_timer > 0:
            self.status_timer -= 1

    def draw(self):
        self.screen.fill((0, 0, 0))

        # Tytuł
        title = self.title_font.render("Settings", True, (0, 255, 0))
        self.screen.blit(title, ((constants.SCREEN_WIDTH - title.get_width()) / 2, 60))

        # Opis typu otoczki
        desc_text = self.small_font.render("Hull Method (affects area capture mechanics):", True, (255, 255, 255))
        self.screen.blit(desc_text, ((constants.SCREEN_WIDTH - desc_text.get_width()) / 2, 140))

        # Przycisk przełączania typu otoczki
        hull_type = "Concave (Realistic)" if constants.USE_CONCAVE_HULL else "Convex (Simple)"
        button_color = (0, 255, 0) if constants.USE_CONCAVE_HULL else (255, 255, 0)
        button_enabled = not constants.USE_TRIANGULATION

        if not button_enabled:
            button_color = (100, 100, 100)  # Szary gdy wyłączony

        pygame.draw.rect(self.screen, button_color, self.hull_toggle_button)
        hull_text = self.button_font.render(hull_type, True, (0, 0, 0))
        self.screen.blit(hull_text, (
            self.hull_toggle_button.centerx - hull_text.get_width() / 2,
            self.hull_toggle_button.centery - hull_text.get_height() / 2
        ))

        # Przycisk triangulacji
        triangulation_type = "Triangulated Hull" if constants.USE_TRIANGULATION else "Standard Hull"
        triangulation_color = (255, 100, 255) if constants.USE_TRIANGULATION else (200, 200, 200)

        pygame.draw.rect(self.screen, triangulation_color, self.triangulation_toggle_button)
        triangulation_text = self.button_font.render(triangulation_type, True, (0, 0, 0))
        self.screen.blit(triangulation_text, (
            self.triangulation_toggle_button.centerx - triangulation_text.get_width() / 2,
            self.triangulation_toggle_button.centery - triangulation_text.get_height() / 2
        ))

        # Ustawienia alpha (tylko gdy jest wybrana otoczka wklęsła i nie ma triangulacji)
        if constants.USE_CONCAVE_HULL and not constants.USE_TRIANGULATION:
            alpha_desc = self.small_font.render("Concave Detail Level (lower = more detailed):", True, (255, 255, 255))
            self.screen.blit(alpha_desc, ((constants.SCREEN_WIDTH - alpha_desc.get_width()) / 2, 290))

            # Przycisk zmniejszenia alpha
            pygame.draw.rect(self.screen, (255, 100, 100), self.alpha_decrease_button)
            minus_text = self.button_font.render("-", True, (255, 255, 255))
            self.screen.blit(minus_text, (
                self.alpha_decrease_button.centerx - minus_text.get_width() / 2,
                self.alpha_decrease_button.centery - minus_text.get_height() / 2
            ))

            # Wartość alpha
            alpha_value = self.button_font.render(f"{constants.CONCAVE_ALPHA:.1f}", True, (255, 255, 255))
            alpha_x = (constants.SCREEN_WIDTH - alpha_value.get_width()) / 2
            self.screen.blit(alpha_value, (alpha_x, self.alpha_decrease_button.centery - alpha_value.get_height() / 2))

            # Przycisk zwiększenia alpha
            pygame.draw.rect(self.screen, (100, 255, 100), self.alpha_increase_button)
            plus_text = self.button_font.render("+", True, (255, 255, 255))
            self.screen.blit(plus_text, (
                self.alpha_increase_button.centerx - plus_text.get_width() / 2,
                self.alpha_increase_button.centery - plus_text.get_height() / 2
            ))

        # Przycisk przełączania wygładzania obszarów
        smoothing_desc = self.small_font.render("Area Smoothing (affects visual quality):", True, (255, 255, 255))
        self.screen.blit(smoothing_desc, ((constants.SCREEN_WIDTH - smoothing_desc.get_width()) / 2, 380))

        smoothing_type = "Smooth Areas" if constants.AREA_SMOOTHING else "Sharp Areas"
        smoothing_color = (0, 255, 0) if constants.AREA_SMOOTHING else (255, 255, 0)

        pygame.draw.rect(self.screen, smoothing_color, self.smoothing_toggle_button)
        smoothing_text = self.button_font.render(smoothing_type, True, (0, 0, 0))
        self.screen.blit(smoothing_text, (
            self.smoothing_toggle_button.centerx - smoothing_text.get_width() / 2,
            self.smoothing_toggle_button.centery - smoothing_text.get_height() / 2
        ))

        # Przycisk powrotu
        pygame.draw.rect(self.screen, (0, 255, 0), self.back_button)
        back_text = self.button_font.render("Return", True, (0, 0, 0))
        self.screen.blit(back_text, (
            self.back_button.centerx - back_text.get_width() / 2,
            self.back_button.centery - back_text.get_height() / 2
        ))

        # Status message
        if self.status_timer > 0:
            status_text = self.small_font.render(self.status_message, True, (0, 255, 0))
            self.screen.blit(status_text, ((constants.SCREEN_WIDTH - status_text.get_width()) / 2, 420))

        # Informacje o różnicach
        info_lines = [
            "Convex: Simple hull, may capture undrawn areas (faster)",
            "Concave: Realistic hull, follows your path precisely (slower)",
            "Triangulated: Each triangle gets its own mini-hull (experimental)",
            "Smooth: Adds interpolation for smoother trails and areas"
        ]

        for i, line in enumerate(info_lines):
            info_text = info_text = self.info_font.render(line, True, (150, 150, 150))
            self.screen.blit(info_text, ((constants.SCREEN_WIDTH - info_text.get_width()) / 2, 620 + i * 25))