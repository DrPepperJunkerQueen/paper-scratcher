import pygame
import constants
import math
import random
from scenes.game_mechanics.PaperBot import PaperBot
from scenes.game_mechanics.PaperPlayer import PaperPlayer



def convex_hull(points):
    """Algoritm Grahama dla otoczki wypukłej"""
    if len(points) < 3:
        return points

    # Znajdź punkt o najniższej współrzędnej y (i najniższej x w przypadku remisu)
    start = min(points, key=lambda p: (p[1], p[0]))

    # Sortuj punkty według kąta polarnego względem punktu startowego
    def polar_angle(p):
        return math.atan2(p[1] - start[1], p[0] - start[0])

    sorted_points = sorted([p for p in points if p != start], key=polar_angle)

    # Buduj otoczkę wypukłą
    hull = [start]
    for point in sorted_points:
        # Usuń punkty, które tworzą zakręt w prawo
        while len(hull) > 1 and cross_product(hull[-2], hull[-1], point) <= 0:
            hull.pop()
        hull.append(point)

    return hull


def cross_product(o, a, b):
    """Iloczyn wektorowy dla trzech punktów"""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def point_in_polygon(point, polygon):
    """Sprawdź czy punkt jest wewnątrz wielokąta używając ray casting"""
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def find_area_intersection(area, trail_start, trail_end):
    """Znajdź punkty przecięcia śladu z obszarem"""
    intersections = []

    for i in range(len(area)):
        p1 = area[i]
        p2 = area[(i + 1) % len(area)]

        # Sprawdź przecięcie odcinka area z punktem wyjścia/wejścia
        if point_on_segment(p1, p2, trail_start):
            intersections.append((i, trail_start))
        if point_on_segment(p1, p2, trail_end):
            intersections.append((i, trail_end))

    return intersections


def point_on_segment(p1, p2, point, tolerance=5):
    """Sprawdź czy punkt leży na odcinku z tolerancją"""
    # Sprawdź czy punkt jest blisko odcinka
    dist = distance_point_to_segment(point, p1, p2)
    return dist <= tolerance


def distance_point_to_segment(point, seg_start, seg_end):
    """Odległość punktu od odcinka"""
    px, py = point
    x1, y1 = seg_start
    x2, y2 = seg_end

    A = px - x1
    B = py - y1
    C = x2 - x1
    D = y2 - y1

    dot = A * C + B * D
    len_sq = C * C + D * D

    if len_sq == 0:
        return math.sqrt(A * A + B * B)

    param = dot / len_sq

    if param < 0:
        xx, yy = x1, y1
    elif param > 1:
        xx, yy = x2, y2
    else:
        xx = x1 + param * C
        yy = y1 + param * D

    dx = px - xx
    dy = py - yy
    return math.sqrt(dx * dx + dy * dy)


