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


def concave_hull_alpha_shapes(points, alpha=None):
    """Implementacja otoczki wklęsłej za pomocą alpha shapes"""
    if len(points) < 3:
        return points

    # Użyj alpha z ustawień jeśli nie podano
    if alpha is None:
        alpha = constants.CONCAVE_ALPHA

    # Usuń duplikaty punktów
    unique_points = []
    for point in points:
        is_duplicate = False
        for existing in unique_points:
            if distance_between_points(point, existing) < 3:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_points.append(point)

    if len(unique_points) < 3:
        return unique_points

    # Prosta implementacja alpha shapes
    # 1. Znajdź wszystkie możliwe trójkąty
    triangles = []
    n = len(unique_points)

    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                p1, p2, p3 = unique_points[i], unique_points[j], unique_points[k]

                # Sprawdź czy trójkąt nie jest zdegenerowany
                if abs(cross_product(p1, p2, p3)) < 1e-10:
                    continue

                # Oblicz promień okręgu opisanego na trójkącie
                circumradius = calculate_circumradius(p1, p2, p3)

                # Jeśli promień jest mniejszy niż 1/alpha, dodaj trójkąt
                if circumradius <= 1.0 / alpha:
                    triangles.append([i, j, k])

    if not triangles:
        # Jeśli nie ma odpowiednich trójkątów, użyj otoczki wypukłej
        return convex_hull(unique_points)

    # 2. Znajdź krawędzie brzegowe (które należą tylko do jednego trójkąta)
    edge_count = {}
    for triangle in triangles:
        edges = [
            (min(triangle[0], triangle[1]), max(triangle[0], triangle[1])),
            (min(triangle[1], triangle[2]), max(triangle[1], triangle[2])),
            (min(triangle[0], triangle[2]), max(triangle[0], triangle[2]))
        ]
        for edge in edges:
            edge_count[edge] = edge_count.get(edge, 0) + 1

    # Krawędzie brzegowe to te które występują tylko raz
    boundary_edges = [edge for edge, count in edge_count.items() if count == 1]

    if not boundary_edges:
        return convex_hull(unique_points)

    # 3. Zbuduj kontury z krawędzi brzegowych
    contour = build_contour_from_edges(boundary_edges, unique_points)

    return contour if len(contour) >= 3 else convex_hull(unique_points)


def calculate_circumradius(p1, p2, p3):
    """Oblicz promień okręgu opisanego na trójkącie"""
    # Długości boków
    a = distance_between_points(p2, p3)
    b = distance_between_points(p1, p3)
    c = distance_between_points(p1, p2)

    # Pole trójkąta (wzór Herona)
    s = (a + b + c) / 2
    area_squared = s * (s - a) * (s - b) * (s - c)

    if area_squared <= 0:
        return float('inf')

    area = math.sqrt(area_squared)

    # Promień okręgu opisanego
    if area == 0:
        return float('inf')

    return (a * b * c) / (4 * area)


def build_contour_from_edges(edges, points):
    """Zbuduj kontur z listy krawędzi"""
    if not edges:
        return []

    # Stwórz graf sąsiedztwa
    graph = {}
    for edge in edges:
        p1, p2 = edge
        if p1 not in graph:
            graph[p1] = []
        if p2 not in graph:
            graph[p2] = []
        graph[p1].append(p2)
        graph[p2].append(p1)

    # Znajdź najdłuższy cykl
    visited = set()
    longest_path = []

    for start_node in graph:
        if start_node in visited:
            continue

        path = find_longest_cycle(graph, start_node, visited.copy())
        if len(path) > len(longest_path):
            longest_path = path

    # Przekonwertuj indeksy na punkty
    if longest_path:
        return [points[i] for i in longest_path]
    else:
        return []


def find_longest_cycle(graph, start, visited):
    """Znajdź najdłuższy cykl zaczynający się od danego węzła"""

    def dfs(node, path):
        if node in visited:
            if node == start and len(path) > 2:
                return path
            else:
                return []

        visited.add(node)
        longest = []

        for neighbor in graph.get(node, []):
            result = dfs(neighbor, path + [neighbor])
            if len(result) > len(longest):
                longest = result

        visited.remove(node)
        return longest

    return dfs(start, [start])


