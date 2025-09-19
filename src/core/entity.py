import math

import pygame

from .const import *
from .entity import Entity

assets = None
settings = None

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, name="", image=None):
        super().__init__()
        self.name = name
        self.image = image
        if image:
            self.image = pygame.transform.scale(image, (w, h))
        else:
            self.image = pygame.Surface((w, h))
            self.image.fill(DARK_PURPLE)
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface, camera, puzzle_manager=None):
        surface.blit(self.image, camera.apply(self.rect))
