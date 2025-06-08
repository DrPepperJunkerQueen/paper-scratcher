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
        self.mode = "explore"
        self.steps_outside = 0
        self.is_alive = True
        self.death_reason = ""
        self.just_finished_drawing = False

        self.other_players = []

        self.captured_points = []
        self.captured_points_timer = 0

        self.triangles = []

        self.speed_boost_timer = 0
        self.base_speed_multiplier = 1.0
        self.speed_boost_multiplier = 2.0
        self.speed_boost_duration = 300

        self.target_powerup = None
        self.powerup_search_range = 100
        self.powerup_chase_time = 0

        margin = 40
        self.area = [
            (x - margin, y - margin),
            (x + margin, y - margin),
            (x + margin, y + margin),
            (x - margin, y + margin)
        ]

    def apply_speed_powerup(self):
        self.speed_boost_timer = self.speed_boost_duration

    def get_current_speed_multiplier(self):
        if self.speed_boost_timer > 0:
            return self.speed_boost_multiplier
        return self.base_speed_multiplier

    def update_powerup_timers(self):
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= 1

    def set_other_players(self, players):
        self.other_players = players

    def update_captured_points_timer(self):
        if self.captured_points_timer > 0:
            self.captured_points_timer -= 1
            if self.captured_points_timer <= 0:
                self.captured_points = []

    def find_nearest_powerup(self, powerups):
        nearest_powerup = None
        min_distance = self.powerup_search_range

        for powerup in powerups:
            if powerup.collected:
                continue

            distance = math.sqrt((powerup.x - self.x) ** 2 + (powerup.y - self.y) ** 2)
            if distance < min_distance:
                min_distance = distance
                nearest_powerup = powerup

        return nearest_powerup

    def should_chase_powerup(self):
        if self.speed_boost_timer > 0:
            return False

        current_pos = (self.x, self.y)
        if not scenes.game.point_in_polygon(current_pos, self.area):
            return False

        area_size = self.calculate_polygon_area(self.area)
        map_area = (constants.SCREEN_WIDTH - 100) * (constants.SCREEN_HEIGHT - 100)
        if area_size > map_area * 0.3:
            return False

        return True

    def calculate_polygon_area(self, points):
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
        self.just_finished_drawing = False
        self.speed_boost_timer = 0
        self.target_powerup = None

    def move(self, speed, powerups=None):
        self.update_powerup_timers()

        effective_speed = speed * self.get_current_speed_multiplier()

        current_pos = (self.x, self.y)

        if powerups and self.should_chase_powerup():
            if self.target_powerup and (self.target_powerup.collected or
                                        self.distance((self.x, self.y), (
                                        self.target_powerup.x, self.target_powerup.y)) > self.powerup_search_range):
                self.target_powerup = None
                self.mode = "explore"
                self.powerup_chase_time = 0

            if not self.target_powerup:
                self.target_powerup = self.find_nearest_powerup(powerups)
                if self.target_powerup:
                    self.mode = "powerup"
                    self.powerup_chase_time = 300

        if self.mode == "powerup" and self.target_powerup and not self.target_powerup.collected:
            self.powerup_chase_time -= 1

            if self.powerup_chase_time <= 0 or self.target_powerup.collected:
                self.target_powerup = None
                self.mode = "explore"
                self.powerup_chase_time = 0
            else:
                dx = self.target_powerup.x - self.x
                dy = self.target_powerup.y - self.y

                if abs(dx) > abs(dy):
                    self.direction = (1 if dx > 0 else -1, 0)
                else:
                    self.direction = (0, 1 if dy > 0 else -1)

        elif self.mode == "return":
            centroid = self.calculate_centroid(self.area)
            dx = centroid[0] - self.x
            dy = centroid[1] - self.y
            if abs(dx) > abs(dy):
                self.direction = (1 if dx > 0 else -1, 0)
            else:
                self.direction = (0, 1 if dy > 0 else -1)

        dx, dy = self.direction
        new_x = self.x + dx * effective_speed
        new_y = self.y + dy * effective_speed

        min_x = 50 + self.size // 2
        max_x = constants.SCREEN_WIDTH - 50 - self.size // 2
        min_y = 50 + self.size // 2
        max_y = constants.SCREEN_HEIGHT - 50 - self.size // 2

        if new_x < min_x or new_x > max_x or new_y < min_y or new_y > max_y:
            self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            if self.mode == "powerup":
                self.target_powerup = None
                self.mode = "explore"
                self.powerup_chase_time = 0
            return

        self.x = new_x
        self.y = new_y
        current_pos = (self.x, self.y)

        if scenes.game.point_in_polygon(current_pos, self.area):
            if self.is_tracing and len(self.trail) > 3:
                self.update_area()
                self.just_finished_drawing = True
            self.is_tracing = False
            self.trail = []
            self.trail_start_point = None
            self.mode = "explore"
            self.steps_outside = 0
            if self.target_powerup:
                self.target_powerup = None
                self.powerup_chase_time = 0
        else:
            self.just_finished_drawing = False
            if not self.is_tracing:
                self.is_tracing = True
                self.trail = []
                self.trail_start_point = current_pos

            min_distance = 3 if self.speed_boost_timer == 0 else 2
            if not self.trail or self.distance(current_pos, self.trail[-1]) > min_distance:
                self.trail.append(current_pos)
            self.steps_outside += 1

            if self.steps_outside > random.randint(40, 80) and self.mode != "powerup":
                self.mode = "return"

        if self.mode == "explore" and random.random() < 0.02:
            self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])

    def update_area(self):
        if len(self.trail) < 3:
            return

        new_area = self.create_area_expansion()
        if new_area and len(new_area) >= 3:
            all_captured_points = []

            for other_player in self.other_players:
                if not other_player.is_alive:
                    continue

                taken_points = [p for p in other_player.area if scenes.game.point_in_polygon(p, new_area)]
                if taken_points:
                    all_captured_points.extend(taken_points)

                    other_player.area = [p for p in other_player.area if not scenes.game.point_in_polygon(p, new_area)]

                    new_area += taken_points

                    if len(other_player.area) >= 3:
                        hull_result = scenes.game.smart_hull(other_player.area)
                        if isinstance(hull_result, tuple):
                            other_player.area = hull_result[0]
                        else:
                            other_player.area = hull_result
                    else:
                        other_player.area = []

                    hull_result = scenes.game.smart_hull(new_area)
                    if isinstance(hull_result, tuple):
                        new_area = hull_result[0]
                    else:
                        new_area = hull_result

            if all_captured_points:
                self.captured_points = all_captured_points
                self.captured_points_timer = 180

            self.area = new_area

    def create_area_expansion(self):
        smoothed_trail = scenes.game.smooth_trail(self.trail)

        interpolated_trail = scenes.game.interpolate_points(smoothed_trail, density=8)

        all_points = []
        all_points.extend(self.area)
        all_points.extend(interpolated_trail)

        if len(all_points) >= 3:
            hull, triangles = scenes.game.smart_hull(all_points)
            self.triangles = triangles
            return self.clean_area(hull)

        return None

    def clean_area(self, points):
        if len(points) < 3:
            return points

        cleaned = []
        for point in points:
            if not cleaned or self.distance(point, cleaned[-1]) > 5:
                cleaned.append(point)

        if len(cleaned) > 2 and self.distance(cleaned[0], cleaned[-1]) <= 5:
            cleaned.pop()

        if len(cleaned) < 3:
            return self.area

        return cleaned

    def distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def draw(self, screen):
        if len(self.area) > 2:
            if self.speed_boost_timer > 0:
                pulse = int(abs(math.sin(self.speed_boost_timer * 0.3)) * 30)
                light_color = (
                    min(255, self.color[0] + 100 + pulse),
                    min(255, self.color[1] + 100 + pulse),
                    min(255, self.color[2] + 100 + pulse)
                )
                dark_color = (
                    min(255, max(0, self.color[0] - 50 + pulse)),
                    min(255, max(0, self.color[1] - 50 + pulse)),
                    min(255, max(0, self.color[2] - 50 + pulse))
                )
            else:
                light_color = (
                    min(255, self.color[0] + 100),
                    min(255, self.color[1] + 100),
                    min(255, self.color[2] + 100)
                )
                dark_color = (
                    max(0, self.color[0] - 50),
                    max(0, self.color[1] - 50),
                    max(0, self.color[2] - 50)
                )

            pygame.draw.polygon(screen, light_color, self.area)
            pygame.draw.polygon(screen, dark_color, self.area, 2)

        if constants.USE_TRIANGULATION and self.triangles:
            for triangle in self.triangles:
                triangle_color = (
                    max(0, self.color[0] - 100),
                    max(0, self.color[1] - 100),
                    max(0, self.color[2] - 100)
                )
                int_triangle = [(int(p[0]), int(p[1])) for p in triangle]
                pygame.draw.polygon(screen, triangle_color, int_triangle, 2)

                for point in triangle:
                    pygame.draw.circle(screen, triangle_color, (int(point[0]), int(point[1])), 3)

        if self.captured_points and self.captured_points_timer > 0:
            for point in self.captured_points:
                pulse_size = 3 + int(2 * abs(math.sin(self.captured_points_timer * 0.3)))
                pygame.draw.circle(screen, (255, 0, 0), (int(point[0]), int(point[1])), pulse_size)
                pygame.draw.circle(screen, (255, 255, 255), (int(point[0]), int(point[1])), pulse_size + 1, 1)

        if len(self.trail) > 1:
            smoothed_trail = scenes.game.smooth_trail_for_drawing(self.trail)
            if len(smoothed_trail) > 1:
                int_trail = [(int(p[0]), int(p[1])) for p in smoothed_trail]

                if self.speed_boost_timer > 0:
                    trail_color = (255, 100, 100)
                    trail_width = 5
                else:
                    trail_color = (255, 0, 0)
                    trail_width = 3

                pygame.draw.lines(screen, trail_color, False, int_trail, trail_width)

        bot_color = self.color
        if self.speed_boost_timer > 0:
            pulse = int(abs(math.sin(self.speed_boost_timer * 0.5)) * 50)
            bot_color = (
                min(255, self.color[0] + pulse),
                min(255, self.color[1] + pulse),
                min(255, self.color[2] + pulse)
            )

        pygame.draw.rect(
            screen,
            bot_color,
            (self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
        )

        if self.target_powerup and not self.target_powerup.collected:
            pygame.draw.line(screen, (255, 255, 0),
                             (int(self.x), int(self.y)),
                             (int(self.target_powerup.x), int(self.target_powerup.y)), 2)

            arrow_points = [
                (self.x, self.y - self.size),
                (self.x - 5, self.y - self.size - 8),
                (self.x + 5, self.y - self.size - 8)
            ]
            pygame.draw.polygon(screen, (255, 255, 0), arrow_points)

    def calculate_centroid(self, points):
        if not points:
            return (0, 0)
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return (x, y)