def smart_hull(points):
    """Wybierz odpowiednią metodę otoczki na podstawie ustawień"""
    if constants.USE_CONCAVE_HULL:
        return concave_hull_alpha_shapes(points)
    else:
        return convex_hull(points)


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


def polygon_union(poly1, poly2):
    """Połącz dwa wielokąty w jeden (uproszczona wersja)"""
    if len(poly1) < 3 or len(poly2) < 3:
        return poly1 if len(poly1) >= 3 else poly2

    # Znajdź wszystkie punkty z obu wielokątów
    all_points = list(poly1) + list(poly2)

    # Dodaj punkty przecięć krawędzi
    intersection_points = []
    for i in range(len(poly1)):
        edge1_start = poly1[i]
        edge1_end = poly1[(i + 1) % len(poly1)]

        for j in range(len(poly2)):
            edge2_start = poly2[j]
            edge2_end = poly2[(j + 1) % len(poly2)]

            intersection = line_intersection(edge1_start, edge1_end, edge2_start, edge2_end)
            if intersection:
                intersection_points.append(intersection)

    all_points.extend(intersection_points)

    # Znajdź punkty które są na brzegu lub wewnątrz któregokolwiek wielokąta
    union_points = []
    for point in all_points:
        if (point_in_polygon(point, poly1) or point_in_polygon(point, poly2) or
                point_on_polygon_edge(point, poly1) or point_on_polygon_edge(point, poly2)):
            union_points.append(point)

    # Usuń duplikaty
    unique_points = []
    for point in union_points:
        is_duplicate = False
        for existing in unique_points:
            if distance_between_points(point, existing) < 3:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_points.append(point)

    if len(unique_points) >= 3:
        return smart_hull(unique_points)
    else:
        return poly1


def polygon_difference(main_poly, subtract_poly):
    """Odejmij jeden wielokąt od drugiego"""
    if len(main_poly) < 3 or len(subtract_poly) < 3:
        return main_poly

    # Znajdź punkty głównego wielokąta które NIE są wewnątrz odejmowanego
    remaining_points = []
    for point in main_poly:
        if not point_in_polygon(point, subtract_poly):
            remaining_points.append(point)

    # Dodaj punkty przecięć krawędzi
    intersection_points = []
    for i in range(len(main_poly)):
        edge1_start = main_poly[i]
        edge1_end = main_poly[(i + 1) % len(main_poly)]

        for j in range(len(subtract_poly)):
            edge2_start = subtract_poly[j]
            edge2_end = subtract_poly[(j + 1) % len(subtract_poly)]

            intersection = line_intersection(edge1_start, edge1_end, edge2_start, edge2_end)
            if intersection:
                # Sprawdź czy punkt przecięcia leży na krawędzi głównego wielokąta
                if point_on_segment(edge1_start, edge1_end, intersection, tolerance=5):
                    intersection_points.append(intersection)

    remaining_points.extend(intersection_points)

    # Usuń duplikaty
    unique_points = []
    for point in remaining_points:
        is_duplicate = False
        for existing in unique_points:
            if distance_between_points(point, existing) < 3:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_points.append(point)

    if len(unique_points) >= 3:
        return smart_hull(unique_points)
    else:
        return []


def line_intersection(p1, p2, p3, p4):
    """Znajdź przecięcie dwóch linii (odcinków)"""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    # Sprawdź czy przecięcie jest na obu odcinkach
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    return None


def point_on_polygon_edge(point, polygon, tolerance=5):
    """Sprawdź czy punkt leży na brzegu wielokąta"""
    for i in range(len(polygon)):
        edge_start = polygon[i]
        edge_end = polygon[(i + 1) % len(polygon)]
        if point_on_segment(edge_start, edge_end, point, tolerance):
            return True
    return False


def distance_between_points(p1, p2):
    """Odległość między dwoma punktami"""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def calculate_territory_capture(winner_area, winner_trail, loser_area):
    """Oblicz jak przejąć teren po kolizji"""
    if len(winner_trail) < 3:
        return winner_area, loser_area

    # Stwórz nowy obszar z śladu zwycięzcy
    new_captured_area = smart_hull(winner_area + winner_trail)

    if len(new_captured_area) < 3:
        return winner_area, loser_area

    # Połącz nowy obszar z istniejącym obszarem zwycięzcy
    combined_winner_area = polygon_union(winner_area, new_captured_area)

    # Odejmij przejęty teren od przegrywającego
    remaining_loser_area = polygon_difference(loser_area, new_captured_area)

    return combined_winner_area, remaining_loser_area


