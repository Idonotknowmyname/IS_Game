from .dynamic import Dynamic
from .collidable import Collidable
from .bot import Bot
from .obstacle import Obstacle
import numpy as np

class Projectile(Dynamic, Collidable):

    # Dynamic properties
    MAX_SPEED = 250.
    MAX_ANG_SPEED = 0.

    # Projectile properties
    DAMAGE = 10

    # Collidable properties
    BOX_HEIGHT = 10
    BOX_WIDTH = 10
    RADIUS = 5
    SHAPE = 0

    def __init__(self, position, shooter, damage=None):
        self.position = np.array(position)
        self.rotation = shooter.rotation
        self.team = shooter.team
        self.shooter = shooter
        self.speed = np.array([0, 1])
        self.ang_speed = 0
        self.damage = self.DAMAGE if damage is None else damage

        # If damage has already been assigned (no two enemies hit with one shot)
        self.assigned = False

    def __copy__(self):
        return Projectile(self.position, self.shooter, self.damage)

    def handle_collision(self, collidable):
        if isinstance(collidable, Bot) and collidable.team != self.team:
            assigned = True
            return -1
        elif isinstance(collidable, Obstacle):
            return -1
        return 0
