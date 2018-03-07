from .dynamic import Dynamic
from .collidable import Collidable
from .bot import Bot
from .obstacle import Obstacle
import numpy as np

class Projectile(Dynamic, Collidable):

    # Dynamic properties
    MAX_SPEED = 200.
    MAX_ANG_SPEED = 0.

    # Projectile properties
    DAMAGE = 10

    # Collidable properties
    BOX_HEIGHT = 10
    BOX_WIDTH = 10
    RADIUS = 5
    SHAPE = 0

    def __init__(self, position, rotation, team, damage=None):
        self.position = np.array(position)
        self.rotation = rotation
        self.team = team
        self.speed = np.array([0, 1])
        self.ang_speed = 0
        self.damage = self.DAMAGE if damage is None else damage


    def handle_collision(self, collidable):
        if type(collidable) == Bot and collidable.team != self.team:
            return -1
        elif type(collidable) == Obstacle:
            return -1
        return 0