class GameScene:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 24)
        self.big_font = pygame.font.SysFont("arial", 48)
        self.next_scene = None
        self.bot = PaperBot(100, 100, color=(255, 100, 0))  # Pomarańczowy
        self.bot2 = PaperBot(constants.SCREEN_WIDTH - 100, constants.SCREEN_HEIGHT - 100,
                             color=(100, 255, 0))  # Zielony
        self.bot3 = PaperBot(100, constants.SCREEN_HEIGHT - 100, color=(0, 255, 100))  # Cyjan
        # Gracz będzie teraz używał wybranego skina
        self.player = PaperPlayer(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2, bot=self.bot)

        # NOWE: Ustaw referencje do wszystkich innych graczy dla każdego bota
        self.setup_player_references()
        self.speed = 2
        self.game_over_timer = 0
        self.map_area = (constants.SCREEN_WIDTH - 100) * (constants.SCREEN_HEIGHT - 100)
        self.win_ratio = 0.8

    def setup_player_references(self):
        """Ustaw referencje między wszystkimi graczami dla logiki przejmowania obszarów"""
        # Bot 1 może przejmować od gracza, bot2 i bot3
        self.bot.set_other_players([self.player, self.bot2, self.bot3])

        # Bot 2 może przejmować od gracza, bot1 i bot3
        self.bot2.set_other_players([self.player, self.bot, self.bot3])

        # Bot 3 może przejmować od gracza, bot1 i bot2
        self.bot3.set_other_players([self.player, self.bot, self.bot2])

        # Gracz już ma referencję do bot1, dodaj pozostałe
        self.player.other_bots = [self.bot, self.bot2, self.bot3]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from scenes.main_menu import MainMenu
                self.next_scene = MainMenu(self.screen)
            elif event.key == pygame.K_r and (
                    not self.player.is_alive or not self.bot.is_alive or not self.bot2.is_alive or not self.bot3.is_alive):
                # Resetuj gra z zachowaniem wybranego skina
                self.bot = PaperBot(100, 100, color=(255, 100, 0))  # Pomarańczowy
                self.bot2 = PaperBot(constants.SCREEN_WIDTH - 100, constants.SCREEN_HEIGHT - 100,
                                     color=(100, 255, 0))  # Zielony
                self.bot3 = PaperBot(100, constants.SCREEN_HEIGHT - 100, color=(0, 255, 100))  # Cyjan
                self.player = PaperPlayer(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2, bot=self.bot)
                self.setup_player_references()  # NOWE: Ustaw referencje po resecie
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

    # Dodaj tę metodę do klasy GameScene w game.py

    def debug_collision_check(self):
        """Debug - sprawdź stan wszystkich obiektów"""
        print("=== DEBUG KOLIZJI ===")
        print(
            f"Gracz: pozycja=({self.player.x}, {self.player.y}), is_tracing={self.player.is_tracing}, trail_len={len(self.player.trail)}, area_len={len(self.player.area)}")
        print(
            f"Bot1: pozycja=({self.bot.x}, {self.bot.y}), is_tracing={self.bot.is_tracing}, trail_len={len(self.bot.trail)}, area_len={len(self.bot.area)}")
        print(
            f"Bot2: pozycja=({self.bot2.x}, {self.bot2.y}), is_tracing={self.bot2.is_tracing}, trail_len={len(self.bot2.trail)}, area_len={len(self.bot2.area)}")
        print(
            f"Bot3: pozycja=({self.bot3.x}, {self.bot3.y}), is_tracing={self.bot3.is_tracing}, trail_len={len(self.bot3.trail)}, area_len={len(self.bot3.area)}")

        # Sprawdź czy gracz jest w obszarze któregoś bota
        player_pos = (self.player.x, self.player.y)
        print(f"Gracz w obszarze bot1: {point_in_polygon(player_pos, self.bot.area)}")
        print(f"Gracz w obszarze bot2: {point_in_polygon(player_pos, self.bot2.area)}")
        print(f"Gracz w obszarze bot3: {point_in_polygon(player_pos, self.bot3.area)}")

        # Sprawdź czy któryś bot jest w obszarze gracza
        bot1_pos = (self.bot.x, self.bot.y)
        bot2_pos = (self.bot2.x, self.bot2.y)
        bot3_pos = (self.bot3.x, self.bot3.y)
        print(f"Bot1 w obszarze gracza: {point_in_polygon(bot1_pos, self.player.area)}")
        print(f"Bot2 w obszarze gracza: {point_in_polygon(bot2_pos, self.player.area)}")
        print(f"Bot3 w obszarze gracza: {point_in_polygon(bot3_pos, self.player.area)}")
        print("===================")

    def check_territory_invasion(self):
        """Sprawdź czy ktoś rysuje w obszarze wroga i przejmij teren gdy wraca"""

        # Sprawdź czy gracz kończy rysowanie w obszarze któregoś bota
        if self.player.is_alive and not self.player.is_tracing and len(self.player.trail) == 0:
            # Gracz właśnie skończył rysować - sprawdź czy przejął jakiś teren
            player_pos = (self.player.x, self.player.y)

            # Sprawdź każdego bota
            for bot_name, bot in [("Bot1", self.bot), ("Bot2", self.bot2), ("Bot3", self.bot3)]:
                if not bot.is_alive:
                    continue

                # Sprawdź czy nowy obszar gracza nachodzi na obszar bota
                if len(self.player.area) > 2 and len(bot.area) > 2:
                    captured_area = self.find_overlapping_area(self.player.area, bot.area)
                    if captured_area and len(captured_area) > 2:
                        print(f"!!! PRZEJĘCIE TERENU: Gracz przejął teren od {bot_name} !!!")

                        # Usuń przejęty teren z bota
                        bot.area = self.remove_overlapping_area(bot.area, self.player.area)

                        # Sprawdź czy bot stracił cały teren
                        if len(bot.area) < 3:
                            bot.die(f"Stracił cały teren na rzecz gracza")

        # Sprawdź czy któryś bot kończy rysowanie w obszarze gracza
        for bot_name, bot in [("Bot1", self.bot), ("Bot2", self.bot2), ("Bot3", self.bot3)]:
            if not bot.is_alive or bot.is_tracing or len(bot.trail) > 0:
                continue

            # Bot właśnie skończył rysować
            if len(bot.area) > 2 and len(self.player.area) > 2:
                captured_area = self.find_overlapping_area(bot.area, self.player.area)
                if captured_area and len(captured_area) > 2:
                    print(f"!!! PRZEJĘCIE TERENU: {bot_name} przejął teren od gracza !!!")

                    # Usuń przejęty teren z gracza
                    self.player.area = self.remove_overlapping_area(self.player.area, bot.area)

                    # Sprawdź czy gracz stracił cały teren
                    if len(self.player.area) < 3:
                        self.player.die(f"{bot_name} przejął cały twój teren")

    # Dodaj te nowe metody do klasy GameScene w game.py (przed metodą update):

    def find_overlapping_area(self, area1, area2):
        """Znajdź nachodzącą się część dwóch obszarów"""
        overlapping_points = []

        # Znajdź punkty z area1 które są w area2
        for point in area1:
            if point_in_polygon(point, area2):
                overlapping_points.append(point)

        # Znajdź punkty z area2 które są w area1
        for point in area2:
            if point_in_polygon(point, area1):
                overlapping_points.append(point)

        # Usuń duplikaty
        unique_points = []
        for point in overlapping_points:
            is_duplicate = False
            for existing in unique_points:
                if abs(point[0] - existing[0]) < 5 and abs(point[1] - existing[1]) < 5:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_points.append(point)

        return unique_points if len(unique_points) >= 3 else []

    def remove_overlapping_area(self, main_area, overlapping_area):
        """Usuń nachodzącą się część z głównego obszaru"""
        remaining_points = []

        # Zachowaj tylko punkty które NIE są w nachodzącym obszarze
        for point in main_area:
            if not point_in_polygon(point, overlapping_area):
                remaining_points.append(point)

        if len(remaining_points) >= 3:
            return smart_hull(remaining_points)
        else:
            return []

    # Zastąp metodę check_area_expansion() w game.py tym kodem:

    def check_area_expansion(self):
        """Sprawdź czy ktoś właśnie rozszerzył swój obszar i przejmij terytoria wrogów"""

        # 1. Gdy gracz wraca do swojego obszaru po rysowaniu
        if (self.player.is_alive and not self.player.is_tracing and
                hasattr(self.player, 'just_finished_drawing') and self.player.just_finished_drawing):

            self.player.just_finished_drawing = False
            print("!!! Gracz skończył rysować - sprawdzam przejęcia !!!")

            # Sprawdź każdego bota
            for bot_name, bot in [("Bot1", self.bot), ("Bot2", self.bot2), ("Bot3", self.bot3)]:
                if not bot.is_alive:
                    continue

                # Sprawdź ile terenu bota jest teraz w obszarze gracza
                captured_points = [p for p in bot.area if point_in_polygon(p, self.player.area)]

                if len(captured_points) > len(bot.area) * 0.3:  # Jeśli przejęto >30% terenu bota
                    print(f"!!! Gracz przejął {len(captured_points)}/{len(bot.area)} punktów od {bot_name} !!!")

                    # Usuń przejęte punkty z bota
                    bot.area = [p for p in bot.area if not point_in_polygon(p, self.player.area)]

                    if len(bot.area) < 3:
                        bot.die(f"Stracił teren na rzecz gracza")

        # 2. Gdy bot 1 wraca do swojego obszaru po rysowaniu
        if (self.bot.is_alive and not self.bot.is_tracing and
                hasattr(self.bot, 'just_finished_drawing') and self.bot.just_finished_drawing):

            self.bot.just_finished_drawing = False
            print("!!! Bot 1 skończył rysować - sprawdzam przejęcia !!!")

            # Sprawdź gracza
            if self.player.is_alive:
                captured_points = [p for p in self.player.area if point_in_polygon(p, self.bot.area)]
                if len(captured_points) > len(self.player.area) * 0.3:
                    print(f"!!! Bot 1 przejął {len(captured_points)}/{len(self.player.area)} punktów od gracza !!!")
                    self.player.area = [p for p in self.player.area if not point_in_polygon(p, self.bot.area)]
                    if len(self.player.area) < 3:
                        self.player.die("Bot 1 przejął twój teren")

            # Sprawdź innych botów
            for bot_name, other_bot in [("Bot2", self.bot2), ("Bot3", self.bot3)]:
                if not other_bot.is_alive:
                    continue
                captured_points = [p for p in other_bot.area if point_in_polygon(p, self.bot.area)]
                if len(captured_points) > len(other_bot.area) * 0.3:
                    print(f"!!! Bot 1 przejął {len(captured_points)}/{len(other_bot.area)} punktów od {bot_name} !!!")
                    other_bot.area = [p for p in other_bot.area if not point_in_polygon(p, self.bot.area)]
                    if len(other_bot.area) < 3:
                        other_bot.die(f"Stracił teren na rzecz Bot 1")

        # 3. Gdy bot 2 wraca do swojego obszaru po rysowaniu
        if (self.bot2.is_alive and not self.bot2.is_tracing and
                hasattr(self.bot2, 'just_finished_drawing') and self.bot2.just_finished_drawing):

            self.bot2.just_finished_drawing = False
            print("!!! Bot 2 skończył rysować - sprawdzam przejęcia !!!")

            # Sprawdź gracza
            if self.player.is_alive:
                captured_points = [p for p in self.player.area if point_in_polygon(p, self.bot2.area)]
                if len(captured_points) > len(self.player.area) * 0.3:
                    print(f"!!! Bot 2 przejął {len(captured_points)}/{len(self.player.area)} punktów od gracza !!!")
                    self.player.area = [p for p in self.player.area if not point_in_polygon(p, self.bot2.area)]
                    if len(self.player.area) < 3:
                        self.player.die("Bot 2 przejął twój teren")

            # Sprawdź innych botów
            for bot_name, other_bot in [("Bot1", self.bot), ("Bot3", self.bot3)]:
                if not other_bot.is_alive:
                    continue
                captured_points = [p for p in other_bot.area if point_in_polygon(p, self.bot2.area)]
                if len(captured_points) > len(other_bot.area) * 0.3:
                    print(f"!!! Bot 2 przejął {len(captured_points)}/{len(other_bot.area)} punktów od {bot_name} !!!")
                    other_bot.area = [p for p in other_bot.area if not point_in_polygon(p, self.bot2.area)]
                    if len(other_bot.area) < 3:
                        other_bot.die(f"Stracił teren na rzecz Bot 2")

        # 4. Gdy bot 3 wraca do swojego obszaru po rysowaniu
        if (self.bot3.is_alive and not self.bot3.is_tracing and
                hasattr(self.bot3, 'just_finished_drawing') and self.bot3.just_finished_drawing):

            self.bot3.just_finished_drawing = False
            print("!!! Bot 3 skończył rysować - sprawdzam przejęcia !!!")

            # Sprawdź gracza
            if self.player.is_alive:
                captured_points = [p for p in self.player.area if point_in_polygon(p, self.bot3.area)]
                if len(captured_points) > len(self.player.area) * 0.3:
                    print(f"!!! Bot 3 przejął {len(captured_points)}/{len(self.player.area)} punktów od gracza !!!")
                    self.player.area = [p for p in self.player.area if not point_in_polygon(p, self.bot3.area)]
                    if len(self.player.area) < 3:
                        self.player.die("Bot 3 przejął twój teren")

            # Sprawdź innych botów
            for bot_name, other_bot in [("Bot1", self.bot), ("Bot2", self.bot2)]:
                if not other_bot.is_alive:
                    continue
                captured_points = [p for p in other_bot.area if point_in_polygon(p, self.bot3.area)]
                if len(captured_points) > len(other_bot.area) * 0.3:
                    print(f"!!! Bot 3 przejął {len(captured_points)}/{len(other_bot.area)} punktów od {bot_name} !!!")
                    other_bot.area = [p for p in other_bot.area if not point_in_polygon(p, self.bot3.area)]
                    if len(other_bot.area) < 3:
                        other_bot.die(f"Stracił teren na rzecz Bot 3")

    def update(self):
        if self.player.is_alive and (self.bot.is_alive or self.bot2.is_alive or self.bot3.is_alive):
            self.player.move(self.speed)
            if self.bot.is_alive:
                self.bot.move(self.speed)
            if self.bot2.is_alive:
                self.bot2.move(self.speed)
            if self.bot3.is_alive:
                self.bot3.move(self.speed)

            # 1. Kolizje gracza z botami (gracz zabija bota przez najechanie na ślad)
            if self.bot.is_alive and self.check_trail_collision(self.player, self.bot):
                print("!!! KOLIZJA: Gracz najechał na ślad bota 1 !!!")
                self.bot.die("Kolizja ze śladem gracza")
                self.player.area = smart_hull(self.player.area + self.bot.area)

            if self.bot2.is_alive and self.check_trail_collision(self.player, self.bot2):
                print("!!! KOLIZJA: Gracz najechał na ślad bota 2 !!!")
                self.bot2.die("Kolizja ze śladem gracza")
                self.player.area = smart_hull(self.player.area + self.bot2.area)

            if self.bot3.is_alive and self.check_trail_collision(self.player, self.bot3):
                print("!!! KOLIZJA: Gracz najechał na ślad bota 3 !!!")
                self.bot3.die("Kolizja ze śladem gracza")
                self.player.area = smart_hull(self.player.area + self.bot3.area)

            # 2. Kolizje botów ze śladem gracza (bot zabija gracza przez najechanie na ślad)
            if self.player.is_alive and self.bot.is_alive and self.check_trail_collision(self.bot, self.player):
                print("!!! KOLIZJA: Bot 1 najechał na ślad gracza !!!")
                self.player.die("Bot 1 przejął twój ślad")
                self.bot.area = smart_hull(self.bot.area + self.player.area)
                self.player.area = []

            if self.player.is_alive and self.bot2.is_alive and self.check_trail_collision(self.bot2, self.player):
                print("!!! KOLIZJA: Bot 2 najechał na ślad gracza !!!")
                self.player.die("Bot 2 przejął twój ślad")
                self.bot2.area = smart_hull(self.bot2.area + self.player.area)
                self.player.area = []

            if self.player.is_alive and self.bot3.is_alive and self.check_trail_collision(self.bot3, self.player):
                print("!!! KOLIZJA: Bot 3 najechał na ślad gracza !!!")
                self.player.die("Bot 3 przejął twój ślad")
                self.bot3.area = smart_hull(self.bot3.area + self.player.area)
                self.player.area = []

            # 3. NOWE: Kolizje bot vs bot (boty zabijają się nawzajem przez najechanie na ślady)

            # Bot 1 vs Bot 2
            if self.bot.is_alive and self.bot2.is_alive:
                if self.check_trail_collision(self.bot, self.bot2):
                    print("!!! KOLIZJA: Bot 1 najechał na ślad bota 2 !!!")
                    self.bot2.die("Bot 1 przejął ślad bota 2")
                    self.bot.area = smart_hull(self.bot.area + self.bot2.area)
                    self.bot2.area = []
                elif self.check_trail_collision(self.bot2, self.bot):
                    print("!!! KOLIZJA: Bot 2 najechał na ślad bota 1 !!!")
                    self.bot.die("Bot 2 przejął ślad bota 1")
                    self.bot2.area = smart_hull(self.bot2.area + self.bot.area)
                    self.bot.area = []

            # Bot 1 vs Bot 3
            if self.bot.is_alive and self.bot3.is_alive:
                if self.check_trail_collision(self.bot, self.bot3):
                    print("!!! KOLIZJA: Bot 1 najechał na ślad bota 3 !!!")
                    self.bot3.die("Bot 1 przejął ślad bota 3")
                    self.bot.area = smart_hull(self.bot.area + self.bot3.area)
                    self.bot3.area = []
                elif self.check_trail_collision(self.bot3, self.bot):
                    print("!!! KOLIZJA: Bot 3 najechał na ślad bota 1 !!!")
                    self.bot.die("Bot 3 przejął ślad bota 1")
                    self.bot3.area = smart_hull(self.bot3.area + self.bot.area)
                    self.bot.area = []

            # Bot 2 vs Bot 3
            if self.bot2.is_alive and self.bot3.is_alive:
                if self.check_trail_collision(self.bot2, self.bot3):
                    print("!!! KOLIZJA: Bot 2 najechał na ślad bota 3 !!!")
                    self.bot3.die("Bot 2 przejął ślad bota 3")
                    self.bot2.area = smart_hull(self.bot2.area + self.bot3.area)
                    self.bot3.area = []
                elif self.check_trail_collision(self.bot3, self.bot2):
                    print("!!! KOLIZJA: Bot 3 najechał na ślad bota 2 !!!")
                    self.bot2.die("Bot 3 przejął ślad bota 2")
                    self.bot3.area = smart_hull(self.bot3.area + self.bot2.area)
                    self.bot2.area = []

            # 4. Sprawdź przejęcia terenu gdy ktoś kończy rysowanie (gracz i boty)
            self.check_area_expansion()

            # 5. Warunek zwycięstwa
            player_area = self.player.calculate_polygon_area(self.player.area) if self.player.is_alive else 0
            bot_area = self.bot.calculate_polygon_area(self.bot.area) if self.bot.is_alive else 0
            bot2_area = self.bot2.calculate_polygon_area(self.bot2.area) if self.bot2.is_alive else 0
            bot3_area = self.bot3.calculate_polygon_area(self.bot3.area) if self.bot3.is_alive else 0

            if player_area > self.map_area * self.win_ratio:
                # Gracz wygrał
                for bot in [self.bot, self.bot2, self.bot3]:
                    if bot.is_alive:
                        bot.is_alive = False
                self.player.death_reason = "Zajęto >80% mapy - WYGRANA!"
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

        # Rysuj obszar gracza
        if len(self.player.area) > 2:
            color = (200, 220, 255) if self.player.is_alive else (150, 150, 150)
            border = (0, 0, 200) if self.player.is_alive else (100, 100, 100)
            pygame.draw.polygon(self.screen, color, self.player.area)
            pygame.draw.polygon(self.screen, border, self.player.area, 2)

        # Rysuj wszystkie postacie (każdy bot rysuje się sam ze swoim kolorem)
        self.bot.draw(self.screen)
        self.bot2.draw(self.screen)
        self.bot3.draw(self.screen)
        self.player.draw(self.screen)

        # Rysuj procenty obszarów
        font = pygame.font.SysFont("arial", 22)
        entities = [
            (self.player, (0, 0, 200)),
            (self.bot, self.bot.color),
            (self.bot2, self.bot2.color),
            (self.bot3, self.bot3.color),
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

        # Pokaż typ otoczki
        hull_type = "Concave (Realistic)" if constants.USE_CONCAVE_HULL else "Convex (Simple)"
        hull_text = self.font.render(f"Hull: {hull_type}", True, (100, 100, 100))
        self.screen.blit(hull_text, (10, 40))

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