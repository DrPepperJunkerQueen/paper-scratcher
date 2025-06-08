import pygame
import constants
import math
import random
from scenes.game_mechanics.PaperBot import PaperBot
from scenes.game_mechanics.PaperPlayer import PaperPlayer
from scenes.game_mechanics.PowerUp import PowerUpManager


def convex_hull(points):
    if len(points) < 3:
        return points

    start = min(points, key=lambda p: (p[1], p[0]))

    def polar_angle(p):
        return math.atan2(p[1] - start[1], p[0] - start[0])

    sorted_points = sorted([p for p in points if p != start], key=polar_angle)

    hull = [start]
    for point in sorted_points:
        while len(hull) > 1 and cross_product(hull[-2], hull[-1], point) <= 0:
            hull.pop()
        hull.append(point)

    return hull


def concave_hull_simple(points, max_edge_length=50):
    if len(points) < 3:
        return points

    convex = convex_hull(points)
    if len(convex) < 3:
        return convex

    inner_points = []
    for point in points:
        if point not in convex:
            inner_points.append(point)

    if not inner_points:
        return convex

    concave_points = []
    for i in range(len(convex)):
        current_point = convex[i]
        next_point = convex[(i + 1) % len(convex)]

        concave_points.append(current_point)

        edge_length = distance_between_points(current_point, next_point)

        if edge_length > max_edge_length:
            edge_points = []
            for inner_point in inner_points:
                dist_to_edge = distance_point_to_segment(inner_point, current_point, next_point)
                if dist_to_edge < max_edge_length * 0.3:
                    edge_points.append(inner_point)

            if edge_points:
                def distance_along_edge(p):
                    dx = next_point[0] - current_point[0]
                    dy = next_point[1] - current_point[1]
                    if dx == 0 and dy == 0:
                        return 0
                    t = ((p[0] - current_point[0]) * dx + (p[1] - current_point[1]) * dy) / (dx * dx + dy * dy)
                    return max(0, min(1, t))

                edge_points.sort(key=distance_along_edge)
                concave_points.extend(edge_points)

    return concave_points if len(concave_points) >= 3 else convex


def concave_hull_alpha_shapes(points, alpha=None):
    if alpha is None:
        alpha = constants.CONCAVE_ALPHA

    max_edge_length = 100.0 / alpha

    return concave_hull_simple(points, max_edge_length)


def smooth_trail_for_drawing(trail, smoothing_factor=2):
    if len(trail) < smoothing_factor * 2 or not constants.AREA_SMOOTHING:
        return trail

    smoothed = []
    for i in range(len(trail)):
        if i < smoothing_factor or i >= len(trail) - smoothing_factor:
            smoothed.append(trail[i])
        else:
            sum_x = 0
            sum_y = 0
            count = 0

            for j in range(-smoothing_factor, smoothing_factor + 1):
                if 0 <= i + j < len(trail):
                    weight = 1.0 - abs(j) * 0.3
                    sum_x += trail[i + j][0] * weight
                    sum_y += trail[i + j][1] * weight
                    count += weight

            if count > 0:
                smoothed.append((sum_x / count, sum_y / count))
            else:
                smoothed.append(trail[i])

    return smoothed


def delaunay_triangulation_simple(points):
    if len(points) < 3:
        return []

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
        return []

    triangles = []
    n = len(unique_points)

    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                p1, p2, p3 = unique_points[i], unique_points[j], unique_points[k]

                if abs(cross_product(p1, p2, p3)) < 1e-10:
                    continue

                is_delaunay = True
                circumcenter = calculate_circumcenter(p1, p2, p3)
                circumradius_sq = distance_between_points(circumcenter, p1) ** 2

                for l in range(n):
                    if l == i or l == j or l == k:
                        continue

                    test_point = unique_points[l]
                    dist_sq = distance_between_points(circumcenter, test_point) ** 2

                    if dist_sq < circumradius_sq - 1e-10:
                        is_delaunay = False
                        break

                if is_delaunay:
                    triangles.append([p1, p2, p3])

    return triangles


