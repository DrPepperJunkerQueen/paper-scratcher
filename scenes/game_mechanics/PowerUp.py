import pygame
import math
import random
import constants


class PowerUp:
    def __init__(self, x, y, powerup_type="speed"):
        self.x = x
        self.y = y
        self.size = 20
        self.type = powerup_type
        self.collected = False
        self.pulse_timer = 0
        self.spawn_animation = 60

        self.colors = {
            "speed": (255, 255, 0),
            "size": (0, 255, 255),
            "shield": (255, 0, 255)
        }

        self.color = self.colors.get(powerup_type, (255, 255, 255))

    def update(self):
        self.pulse_timer += 1
        if self.spawn_animation > 0:
            self.spawn_animation -= 1

    def check_collision(self, entity):
        if self.collected:
            return False

        distance = math.sqrt((self.x - entity.x) ** 2 + (self.y - entity.y) ** 2)
        collision_distance = self.size // 2 + entity.size // 2

        if distance <= collision_distance:
            self.collected = True
            return True

        return False

    def draw(self, screen):
        if self.collected:
            return

        pulse_size = self.size + int(3 * math.sin(self.pulse_timer * 0.2))

        if self.spawn_animation > 0:
            alpha_factor = 1 - (self.spawn_animation / 60.0)
            pulse_size = int(pulse_size * alpha_factor)
            if pulse_size <= 0:
                return

        outer_color = tuple(min(255, c + 50) for c in self.color)
        pygame.draw.circle(screen, outer_color, (int(self.x), int(self.y)), pulse_size)

        inner_size = max(1, pulse_size - 4)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), inner_size)

        center_size = max(1, inner_size - 6)
        center_color = tuple(max(0, c - 100) for c in self.color)
        pygame.draw.circle(screen, center_color, (int(self.x), int(self.y)), center_size)

        if self.type == "speed":
            arrow_points = [
                (self.x + center_size - 2, self.y),
                (self.x - center_size + 2, self.y - center_size // 2),
                (self.x - center_size + 2, self.y + center_size // 2)
            ]
            pygame.draw.polygon(screen, (255, 255, 255), arrow_points)


class PowerUpManager:
    def __init__(self):
        self.powerups = []
        self.spawn_timer = 0
        self.spawn_interval = 300
        self.max_powerups = 3

    def update(self):
        for powerup in self.powerups[:]:
            powerup.update()
            if powerup.collected:
                self.powerups.remove(powerup)

        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval and len(self.powerups) < self.max_powerups:
            self.spawn_powerup()
            self.spawn_timer = 0

    def spawn_powerup(self):
        margin = 80

        x = random.randint(margin, constants.SCREEN_WIDTH - margin)
        y = random.randint(margin, constants.SCREEN_HEIGHT - margin)

        powerup_type = "speed"

        new_powerup = PowerUp(x, y, powerup_type)
        self.powerups.append(new_powerup)

    def check_collisions(self, entity):
        for powerup in self.powerups:
            if powerup.check_collision(entity):
                return powerup.type
        return None

    def draw(self, screen):
        for powerup in self.powerups:
            powerup.draw(screen)

    def clear_all(self):
        self.powerups.clear()