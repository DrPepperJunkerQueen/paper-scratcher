import pygame
import constants
import math
import random


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

class PaperBot:
    def __init__(self, x, y, color=(255, 100, 0)):
        self.x = x
        self.y = y
        self.size = 15
        self.color = color
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.trail = []
        self.is_tracing = False
        self.trail_start_point = None
        self.mode = "explore"  # "explore" lub "return"
        self.steps_outside = 0
        self.is_alive = True
        self.death_reason = ""

        margin = 40
        self.area = [
            (x - margin, y - margin),
            (x + margin, y - margin),
            (x + margin, y + margin),
            (x - margin, y + margin)
        ]

    def calculate_polygon_area(self, points):
        """Oblicz powierzchnię wielokąta"""
        if len(points) < 3:
            return 0

        area = 0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1] - points[j][0] * points[i][1]

        return abs(area) / 2

    def die(self, reason):
        self.is_alive = False
        self.death_reason = reason
        print(f"Bot zmarł: {reason}")

    def move(self, speed):
        # Tryb powrotu do obszaru
        if self.mode == "return":
            centroid = self.calculate_centroid(self.area)
            dx = centroid[0] - self.x
            dy = centroid[1] - self.y
            if abs(dx) > abs(dy):
                self.direction = (1 if dx > 0 else -1, 0)
            else:
                self.direction = (0, 1 if dy > 0 else -1)

        dx, dy = self.direction
        new_x = self.x + dx * speed
        new_y = self.y + dy * speed

        min_x = 50 + self.size // 2
        max_x = constants.SCREEN_WIDTH - 50 - self.size // 2
        min_y = 50 + self.size // 2
        max_y = constants.SCREEN_HEIGHT - 50 - self.size // 2

        # Zmień kierunek przy granicy
        if new_x < min_x or new_x > max_x or new_y < min_y or new_y > max_y:
            self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            return

        self.x = new_x
        self.y = new_y
        current_pos = (self.x, self.y)

        # Sprawdź, czy bot jest w swoim obszarze
        if point_in_polygon(current_pos, self.area):
            if self.is_tracing and len(self.trail) > 3:
                self.update_area()
            self.is_tracing = False
            self.trail = []
            self.trail_start_point = None
            self.mode = "explore"
            self.steps_outside = 0
        else:
            if not self.is_tracing:
                self.is_tracing = True
                self.trail = []
                self.trail_start_point = current_pos
            if not self.trail or self.distance(current_pos, self.trail[-1]) > 3:
                self.trail.append(current_pos)
            self.steps_outside += 1
            # Po wyjściu na określoną liczbę kroków, bot wraca do obszaru
            if self.steps_outside > random.randint(40, 80):
                self.mode = "return"

        # Losowa zmiana kierunku tylko w trybie eksploracji
        if self.mode == "explore" and random.random() < 0.02:
            self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
    def update_area(self):
        if len(self.trail) < 3:
            return
        # Prosta ekspansja: połącz obszar i ślad, znajdź otoczkę wypukłą
        all_points = self.area + self.trail
        if len(all_points) >= 3:
            self.area = convex_hull(all_points)

    def distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def draw(self, screen):
        if len(self.area) > 2:
            pygame.draw.polygon(screen, (255, 220, 180), self.area)
            pygame.draw.polygon(screen, (200, 100, 0), self.area, 2)
        if len(self.trail) > 1:
            pygame.draw.lines(screen, (255, 0, 0), False, self.trail, 3)
        pygame.draw.rect(
            screen,
            self.color,
            (self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
        )

    def calculate_centroid(self, points):
        """Oblicz środek ciężkości wielokąta"""
        if not points:
            return (0, 0)
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return (x, y)

class PaperPlayer:
    def __init__(self, x, y, color=(0, 0, 255), bot=None):
        self.x = x
        self.y = y
        self.size = constants.SKIN_SIZE
        self.color = color
        self.direction = (1, 0)
        self.trail = []
        self.is_tracing = False
        self.trail_start_point = None
        self.is_alive = True
        self.death_reason = ""
        self.bot = bot
        
        # Wczytaj wybrany skin
        self.skin_image = None
        self.load_skin()

        margin = 40
        self.area = [
            (x - margin, y - margin),
            (x + margin, y - margin),
            (x + margin, y + margin),
            (x - margin, y + margin)
        ]

    def load_skin(self):
        """Wczytaj wybrany skin"""
        try:
            if constants.SELECTED_SKIN_INDEX < len(constants.SKIN_IMAGE_PATHS):
                skin_path = constants.SKIN_IMAGE_PATHS[constants.SELECTED_SKIN_INDEX]
                self.skin_image = pygame.image.load(skin_path).convert_alpha()
                self.skin_image = pygame.transform.smoothscale(self.skin_image, (self.size, self.size))
        except (pygame.error, IndexError):
            # Jeśli nie udało się wczytać skina, używaj domyślnego koloru
            self.skin_image = None

    def move(self, speed):
        if not self.is_alive:
            return

        dx, dy = self.direction
        new_x = self.x + dx * speed
        new_y = self.y + dy * speed

        # Granice planszy
        min_x = 50 + self.size // 2
        max_x = constants.SCREEN_WIDTH - 50 - self.size // 2
        min_y = 50 + self.size // 2
        max_y = constants.SCREEN_HEIGHT - 50 - self.size // 2

        # Zatrzymaj się na granicy, niezależnie czy rysujesz czy nie
        if new_x < min_x or new_x > max_x or new_y < min_y or new_y > max_y:
            self.x = max(min_x, min(max_x, new_x))
            self.y = max(min_y, min(max_y, new_y))
            return

        self.x = new_x
        self.y = new_y
        current_pos = (self.x, self.y)

        # Sprawdź kolizję ze śladem (tylko jeśli rysuje)
        if self.is_tracing and self.check_trail_collision(current_pos):
            self.die("Kolizja z własnym śladem")
            return

        # Sprawdź, czy gracz jest w swoim obszarze
        if point_in_polygon(current_pos, self.area):
            if self.is_tracing and len(self.trail) > 3:
                # Zamknij pętlę i powiększ obszar
                self.update_area()
            self.is_tracing = False
            self.trail = []
            self.trail_start_point = None
        else:
            if not self.is_tracing:
                self.is_tracing = True
                self.trail = []
                self.trail_start_point = current_pos

            # Dodaj punkt do śladu tylko jeśli jest wystarczająco daleko od ostatniego
            if not self.trail or self.distance(current_pos, self.trail[-1]) > 3:
                self.trail.append(current_pos)

    def check_trail_collision(self, current_pos):
        """Sprawdź kolizję z własnym śladem"""
        if len(self.trail) < 10:  # Potrzebujemy więcej punktów przed sprawdzeniem kolizji
            return False

        # Sprawdź kolizję z odcinkami śladu (pomijając ostatnie 8 punktów żeby uniknąć fałszywych kolizji)
        for i in range(len(self.trail) - 8):
            if i + 1 < len(self.trail) - 8:
                p1 = self.trail[i]
                p2 = self.trail[i + 1]

                # Sprawdź czy aktualny punkt jest blisko odcinka śladu
                dist = distance_point_to_segment(current_pos, p1, p2)
                if dist < self.size // 2 + 3:  # Kolizja z małą tolerancją
                    return True

        return False

    def die(self, reason):
        """Zabij gracza"""
        self.is_alive = False
        self.death_reason = reason
        print(f"Gracz zmarł: {reason}")

    def reset(self):
        """Resetuj gracza do stanu początkowego"""
        self.x = constants.SCREEN_WIDTH // 2
        self.y = constants.SCREEN_HEIGHT // 2
        self.is_alive = True
        self.death_reason = ""
        self.trail = []
        self.is_tracing = False
        self.trail_start_point = None
        self.direction = (1, 0)
        
        # Przeładuj skin (na wypadek gdyby się zmienił)
        self.load_skin()

        # Resetuj obszar
        margin = 40
        self.area = [
            (self.x - margin, self.y - margin),
            (self.x + margin, self.y - margin),
            (self.x + margin, self.y + margin),
            (self.x - margin, self.y + margin)
        ]

    def distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def update_area(self):
        if len(self.trail) < 3:
            return

        new_area = self.create_simple_expansion()
        if new_area and len(new_area) >= 3:
            bot = self.bot
            if bot:
                taken_points = [p for p in bot.area if point_in_polygon(p, new_area)]
                if taken_points:
                    bot.area = [p for p in bot.area if p not in taken_points]
                    new_area += taken_points
                    bot.area = convex_hull(bot.area)
                    new_area = convex_hull(new_area)
            self.area = new_area

    def create_area_with_intersections(self):
        """Stwórz obszar znajdując przecięcia śladu z obecnym obszarem"""
        if not self.trail_start_point:
            return None

        # Znajdź punkty wejścia i wyjścia ze śladu
        entry_point = self.trail_start_point
        exit_point = (self.x, self.y)

        # Znajdź najbliższe punkty na brzegu obszaru
        entry_edge_idx = self.find_closest_edge(entry_point)
        exit_edge_idx = self.find_closest_edge(exit_point)

        if entry_edge_idx == -1 or exit_edge_idx == -1:
            return None

        # Stwórz nowy obszar
        new_area = []

        # Dodaj część starego obszaru (od exit do entry)
        current_idx = exit_edge_idx
        while current_idx != entry_edge_idx:
            new_area.append(self.area[current_idx])
            current_idx = (current_idx + 1) % len(self.area)

        # Dodaj punkt entry
        new_area.append(self.area[entry_edge_idx])

        # Dodaj ślad
        new_area.extend(self.trail)

        return self.clean_area(new_area)

    def create_simple_expansion(self):
        """Prosta ekspansja - dodaj ślad do istniejącego obszaru"""
        # Połącz obszar i ślad
        all_points = []

        # Dodaj punkty obszaru
        all_points.extend(self.area)

        # Dodaj punkty śladu
        all_points.extend(self.trail)

        # Znajdź otoczkę wypukłą
        if len(all_points) >= 3:
            hull = convex_hull(all_points)
            return self.clean_area(hull)

        return None

    def find_closest_edge(self, point):
        """Znajdź indeks najbliższej krawędzi obszaru"""
        min_dist = float('inf')
        closest_idx = -1

        for i in range(len(self.area)):
            p1 = self.area[i]
            p2 = self.area[(i + 1) % len(self.area)]

            dist = distance_point_to_segment(point, p1, p2)
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        return closest_idx

    def find_closest_point_on_area(self, point):
        """Znajdź najbliższy punkt na brzegu obszaru"""
        min_dist = float('inf')
        closest_point = None
        closest_edge_idx = -1

        for i in range(len(self.area)):
            p1 = self.area[i]
            p2 = self.area[(i + 1) % len(self.area)]

            # Znajdź najbliższy punkt na tym odcinku
            closest_on_segment = self.closest_point_on_segment(point, p1, p2)
            dist = self.distance(point, closest_on_segment)

            if dist < min_dist:
                min_dist = dist
                closest_point = closest_on_segment
                closest_edge_idx = i

        return closest_point, closest_edge_idx

    def clean_area(self, points):
        """Wyczyść obszar z duplikatów i niepotrzebnych punktów"""
        if len(points) < 3:
            return points

        # Usuń duplikaty
        cleaned = []
        for point in points:
            if not cleaned or self.distance(point, cleaned[-1]) > 8:
                cleaned.append(point)

        # Usuń punkt końcowy jeśli jest za blisko pierwszego
        if len(cleaned) > 2 and self.distance(cleaned[0], cleaned[-1]) <= 8:
            cleaned.pop()

        # Jeśli zbyt mało punktów, zwróć oryginalny obszar
        if len(cleaned) < 3:
            return self.area

        return cleaned

    def closest_point_on_segment(self, point, seg_start, seg_end):
        """Znajdź najbliższy punkt na odcinku"""
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
            return seg_start

        param = dot / len_sq

        if param < 0:
            return seg_start
        elif param > 1:
            return seg_end
        else:
            return (x1 + param * C, y1 + param * D)

    def calculate_polygon_area(self, points):
        """Oblicz powierzchnię wielokąta"""
        if len(points) < 3:
            return 0

        area = 0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1] - points[j][0] * points[i][1]

        return abs(area) / 2

    def calculate_centroid(self, points):
        """Oblicz środek ciężkości wielokąta"""
        if not points:
            return (0, 0)

        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return (x, y)

    def remove_duplicate_points(self, points, tolerance=3):
        """Usuń punkty, które są bardzo blisko siebie"""
        if len(points) < 2:
            return points

        cleaned = [points[0]]
        for i in range(1, len(points)):
            if self.distance(points[i], cleaned[-1]) > tolerance:
                cleaned.append(points[i])

        # Sprawdź czy pierwszy i ostatni punkt nie są za blisko
        if len(cleaned) > 2 and self.distance(cleaned[0], cleaned[-1]) <= tolerance:
            cleaned.pop()

        return cleaned

    def draw(self, screen):
        # Rysuj obszar
        if len(self.area) > 2:
            if self.is_alive:
                pygame.draw.polygon(screen, (200, 220, 255), self.area)
                pygame.draw.polygon(screen, (0, 0, 200), self.area, 2)
            else:
                # Jeśli gracz nie żyje, rysuj obszar w szarym kolorze
                pygame.draw.polygon(screen, (150, 150, 150), self.area)
                pygame.draw.polygon(screen, (100, 100, 100), self.area, 2)

        # Rysuj ślad
        if len(self.trail) > 1:
            if self.is_alive:
                pygame.draw.lines(screen, (255, 0, 0), False, self.trail, 3)
            else:
                # Jeśli gracz nie żyje, rysuj ślad w ciemniejszym kolorze
                pygame.draw.lines(screen, (150, 0, 0), False, self.trail, 3)

        # Rysuj gracza - użyj skina jeśli dostępny, w przeciwnym razie użyj kwadratu
        if self.skin_image and self.is_alive:
            # Wycentruj skin
            skin_rect = self.skin_image.get_rect(center=(self.x, self.y))
            screen.blit(self.skin_image, skin_rect)
        else:
            # Domyślny kwadrat (gdy nie ma skina lub gracz nie żyje)
            player_color = self.color if self.is_alive else (100, 100, 100)
            pygame.draw.rect(
                screen,
                player_color,
                (self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
            )


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