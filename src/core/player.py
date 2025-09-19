import math

import pygame

from const import *
from entity import Entity

assets = None
settings = None


class Player(Entity):
    def __init__(self, x, y):
        size = 32
        super().__init__(x, y, size, size, name="player")

        self.animation_timer = 0
        self.animation_speed = 0.2
        self.bob_height = 2

        self.speed = 5
        self.dx, self.dy = 0, 0
        self.is_walking = False

        self.image = pygame.Surface((size, size), pygame.SRCALPHA)

        pygame.draw.circle(self.image, CYAN, (size // 2, size // 2), size // 2)

        self.speed = 5
        self.dx, self.dy = 0, 0
        self.is_walking = False

    def update(self, walls):
        self.get_input()
        self.move(walls)
        self.update_sound()

    def animate(self):
        if self.is_walking:
            self.animation_timer += self.animation_speed
            offset_y = int(math.sin(self.animation_timer) * self.bob_height)

            animated_image = pygame.Surface(self.base_image.get_size(), pygame.SRCALPHA)
            animated_image.blit(self.base_image, (0, offset_y))
            self.image = animated_image
        else:
            self.animation_timer = 0
            self.image = self.base_image

    def get_input(self):
        keys = pygame.key.get_pressed()
        self.dx, self.dy = 0, 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: self.dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.dx += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]: self.dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: self.dy += self.speed

    def update_sound(self):
        is_moving_now = self.dx != 0 or self.dy != 0
        if is_moving_now and not self.is_walking:
            self.is_walking = True
            assets.play_sound("walk", loops=-1)
        elif not is_moving_now and self.is_walking:
            self.is_walking = False
            sound = assets.get_sound("walk")
            if sound: sound.stop()

    def stop_sound(self):
        if self.is_walking:
            self.is_walking = False
            sound = assets.get_sound("walk")
            if sound: sound.stop()

    def move(self, collidables):
        self.rect.x += self.dx
        self.check_collision('x', collidables)
        self.rect.y += self.dy
        self.check_collision('y', collidables)

    def check_collision(self, direction, collidables):
        for entity in collidables:
            if self.rect.colliderect(entity.rect):
                if direction == 'x':
                    if self.dx > 0: self.rect.right = entity.rect.left
                    if self.dx < 0: self.rect.left = entity.rect.right
                if direction == 'y':
                    if self.dy > 0: self.rect.bottom = entity.rect.top
                    if self.dy < 0: self.rect.top = entity.rect.bottom

    def draw(self, surface, camera):
        surface.blit(self.image, camera.apply(self.rect))
