import pygame
import constants
import math
import random
import scenes.game


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
        self.just_finished_drawing = False  # NOWA FLAGA do sprawdzania przejęć

        # NOWE: Referencje do innych graczy (będą ustawione przez GameScene)
        self.other_players = []

        margin = 40
        self.area = [
            (x - margin, y - margin),
            (x + margin, y - margin),
            (x + margin, y + margin),
            (x - margin, y + margin)
        ]

    def set_other_players(self, players):
        """Ustaw referencje do innych graczy dla logiki przejmowania obszarów"""
        self.other_players = players

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
        self.just_finished_drawing = False  # Resetuj flagę
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
        if scenes.game.point_in_polygon(current_pos, self.area):
            if self.is_tracing and len(self.trail) > 3:
                self.update_area()
                self.just_finished_drawing = True  # USTAW FLAGĘ
            self.is_tracing = False
            self.trail = []
            self.trail_start_point = None
            self.mode = "explore"
            self.steps_outside = 0
        else:
            self.just_finished_drawing = False  # RESETUJ FLAGĘ gdy rysuje
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

        # Stwórz nowy obszar z śladu i istniejącego obszaru
        new_area = self.create_area_expansion()
        if new_area and len(new_area) >= 3:
            # Przejmij obszary od innych graczy
            for other_player in self.other_players:
                if not other_player.is_alive:
                    continue

                taken_points = [p for p in other_player.area if scenes.game.point_in_polygon(p, new_area)]
                if taken_points:
                    # Usuń przejęte punkty z obszaru przeciwnika
                    other_player.area = [p for p in other_player.area if not scenes.game.point_in_polygon(p, new_area)]

                    # Dodaj przejęte punkty do nowego obszaru
                    new_area += taken_points

                    # Przebuduj obszar przeciwnika
                    if len(other_player.area) >= 3:
                        other_player.area = scenes.game.smart_hull(other_player.area)
                    else:
                        other_player.area = []

                    # Przebuduj nasz obszar z przejętymi punktami
                    new_area = scenes.game.smart_hull(new_area)

                    print(f"Bot przejął {len(taken_points)} punktów od innego gracza!")

            self.area = new_area

    def create_area_expansion(self):
        """Stwórz rozszerzony obszar z obecnego obszaru i śladu"""
        # Połącz obszar i ślad
        all_points = []
        all_points.extend(self.area)
        all_points.extend(self.trail)

        # Użyj smart_hull do stworzenia nowego obszaru
        if len(all_points) >= 3:
            hull = scenes.game.smart_hull(all_points)
            return self.clean_area(hull)

        return None

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

    def distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def draw(self, screen):
        # Każdy bot ma teraz swój unikalny kolor obszaru na podstawie self.color
        if len(self.area) > 2:
            # Jasna wersja koloru dla wypełnienia obszaru
            light_color = (
                min(255, self.color[0] + 100),
                min(255, self.color[1] + 100),
                min(255, self.color[2] + 100)
            )
            # Ciemna wersja koloru dla obramowania
            dark_color = (
                max(0, self.color[0] - 50),
                max(0, self.color[1] - 50),
                max(0, self.color[2] - 50)
            )
            pygame.draw.polygon(screen, light_color, self.area)
            pygame.draw.polygon(screen, dark_color, self.area, 2)

        # Ślad w kolorze czerwonym (pozostaje bez zmian)
        if len(self.trail) > 1:
            pygame.draw.lines(screen, (255, 0, 0), False, self.trail, 3)

        # Rysuj bota w jego unikalnym kolorze
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