def calculate_circumcenter(p1, p2, p3):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    denom = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(denom) < 1e-10:
        return ((x1 + x2 + x3) / 3, (y1 + y2 + y3) / 3)

    ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / denom
    uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / denom

    return (ux, uy)


def triangulated_hull(points):
    if len(points) < 3:
        return points, []

    triangles = delaunay_triangulation_simple(points)
    if not triangles:
        return convex_hull(points), []

    all_hull_points = []
    expansion_radius = 8

    for triangle in triangles:
        center_x = sum(p[0] for p in triangle) / 3
        center_y = sum(p[1] for p in triangle) / 3
        center = (center_x, center_y)

        triangle_hull = []
        for point in triangle:
            triangle_hull.append(point)

            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                expanded_x = point[0] + expansion_radius * math.cos(rad)
                expanded_y = point[1] + expansion_radius * math.sin(rad)
                triangle_hull.append((expanded_x, expanded_y))

        if len(triangle_hull) >= 3:
            mini_hull = convex_hull(triangle_hull)
            all_hull_points.extend(mini_hull)

    unique_hull_points = []
    for point in all_hull_points:
        is_duplicate = False
        for existing in unique_hull_points:
            if distance_between_points(point, existing) < 5:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_hull_points.append(point)

    final_hull = convex_hull(unique_hull_points) if len(unique_hull_points) >= 3 else convex_hull(points)
    return final_hull, triangles


def smart_hull(points):
    if constants.USE_TRIANGULATION:
        hull, triangles = triangulated_hull(points)
        return hull, triangles
    elif constants.USE_CONCAVE_HULL:
        return concave_hull_alpha_shapes(points), []
    else:
        return convex_hull(points), []


