import pygame
import constants

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.Font(constants.TITLE_FONT_PATH, 72)
        self.button_font = pygame.font.SysFont("Comic Sans MS", 36)
        self.next_scene = None

        self.buttons = []
        button_labels = ["Start", "Skins", "Profile", "Settings"]
        button_width = 200
        button_height = 60
        spacing = 20
        total_height = len(button_labels) * (button_height + spacing) - spacing
        start_y = (constants.SCREEN_HEIGHT - total_height) / 2 + 100

        for i, label in enumerate(button_labels):
            x = (constants.SCREEN_WIDTH - button_width) / 2
            y = start_y + i * (button_height + spacing)
            rect = pygame.Rect(x, y, button_width, button_height)
            self.buttons.append((label, rect))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for label, rect in self.buttons:
                if rect.collidepoint(event.pos):
                    if label == "Start":
                        from scenes.game import GameScene
                        self.next_scene = GameScene(self.screen)
                    elif label == "Skins":
                        from scenes.skin_selection import SkinSelectionScene
                        self.next_scene = SkinSelectionScene(self.screen)
                    elif label == "Settings":
                        from scenes.settings import SettingsScene
                        self.next_scene = SettingsScene(self.screen)
                    else:
                        from scenes.game import GameScene
                        self.next_scene = GameScene(self.screen)

    def update(self):
        pass

    def draw(self):
        self.screen.fill((0, 0, 0))

        title_text = self.title_font.render("PaperScratcher", True, (0, 255, 0))
        self.screen.blit(title_text, ((constants.SCREEN_WIDTH - title_text.get_width()) / 2, 100))

        for label, rect in self.buttons:
            pygame.draw.rect(self.screen, (0, 255, 0), rect)
            text = self.button_font.render(label, True, (0, 0, 0))
            self.screen.blit(text, (
                rect.centerx - text.get_width() / 2,
                rect.centery - text.get_height() / 2
            ))