class GameScene:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 24)
        self.big_font = pygame.font.SysFont("arial", 48)
        self.next_scene = None
        self.bot = PaperBot(100, 100)
        self.bot2 = PaperBot(constants.SCREEN_WIDTH-100, constants.SCREEN_HEIGHT-100)
        self.bot3 = PaperBot(100, constants.SCREEN_HEIGHT - 100)
        # Gracz będzie teraz używał wybranego skina
        self.player = PaperPlayer(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2, bot=self.bot)
        self.speed = 2
        self.game_over_timer = 0
        self.map_area = (constants.SCREEN_WIDTH - 100) * (constants.SCREEN_HEIGHT - 100)
        self.win_ratio = 0.8

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from scenes.main_menu import MainMenu
                self.next_scene = MainMenu(self.screen)
            elif event.key == pygame.K_r and (
                        not self.player.is_alive or not self.bot.is_alive or not self.bot2.is_alive or not self.bot3.is_alive):
                # Resetuj gra z zachowaniem wybranego skina
                self.bot = PaperBot(100, 100)
                self.bot2 = PaperBot(constants.SCREEN_WIDTH - 100, constants.SCREEN_HEIGHT - 100)
                self.bot3 = PaperBot(100, constants.SCREEN_HEIGHT - 100)
                self.player = PaperPlayer(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2, bot=self.bot)
                self.game_over_timer = 0
            elif self.player.is_alive:
                # Sterowanie tylko gdy gracz żyje
                if event.key == pygame.K_LEFT:
                    self.player.direction = (-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.player.direction = (1, 0)
                elif event.key == pygame.K_UP:
                    self.player.direction = (0, -1)
                elif event.key == pygame.K_DOWN:
                    self.player.direction = (0, 1)

    def update(self):
        if self.player.is_alive and (self.bot.is_alive or self.bot2.is_alive or self.bot3.is_alive):
            self.player.move(self.speed)
            if self.bot.is_alive:
                self.bot.move(self.speed)
            if self.bot2.is_alive:
                self.bot2.move(self.speed)
            if self.bot3.is_alive:
                self.bot3.move(self.speed)

            # Kolizje gracza z botami
            if self.bot.is_alive and self.check_trail_collision(self.player, self.bot):
                self.bot.die("Kolizja ze śladem bota 1")
                self.player.area = convex_hull(self.player.area + self.bot.area)
            if self.bot2.is_alive and self.check_trail_collision(self.player, self.bot2):
                self.bot2.die("Kolizja ze śladem bota 2")
                self.player.area = convex_hull(self.player.area + self.bot2.area)
            if self.bot3.is_alive and self.check_trail_collision(self.player, self.bot3):
                self.bot3.die("Kolizja ze śladem bota 3")
                self.player.area = convex_hull(self.player.area + self.bot3.area)

            # Kolizje botów ze śladem gracza
            if self.bot.is_alive and self.check_trail_collision(self.bot, self.player):
                self.player.die("Bot 1 przejął twój ślad")
                self.bot.area = convex_hull(self.bot.area + self.player.area)
                self.player.area = []
            if self.bot2.is_alive and self.check_trail_collision(self.bot2, self.player):
                self.player.die("Bot 2 przejął twój ślad")
                self.bot2.area = convex_hull(self.bot2.area + self.player.area)
                self.player.area = []
            if self.bot3.is_alive and self.check_trail_collision(self.bot3, self.player):
                self.player.die("Bot 3 przejął twój ślad")
                self.bot3.area = convex_hull(self.bot3.area + self.player.area)
                self.player.area = []

            # Warunek zwycięstwa
            player_area = self.player.calculate_polygon_area(self.player.area)
            bot_area = self.bot.calculate_polygon_area(self.bot.area) if self.bot.is_alive else 0
            bot2_area = self.bot2.calculate_polygon_area(self.bot2.area) if self.bot2.is_alive else 0
            bot3_area = self.bot3.calculate_polygon_area(self.bot3.area) if self.bot3.is_alive else 0

            if player_area > self.map_area * self.win_ratio:
                self.bot.is_alive = False
                self.bot2.is_alive = False
                self.bot3.is_alive = False
                self.player.death_reason = "Zajęto >80% mapy"
            elif bot_area > self.map_area * self.win_ratio:
                self.player.is_alive = False
                self.player.death_reason = "Bot 1 zajął >80% mapy"
            elif bot2_area > self.map_area * self.win_ratio:
                self.player.is_alive = False
                self.player.death_reason = "Bot 2 zajął >80% mapy"
            elif bot3_area > self.map_area * self.win_ratio:
                self.player.is_alive = False
                self.player.death_reason = "Bot 3 zajął >80% mapy"
        else:
            self.game_over_timer += 1

    def check_trail_collision(self, attacker, defender):
        """Sprawdź czy attacker najechał na ślad defendera"""
        if not defender.is_tracing or not defender.trail or not attacker.is_alive:
            return False
        attacker_pos = (attacker.x, attacker.y)
        for i in range(len(defender.trail) - 1):
            p1 = defender.trail[i]
            p2 = defender.trail[i + 1]
            if distance_point_to_segment(attacker_pos, p1, p2) < attacker.size // 2 + 3:
                return True
        return False

    def draw(self):
        self.screen.fill((255, 255, 255))
        pygame.draw.rect(self.screen, (0, 0, 0), (50, 50, constants.SCREEN_WIDTH - 100, constants.SCREEN_HEIGHT - 100),
                         3)

        # Rysuj obszary botów
        if len(self.bot.area) > 2:
            pygame.draw.polygon(self.screen, (255, 220, 180), self.bot.area)
            pygame.draw.polygon(self.screen, (200, 100, 0), self.bot.area, 2)
        if len(self.bot2.area) > 2:
            pygame.draw.polygon(self.screen, (220, 255, 180), self.bot2.area)
            pygame.draw.polygon(self.screen, (100, 200, 0), self.bot2.area, 2)
        if len(self.bot3.area) > 2:
            pygame.draw.polygon(self.screen, (180, 255, 220), self.bot3.area)
            pygame.draw.polygon(self.screen, (0, 200, 100), self.bot3.area, 2)
        if len(self.player.area) > 2:
            color = (200, 220, 255) if self.player.is_alive else (150, 150, 150)
            border = (0, 0, 200) if self.player.is_alive else (100, 100, 100)
            pygame.draw.polygon(self.screen, color, self.player.area)
            pygame.draw.polygon(self.screen, border, self.player.area, 2)


        # Rysuj postacie
        self.bot.draw(self.screen)
        self.bot2.draw(self.screen)
        self.bot3.draw(self.screen)
        self.player.draw(self.screen)

        font = pygame.font.SysFont("arial", 22)
        entities = [
            (self.player, (0, 0, 200)),
            (self.bot, (200, 100, 0)),
            (self.bot2, (100, 200, 0)),
            (self.bot3, (0, 200, 100)),
        ]
        for entity, color in entities:
            if len(entity.area) > 2:
                area = entity.calculate_polygon_area(entity.area)
                percent = int(100 * area / self.map_area)
                centroid = entity.calculate_centroid(entity.area)
                text = font.render(f"{percent}%", True, color)
                text_rect = text.get_rect(center=(int(centroid[0]), int(centroid[1])))
                self.screen.blit(text, text_rect)

        self.draw_ui()
        if not self.player.is_alive or (not self.bot.is_alive and not self.bot2.is_alive and not self.bot3.is_alive):
            self.draw_game_over()

    def draw_ui(self):
        """Rysuj interfejs użytkownika"""
        # Pokaż powierzchnię obszaru
        area_size = int(self.player.calculate_polygon_area(self.player.area))
        area_text = self.font.render(f"Obszar: {area_size} px²", True, (0, 0, 0))
        self.screen.blit(area_text, (10, 10))

        # Pokaż status
        if self.player.is_tracing:
            status_text = self.font.render("Rysowanie", True, (255, 0, 0))
            self.screen.blit(status_text, (300, 10))
        else:
            status_text = self.font.render("W bezpiecznym obszarze", True, (0, 150, 0))
            self.screen.blit(status_text, (300, 10))

        # Instrukcje
        instruction_text = self.font.render("Strzałki: sterowanie | ESC: menu | R: restart (po śmierci)", True,
                                            (100, 100, 100))
        self.screen.blit(instruction_text, (10, constants.SCREEN_HEIGHT - 30))


    def draw_game_over(self):
        overlay = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        if not self.player.is_alive:
            game_over_text = self.big_font.render("GAME OVER", True, (255, 0, 0))
            reason = self.player.death_reason
        else:
            game_over_text = self.big_font.render("WYGRAŁEŚ!", True, (0, 200, 0))
            reason = self.bot.death_reason

        text_rect = game_over_text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2 - 60))
        self.screen.blit(game_over_text, text_rect)

        reason_text = self.font.render(f"Przyczyna: {reason}", True, (255, 255, 255))
        reason_rect = reason_text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2 - 10))
        self.screen.blit(reason_text, reason_rect)

        restart_text = self.font.render("Naciśnij R aby zagrać ponownie", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(restart_text, restart_rect)

        menu_text = self.font.render("Naciśnij ESC aby wrócić do menu", True, (255, 255, 255))
        menu_rect = menu_text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(menu_text, menu_rect)