def interpolate_points(points, density=5):
    if len(points) < 2 or not constants.AREA_SMOOTHING:
        return points

    interpolated = []
    for i in range(len(points)):
        current_point = points[i]
        next_point = points[(i + 1) % len(points)]

        interpolated.append(current_point)

        dx = next_point[0] - current_point[0]
        dy = next_point[1] - current_point[1]
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > density * 2:
            num_interpolated = int(distance // density)
            for j in range(1, num_interpolated):
                t = j / num_interpolated
                interp_x = current_point[0] + t * dx
                interp_y = current_point[1] + t * dy
                interpolated.append((interp_x, interp_y))

    return interpolated


def smooth_trail(trail, smoothing_factor=3):
    if len(trail) < smoothing_factor * 2 or not constants.AREA_SMOOTHING:
        return trail

    smoothed = []
    for i in range(len(trail)):
        if i < smoothing_factor or i >= len(trail) - smoothing_factor:
            smoothed.append(trail[i])
        else:
            sum_x = 0
            sum_y = 0
            count = 0

            for j in range(-smoothing_factor, smoothing_factor + 1):
                if 0 <= i + j < len(trail):
                    sum_x += trail[i + j][0]
                    sum_y += trail[i + j][1]
                    count += 1

            if count > 0:
                smoothed.append((sum_x / count, sum_y / count))
            else:
                smoothed.append(trail[i])

    return smoothed


def cross_product(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def point_in_polygon(point, polygon):
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
    intersections = []

    for i in range(len(area)):
        p1 = area[i]
        p2 = area[(i + 1) % len(area)]

        if point_on_segment(p1, p2, trail_start):
            intersections.append((i, trail_start))
        if point_on_segment(p1, p2, trail_end):
            intersections.append((i, trail_end))

    return intersections


def point_on_segment(p1, p2, point, tolerance=5):
    dist = distance_point_to_segment(point, p1, p2)
    return dist <= tolerance


def distance_point_to_segment(point, seg_start, seg_end):
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
    if len(poly1) < 3 or len(poly2) < 3:
        return poly1 if len(poly1) >= 3 else poly2

    all_points = list(poly1) + list(poly2)

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

    union_points = []
    for point in all_points:
        if (point_in_polygon(point, poly1) or point_in_polygon(point, poly2) or
                point_on_polygon_edge(point, poly1) or point_on_polygon_edge(point, poly2)):
            union_points.append(point)

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
    if len(main_poly) < 3 or len(subtract_poly) < 3:
        return main_poly

    remaining_points = []
    for point in main_poly:
        if not point_in_polygon(point, subtract_poly):
            remaining_points.append(point)

    intersection_points = []
    for i in range(len(main_poly)):
        edge1_start = main_poly[i]
        edge1_end = main_poly[(i + 1) % len(main_poly)]

        for j in range(len(subtract_poly)):
            edge2_start = subtract_poly[j]
            edge2_end = subtract_poly[(j + 1) % len(subtract_poly)]

            intersection = line_intersection(edge1_start, edge1_end, edge2_start, edge2_end)
            if intersection:
                if point_on_segment(edge1_start, edge1_end, intersection, tolerance=5):
                    intersection_points.append(intersection)

    remaining_points.extend(intersection_points)

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
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    return None


def point_on_polygon_edge(point, polygon, tolerance=5):
    for i in range(len(polygon)):
        edge_start = polygon[i]
        edge_end = polygon[(i + 1) % len(polygon)]
        if point_on_segment(edge_start, edge_end, point, tolerance):
            return True
    return False


def distance_between_points(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def calculate_territory_capture(winner_area, winner_trail, loser_area):
    if len(winner_trail) < 3:
        return winner_area, loser_area

    new_captured_area = smart_hull(winner_area + winner_trail)

    if len(new_captured_area) < 3:
        return winner_area, loser_area

    combined_winner_area = polygon_union(winner_area, new_captured_area)

    remaining_loser_area = polygon_difference(loser_area, new_captured_area)

    return combined_winner_area, remaining_loser_area


class GameScene:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 24)
        self.big_font = pygame.font.SysFont("arial", 48)
        self.next_scene = None
        self.bot = PaperBot(100, 100, color=(255, 100, 0))
        self.bot2 = PaperBot(constants.SCREEN_WIDTH - 100, constants.SCREEN_HEIGHT - 100,
                             color=(100, 255, 0))
        self.bot3 = PaperBot(100, constants.SCREEN_HEIGHT - 100, color=(0, 255, 100))
        self.player = PaperPlayer(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2, bot=self.bot)

        self.powerup_manager = PowerUpManager()

        self.setup_player_references()
        self.speed = 2
        self.game_over_timer = 0
        self.map_area = (constants.SCREEN_WIDTH - 100) * (constants.SCREEN_HEIGHT - 100)
        self.win_ratio = 0.8

    def setup_player_references(self):
        self.bot.set_other_players([self.player, self.bot2, self.bot3])
        self.bot2.set_other_players([self.player, self.bot, self.bot3])
        self.bot3.set_other_players([self.player, self.bot, self.bot2])
        self.player.other_bots = [self.bot, self.bot2, self.bot3]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from scenes.main_menu import MainMenu
                self.next_scene = MainMenu(self.screen)
            elif event.key == pygame.K_r and (
                    not self.player.is_alive or not self.bot.is_alive or not self.bot2.is_alive or not self.bot3.is_alive):
                self.bot = PaperBot(100, 100, color=(255, 100, 0))
                self.bot2 = PaperBot(constants.SCREEN_WIDTH - 100, constants.SCREEN_HEIGHT - 100,
                                     color=(100, 255, 0))
                self.bot3 = PaperBot(100, constants.SCREEN_HEIGHT - 100, color=(0, 255, 100))
                self.player = PaperPlayer(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2, bot=self.bot)
                self.setup_player_references()
                self.powerup_manager.clear_all()
                self.game_over_timer = 0
            elif self.player.is_alive:
                if event.key == pygame.K_LEFT:
                    self.player.direction = (-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.player.direction = (1, 0)
                elif event.key == pygame.K_UP:
                    self.player.direction = (0, -1)
                elif event.key == pygame.K_DOWN:
                    self.player.direction = (0, 1)

    def check_area_expansion(self):
        if (self.player.is_alive and not self.player.is_tracing and
                hasattr(self.player, 'just_finished_drawing') and self.player.just_finished_drawing):

            self.player.just_finished_drawing = False

            for bot_name, bot in [("Bot1", self.bot), ("Bot2", self.bot2), ("Bot3", self.bot3)]:
                if not bot.is_alive:
                    continue

                captured_points = [p for p in bot.area if point_in_polygon(p, self.player.area)]

                if len(captured_points) > len(bot.area) * 0.3:
                    bot.area = [p for p in bot.area if not point_in_polygon(p, self.player.area)]

                    if len(bot.area) < 3:
                        bot.die(f"Stracił teren na rzecz gracza")

        if (self.bot.is_alive and not self.bot.is_tracing and
                hasattr(self.bot, 'just_finished_drawing') and self.bot.just_finished_drawing):

            self.bot.just_finished_drawing = False

            if self.player.is_alive:
                captured_points = [p for p in self.player.area if point_in_polygon(p, self.bot.area)]
                if len(captured_points) > len(self.player.area) * 0.3:
                    self.player.area = [p for p in self.player.area if not point_in_polygon(p, self.bot.area)]
                    if len(self.player.area) < 3:
                        self.player.die("Bot 1 przejął twój teren")

            for bot_name, other_bot in [("Bot2", self.bot2), ("Bot3", self.bot3)]:
                if not other_bot.is_alive:
                    continue
                captured_points = [p for p in other_bot.area if point_in_polygon(p, self.bot.area)]
                if len(captured_points) > len(other_bot.area) * 0.3:
                    other_bot.area = [p for p in other_bot.area if not point_in_polygon(p, self.bot.area)]
                    if len(other_bot.area) < 3:
                        other_bot.die(f"Stracił teren na rzecz Bot 1")

        if (self.bot2.is_alive and not self.bot2.is_tracing and
                hasattr(self.bot2, 'just_finished_drawing') and self.bot2.just_finished_drawing):

            self.bot2.just_finished_drawing = False

            if self.player.is_alive:
                captured_points = [p for p in self.player.area if point_in_polygon(p, self.bot2.area)]
                if len(captured_points) > len(self.player.area) * 0.3:
                    self.player.area = [p for p in self.player.area if not point_in_polygon(p, self.bot2.area)]
                    if len(self.player.area) < 3:
                        self.player.die("Bot 2 przejął twój teren")

            for bot_name, other_bot in [("Bot1", self.bot), ("Bot3", self.bot3)]:
                if not other_bot.is_alive:
                    continue
                captured_points = [p for p in other_bot.area if point_in_polygon(p, self.bot2.area)]
                if len(captured_points) > len(other_bot.area) * 0.3:
                    other_bot.area = [p for p in other_bot.area if not point_in_polygon(p, self.bot2.area)]
                    if len(other_bot.area) < 3:
                        other_bot.die(f"Stracił teren na rzecz Bot 2")

        if (self.bot3.is_alive and not self.bot3.is_tracing and
                hasattr(self.bot3, 'just_finished_drawing') and self.bot3.just_finished_drawing):

            self.bot3.just_finished_drawing = False

            if self.player.is_alive:
                captured_points = [p for p in self.player.area if point_in_polygon(p, self.bot3.area)]
                if len(captured_points) > len(self.player.area) * 0.3:
                    self.player.area = [p for p in self.player.area if not point_in_polygon(p, self.bot3.area)]
                    if len(self.player.area) < 3:
                        self.player.die("Bot 3 przejął twój teren")

            for bot_name, other_bot in [("Bot1", self.bot), ("Bot2", self.bot2)]:
                if not other_bot.is_alive:
                    continue
                captured_points = [p for p in other_bot.area if point_in_polygon(p, self.bot3.area)]
                if len(captured_points) > len(other_bot.area) * 0.3:
                    other_bot.area = [p for p in other_bot.area if not point_in_polygon(p, self.bot3.area)]
                    if len(other_bot.area) < 3:
                        other_bot.die(f"Stracił teren na rzecz Bot 3")

    def update(self):
        if self.player.is_alive and (self.bot.is_alive or self.bot2.is_alive or self.bot3.is_alive):
            self.powerup_manager.update()

            if self.player.is_alive:
                powerup_type = self.powerup_manager.check_collisions(self.player)
                if powerup_type == "speed":
                    self.player.apply_speed_powerup()

            if self.bot.is_alive:
                powerup_type = self.powerup_manager.check_collisions(self.bot)
                if powerup_type == "speed":
                    self.bot.apply_speed_powerup()

            if self.bot2.is_alive:
                powerup_type = self.powerup_manager.check_collisions(self.bot2)
                if powerup_type == "speed":
                    self.bot2.apply_speed_powerup()

            if self.bot3.is_alive:
                powerup_type = self.powerup_manager.check_collisions(self.bot3)
                if powerup_type == "speed":
                    self.bot3.apply_speed_powerup()

            self.player.move(self.speed)
            if self.bot.is_alive:
                self.bot.move(self.speed, self.powerup_manager.powerups)
            if self.bot2.is_alive:
                self.bot2.move(self.speed, self.powerup_manager.powerups)
            if self.bot3.is_alive:
                self.bot3.move(self.speed, self.powerup_manager.powerups)

            self.player.update_captured_points_timer()
            self.bot.update_captured_points_timer()
            self.bot2.update_captured_points_timer()
            self.bot3.update_captured_points_timer()

            if self.bot.is_alive and self.check_trail_collision(self.player, self.bot):
                self.bot.die("Kolizja ze śladem gracza")
                hull_result = smart_hull(self.player.area + self.bot.area)
                if isinstance(hull_result, tuple):
                    self.player.area = hull_result[0]
                else:
                    self.player.area = hull_result

            if self.bot2.is_alive and self.check_trail_collision(self.player, self.bot2):
                self.bot2.die("Kolizja ze śladem gracza")
                hull_result = smart_hull(self.player.area + self.bot2.area)
                if isinstance(hull_result, tuple):
                    self.player.area = hull_result[0]
                else:
                    self.player.area = hull_result

            if self.bot3.is_alive and self.check_trail_collision(self.player, self.bot3):
                self.bot3.die("Kolizja ze śladem gracza")
                hull_result = smart_hull(self.player.area + self.bot3.area)
                if isinstance(hull_result, tuple):
                    self.player.area = hull_result[0]
                else:
                    self.player.area = hull_result

            if self.player.is_alive and self.bot.is_alive and self.check_trail_collision(self.bot, self.player):
                self.player.die("Bot 1 przejął twój ślad")
                hull_result = smart_hull(self.bot.area + self.player.area)
                if isinstance(hull_result, tuple):
                    self.bot.area = hull_result[0]
                else:
                    self.bot.area = hull_result
                self.player.area = []

            if self.player.is_alive and self.bot2.is_alive and self.check_trail_collision(self.bot2, self.player):
                self.player.die("Bot 2 przejął twój ślad")
                hull_result = smart_hull(self.bot2.area + self.player.area)
                if isinstance(hull_result, tuple):
                    self.bot2.area = hull_result[0]
                else:
                    self.bot2.area = hull_result
                self.player.area = []

            if self.player.is_alive and self.bot3.is_alive and self.check_trail_collision(self.bot3, self.player):
                self.player.die("Bot 3 przejął twój ślad")
                hull_result = smart_hull(self.bot3.area + self.player.area)
                if isinstance(hull_result, tuple):
                    self.bot3.area = hull_result[0]
                else:
                    self.bot3.area = hull_result
                self.player.area = []

            if self.bot.is_alive and self.bot2.is_alive:
                if self.check_trail_collision(self.bot, self.bot2):
                    self.bot2.die("Bot 1 przejął ślad bota 2")
                    hull_result = smart_hull(self.bot.area + self.bot2.area)
                    if isinstance(hull_result, tuple):
                        self.bot.area = hull_result[0]
                    else:
                        self.bot.area = hull_result
                    self.bot2.area = []
                elif self.check_trail_collision(self.bot2, self.bot):
                    self.bot.die("Bot 2 przejął ślad bota 1")
                    hull_result = smart_hull(self.bot2.area + self.bot.area)
                    if isinstance(hull_result, tuple):
                        self.bot2.area = hull_result[0]
                    else:
                        self.bot2.area = hull_result
                    self.bot.area = []

            if self.bot.is_alive and self.bot3.is_alive:
                if self.check_trail_collision(self.bot, self.bot3):
                    self.bot3.die("Bot 1 przejął ślad bota 3")
                    hull_result = smart_hull(self.bot.area + self.bot3.area)
                    if isinstance(hull_result, tuple):
                        self.bot.area = hull_result[0]
                    else:
                        self.bot.area = hull_result
                    self.bot3.area = []
                elif self.check_trail_collision(self.bot3, self.bot):
                    self.bot.die("Bot 3 przejął ślad bota 1")
                    hull_result = smart_hull(self.bot3.area + self.bot.area)
                    if isinstance(hull_result, tuple):
                        self.bot3.area = hull_result[0]
                    else:
                        self.bot3.area = hull_result
                    self.bot.area = []

            if self.bot2.is_alive and self.bot3.is_alive:
                if self.check_trail_collision(self.bot2, self.bot3):
                    self.bot3.die("Bot 2 przejął ślad bota 3")
                    hull_result = smart_hull(self.bot2.area + self.bot3.area)
                    if isinstance(hull_result, tuple):
                        self.bot2.area = hull_result[0]
                    else:
                        self.bot2.area = hull_result
                    self.bot3.area = []
                elif self.check_trail_collision(self.bot3, self.bot2):
                    self.bot2.die("Bot 3 przejął ślad bota 2")
                    hull_result = smart_hull(self.bot3.area + self.bot2.area)
                    if isinstance(hull_result, tuple):
                        self.bot3.area = hull_result[0]
                    else:
                        self.bot3.area = hull_result
                    self.bot2.area = []

            self.check_area_expansion()

            player_area = self.player.calculate_polygon_area(self.player.area) if self.player.is_alive else 0
            bot_area = self.bot.calculate_polygon_area(self.bot.area) if self.bot.is_alive else 0
            bot2_area = self.bot2.calculate_polygon_area(self.bot2.area) if self.bot2.is_alive else 0
            bot3_area = self.bot3.calculate_polygon_area(self.bot3.area) if self.bot3.is_alive else 0

            if player_area > self.map_area * self.win_ratio:
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

        if len(self.player.area) > 2:
            color = (200, 220, 255) if self.player.is_alive else (150, 150, 150)
            border = (0, 0, 200) if self.player.is_alive else (100, 100, 100)
            pygame.draw.polygon(self.screen, color, self.player.area)
            pygame.draw.polygon(self.screen, border, self.player.area, 2)

        self.powerup_manager.draw(self.screen)

        self.bot.draw(self.screen)
        self.bot2.draw(self.screen)
        self.bot3.draw(self.screen)
        self.player.draw(self.screen)

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
        area_size = int(self.player.calculate_polygon_area(self.player.area))
        area_text = self.font.render(f"Obszar: {area_size} px²", True, (0, 0, 0))
        self.screen.blit(area_text, (10, 10))

        if self.player.is_tracing:
            status_text = self.font.render("Rysowanie", True, (255, 0, 0))
            self.screen.blit(status_text, (300, 10))
        else:
            status_text = self.font.render("W bezpiecznym obszarze", True, (0, 150, 0))
            self.screen.blit(status_text, (300, 10))

        if self.player.speed_boost_timer > 0:
            remaining_seconds = self.player.speed_boost_timer // 60 + 1
            powerup_text = self.font.render(f"PRZYŚPIESZENIE: {remaining_seconds}s", True, (255, 255, 0))
            self.screen.blit(powerup_text, (10, 70))

        if constants.USE_TRIANGULATION:
            hull_type = "Triangulated"
        elif constants.USE_CONCAVE_HULL:
            hull_type = "Concave"
        else:
            hull_type = "Convex"

        smoothing_type = "Smooth" if constants.AREA_SMOOTHING else "Sharp"
        settings_text = self.font.render(f"Hull: {hull_type} | Areas: {smoothing_type}", True, (100, 100, 100))
        self.screen.blit(settings_text, (10, 40))

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