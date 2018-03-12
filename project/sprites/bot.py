import numpy as np
from ..utils.utils import get_rot_mat
from .dynamic import Dynamic
from .collidable import Collidable
from .obstacle import Obstacle
from time import time

class Bot(Dynamic, Collidable):

    # Collidable properties
    BOX_HEIGHT = 70 # Overwritten in init
    BOX_WIDTH = 70 # Overwritten in init
    RADIUS = 20
    SHAPE = 0

    # Bot properties
    MAX_HEALTH = 100
    # In seconds
    RECHARGING_TIME = 1

    # Dynamic properties
    MAX_SPEED = 80.
    MAX_ANG_SPEED = 2.

    def __init__(self, team, game, type=0, position=None, rotation=None):

        self.BOX_HEIGHT = 2*self.RADIUS
        self.BOX_WIDTH = 2*self.RADIUS

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

        self.last_shot_time = time()

    def shoot(self):

        if time() - self.last_shot_time > self.RECHARGING_TIME:
            # Get cannon location and direction
            bbox = self.get_bbox()
            cannon_pos = (bbox[0] + bbox[-1]) / 2

            self.game.add_projectile(Projectile(cannon_pos, self.rotation, self.team))

            self.last_shot_time = time()

    # To overwrite when implementing AIs
    def take_action(self):
        pass

    def handle_collision(self, collidable):
        if isinstance(collidable, Bot):
            return 1
        elif isinstance(collidable, Projectile):
            if collidable.team != self.team and not collidable.assigned:
                self.health -= collidable.damage
        elif isinstance(collidable, Obstacle):
            return 1
        return 0

from .projectile import Projectile