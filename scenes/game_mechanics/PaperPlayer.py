import pygame
import constants
import math
import random
import scenes.game

class PaperPlayer:
    def __init__(self, x, y, color=(0, 0, 255), bot=None):
        self.x = x
        self.y = y
        self.size = constants.SKIN_SIZE  # Rozmiar używany do kolizji i mechaniki gry
        self.visual_size = constants.SKIN_SIZE * 2.5  # Rozmiar wizualny (możesz zmienić mnożnik)
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
                # Używamy visual_size zamiast size do skalowania skina
                self.skin_image = pygame.transform.smoothscale(self.skin_image, (int(self.visual_size), int(self.visual_size)))
        except (pygame.error, IndexError):
            # Jeśli nie udało się wczytać skina, używaj domyślnego koloru
            self.skin_image = None

    def move(self, speed):
        if not self.is_alive:
            return

        dx, dy = self.direction
        new_x = self.x + dx * speed
        new_y = self.y + dy * speed

        # Granice planszy - nadal używamy self.size do kolizji z granicami
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

        # Sprawdź kolizję ze śladem (tylko jeśli rysuje) - nadal używamy self.size
        if self.is_tracing and self.check_trail_collision(current_pos):
            self.die("Kolizja z własnym śladem")
            return

        # Sprawdź, czy gracz jest w swoim obszarze
        if scenes.game.point_in_polygon(current_pos, self.area):
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
        """Sprawdź kolizję z własnym śladem - używa self.size do kolizji"""
        if len(self.trail) < 10:  # Potrzebujemy więcej punktów przed sprawdzeniem kolizji
            return False

        # Sprawdź kolizję z odcinkami śladu (pomijając ostatnie 8 punktów żeby uniknąć fałszywych kolizji)
        for i in range(len(self.trail) - 8):
            if i + 1 < len(self.trail) - 8:
                p1 = self.trail[i]
                p2 = self.trail[i + 1]

                # Sprawdź czy aktualny punkt jest blisko odcinka śladu - używamy self.size
                dist = scenes.game.distance_point_to_segment(current_pos, p1, p2)
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
                taken_points = [p for p in bot.area if scenes.game.point_in_polygon(p, new_area)]
                if taken_points:
                    bot.area = [p for p in bot.area if p not in taken_points]
                    new_area += taken_points
                    bot.area = scenes.game.convex_hull(bot.area)
                    new_area = scenes.game.convex_hull(new_area)
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
            hull = scenes.game.convex_hull(all_points)
            return self.clean_area(hull)

        return None

    def find_closest_edge(self, point):
        """Znajdź indeks najbliższej krawędzi obszaru"""
        min_dist = float('inf')
        closest_idx = -1

        for i in range(len(self.area)):
            p1 = self.area[i]
            p2 = self.area[(i + 1) % len(self.area)]

            dist = scenes.game.distance_point_to_segment(point, p1, p2)
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

        # Rysuj gracza - użyj visual_size dla wyświetlania
        if self.skin_image and self.is_alive:
            # Wycentruj skin - skin już ma odpowiedni rozmiar dzięki load_skin()
            skin_rect = self.skin_image.get_rect(center=(self.x, self.y))
            screen.blit(self.skin_image, skin_rect)
        else:
            # Domyślny kwadrat (gdy nie ma skina lub gracz nie żyje) - używamy visual_size
            player_color = self.color if self.is_alive else (100, 100, 100)
            pygame.draw.rect(
                screen,
                player_color,
                (self.x - self.visual_size // 2, self.y - self.visual_size // 2, 
                 int(self.visual_size), int(self.visual_size))
            )