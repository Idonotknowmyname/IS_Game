from ..sprites.bot import Bot
from ..sprites.obstacle import Obstacle
from ..utils.utils import colliding
from ..utils.utils import get_rot_mat
from ..sprites.projectile import Projectile

import numpy as np

class BaseController(Bot):

    def __init__(self, team, game, type=0, position=None, rotation=None):
        super(BaseController, self).__init__(team,game,type,position,rotation)

    def take_action(self):
        pass

    def is_target_visible(self, target):
        # Create a very thin rectangular obstacle (line between bots) and check its collisions
        # Calculate distance and direction of target
        distance_vec = target.position - self.position
        distance = np.linalg.norm(distance_vec)
        direction = np.arctan2(distance_vec[1], distance_vec[0])
        direction = (-direction + np.pi / 2) % (np.pi * 2)

        # Create the obstacle
        thickness = 2
        length = abs(distance - (self.RADIUS + target.RADIUS) - 5)
        obs = Obstacle((target.position + self.position) / 2, length, thickness, direction)

        # Loop through game objects and check if it collides with other obstacles
        for obj in self.game.game_objects:
            if isinstance(obj, Obstacle):
                if colliding(obs, obj):
                    return False

        return True

    def obstacles_on_path(self, target):
        # Create a very thin rectangular obstacle (line between bots) and check its collisions
        # Calculate distance and direction of target
        distance_vec = target.position - self.position
        distance = np.linalg.norm(distance_vec)
        direction = np.arctan2(distance_vec[1], distance_vec[0])
        direction = (-direction + np.pi / 2) % (np.pi * 2)

        # Create the obstacle
        thickness = 2
        length = abs(distance - (self.RADIUS + target.RADIUS) - 5)
        obs = Obstacle((target.position + self.position) / 2, length, thickness, direction)

        # List of obstacles
        obstacles = []

        # If the target is visible
        visible = True
        # Loop through game objects and check if it collides with other obstacles
        for obj in self.game.game_objects:
            if isinstance(obj, Obstacle):
                if colliding(obs, obj):
                    obstacles.append(obj)

        return obstacles