import numpy as np
from ..utils.utils import get_rot_mat
from .dynamic import Dynamic
from .collidable import Collidable
from .obstacle import Obstacle
from time import time

class Bot(Dynamic, Collidable):

    # Collidable properties
    BOX_HEIGHT = 70
    BOX_WIDTH = 70
    RADIUS = 35
    SHAPE = 0

    # Bot properties
    MAX_HEALTH = 100

    # Dynamic properties
    MAX_SPEED = 80.
    MAX_ANG_SPEED = 2.

    def __init__(self, team, game, type=0, position=None, rotation=None):

        self.team = team
        self.game = game
        self.speed = np.array([0,0], dtype=np.float64)
        self.ang_speed = 0.
        self.id = hash(time())

        self.health = self.MAX_HEALTH

        # In pixels, [x,y]
        if position is not None:
            self.position = np.array(position, dtype=np.float64)
        else:
            if team == 'a':
                self.position = np.array([600,400], dtype=np.float64)
            else:
                self.position = np.array([200, 400])


        # Radians from rotation 0 (facing upwards), rot > 0 = anti-clockwise
        if rotation is not None:
            self.rotation = rotation
        else:
            self.rotation = 0.

        self.type = type

    def shoot(self):
        # Get cannon location and direction
        bbox = self.get_bbox()
        cannon_pos = (bbox[0] + bbox[-1]) / 2

        self.game.add_projectile(Projectile(cannon_pos, self.rotation,self.team))

    def handle_collision(self, collidable):
        if type(collidable) == Bot:
            return 1
        elif type(collidable) == Projectile:
            if collidable.team != self.team:
                self.health -= collidable.damage
        elif type(collidable) == Obstacle:
            return 1
        return 0

from .projectile import Projectile