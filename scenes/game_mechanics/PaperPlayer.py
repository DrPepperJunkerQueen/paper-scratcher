import pygame
import constants
import math
import random
import scenes.game


class PaperPlayer:
    def __init__(self, x, y, color=(0, 0, 255), bot=None):
        self.x = x
        self.y = y
        self.size = constants.SKIN_SIZE
        self.visual_size = constants.SKIN_SIZE * 2.5
        self.color = color
        self.direction = (1, 0)
        self.trail = []
        self.is_tracing = False
        self.trail_start_point = None
        self.is_alive = True
        self.death_reason = ""
        self.bot = bot
        self.just_finished_drawing = False
        self.other_bots = []

        self.captured_points = []
        self.captured_points_timer = 0

        self.triangles = []

        self.speed_boost_timer = 0
        self.base_speed_multiplier = 1.0
        self.speed_boost_multiplier = 2.0
        self.speed_boost_duration = 300
        self.powerup_sound = None

        self.skin_image = None
        self.load_skin()

        margin = 40
        self.area = [
            (x - margin, y - margin),
            (x + margin, y - margin),
            (x + margin, y + margin),
            (x - margin, y + margin)
        ]

    def apply_speed_powerup(self):
        self.speed_boost_timer = self.speed_boost_duration
        try:
            self.powerup_sound = pygame.mixer.Sound("resources/MyLifebelikememe.mp3")
            self.powerup_sound.set_volume(0.05)
            self.powerup_sound.play()
        except pygame.error:
            self.powerup_sound = None

    def get_current_speed_multiplier(self):
        if self.speed_boost_timer > 0:
            return self.speed_boost_multiplier
        return self.base_speed_multiplier

    def update_powerup_timers(self):
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer == 0:
                if self.powerup_sound:
                    self.powerup_sound.stop()
                    self.powerup_sound = None

    def update_captured_points_timer(self):
        if self.captured_points_timer > 0:
            self.captured_points_timer -= 1
            if self.captured_points_timer <= 0:
                self.captured_points = []

    def load_skin(self):
        try:
            if constants.SELECTED_SKIN_INDEX < len(constants.SKIN_IMAGE_PATHS):
                skin_path = constants.SKIN_IMAGE_PATHS[constants.SELECTED_SKIN_INDEX]
                self.skin_image = pygame.image.load(skin_path).convert_alpha()
                self.skin_image = pygame.transform.smoothscale(self.skin_image,
                                                               (int(self.visual_size), int(self.visual_size)))
        except (pygame.error, IndexError):
            self.skin_image = None

    def move(self, speed):
        if not self.is_alive:
            return

        self.update_powerup_timers()

        effective_speed = speed * self.get_current_speed_multiplier()

        dx, dy = self.direction
        new_x = self.x + dx * effective_speed
        new_y = self.y + dy * effective_speed

        min_x = 50 + self.size // 2
        max_x = constants.SCREEN_WIDTH - 50 - self.size // 2
        min_y = 50 + self.size // 2
        max_y = constants.SCREEN_HEIGHT - 50 - self.size // 2

        if new_x < min_x or new_x > max_x or new_y < min_y or new_y > max_y:
            self.x = max(min_x, min(max_x, new_x))
            self.y = max(min_y, min(max_y, new_y))
            return

        self.x = new_x
        self.y = new_y
        current_pos = (self.x, self.y)

        if self.is_tracing and self.check_trail_collision(current_pos):
            self.die("Collision with own trail")
            return

        if scenes.game.point_in_polygon(current_pos, self.area):
            if self.is_tracing and len(self.trail) > 3:
                self.update_area()
                self.just_finished_drawing = True
            self.is_tracing = False
            self.trail = []
            self.trail_start_point = None
        else:
            self.just_finished_drawing = False
            if not self.is_tracing:
                self.is_tracing = True
                self.trail = []
                self.trail_start_point = current_pos

            min_distance = 3 if self.speed_boost_timer == 0 else 2
            if not self.trail or self.distance(current_pos, self.trail[-1]) > min_distance:
                self.trail.append(current_pos)

    def check_trail_collision(self, current_pos):
        if len(self.trail) < 10:
            return False

        for i in range(len(self.trail) - 8):
            if i + 1 < len(self.trail) - 8:
                p1 = self.trail[i]
                p2 = self.trail[i + 1]

                dist = scenes.game.distance_point_to_segment(current_pos, p1, p2)
                if dist < self.size // 2 + 3:
                    return True

        return False

    def die(self, reason):
        self.is_alive = False
        self.death_reason = reason
        self.just_finished_drawing = False
        self.speed_boost_timer = 0
        if self.powerup_sound:
            self.powerup_sound.stop()
            self.powerup_sound = None

        # Zatrzymaj wszystkie dźwięki i odtwórz dźwięk porażki
        pygame.mixer.stop()
        try:
            defeat_sound = pygame.mixer.Sound("resources/defeat.mp3")
            defeat_sound.set_volume(0.05)
            defeat_sound.play()
        except pygame.error:
            pass

    def reset(self):
        self.x = constants.SCREEN_WIDTH // 2
        self.y = constants.SCREEN_HEIGHT // 2
        self.is_alive = True
        self.death_reason = ""
        self.trail = []
        self.is_tracing = False
        self.trail_start_point = None
        self.direction = (1, 0)
        self.just_finished_drawing = False
        self.speed_boost_timer = 0
        self.powerup_sound = None
        self.load_skin()

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
            for bot in self.other_bots:
                if not bot.is_alive:
                    continue

                taken_points = [p for p in bot.area if scenes.game.point_in_polygon(p, new_area)]
                if taken_points:
                    bot.area = [p for p in bot.area if not scenes.game.point_in_polygon(p, new_area)]

                    new_area += taken_points

                    if len(bot.area) >= 3:
                        hull_result = scenes.game.smart_hull(bot.area)
                        if isinstance(hull_result, tuple):
                            bot.area = hull_result[0]
                        else:
                            bot.area = hull_result
                    else:
                        bot.area = []

                    hull_result = scenes.game.smart_hull(new_area)
                    if isinstance(hull_result, tuple):
                        new_area = hull_result[0]
                    else:
                        new_area = hull_result

            self.area = new_area

    def create_simple_expansion(self):
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

    def calculate_polygon_area(self, points):
        if len(points) < 3:
            return 0

        area = 0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1] - points[j][0] * points[i][1]

        return abs(area) / 2

    def calculate_centroid(self, points):
        if not points:
            return (0, 0)

        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return (x, y)

    def draw(self, screen):
        if constants.USE_TRIANGULATION and self.triangles:
            for triangle in self.triangles:
                triangle_color = (0, 0, 150) if self.is_alive else (80, 80, 80)
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
                if self.is_alive:
                    if self.speed_boost_timer > 0:
                        trail_color = (255, 100, 100)
                        trail_width = 5
                    else:
                        trail_color = (255, 0, 0)
                        trail_width = 3
                    pygame.draw.lines(screen, trail_color, False, int_trail, trail_width)
                else:
                    pygame.draw.lines(screen, (150, 0, 0), False, int_trail, 3)

        if self.skin_image and self.is_alive:
            skin_rect = self.skin_image.get_rect(center=(self.x, self.y))

            if self.speed_boost_timer > 0:
                pulse = int(abs(math.sin(self.speed_boost_timer * 0.5)) * 10)
                glow_size = self.visual_size // 2 + pulse + 10
                glow_color = (255, 255, 0, 100)

                for i in range(3):
                    glow_radius = glow_size - i * 3
                    glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2))
                    glow_surface.set_alpha(50 - i * 15)
                    glow_surface.fill((255, 255, 0))
                    glow_rect = glow_surface.get_rect(center=(self.x, self.y))

            screen.blit(self.skin_image, skin_rect)
        else:
            player_color = self.color if self.is_alive else (100, 100, 100)

            if self.is_alive and self.speed_boost_timer > 0:
                pulse = int(abs(math.sin(self.speed_boost_timer * 0.3)) * 50)
                player_color = (min(255, player_color[0] + pulse),
                                min(255, player_color[1] + pulse),
                                player_color[2])

            pygame.draw.rect(
                screen,
                player_color,
                (self.x - self.visual_size // 2, self.y - self.visual_size // 2,
                 int(self.visual_size), int(self.visual_size))
            )