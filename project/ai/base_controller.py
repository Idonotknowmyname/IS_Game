from ..sprites.bot import Bot
from ..sprites.obstacle import Obstacle
from ..sprites.point import Point
from ..utils.utils import colliding
from ..utils.utils import get_rot_mat
from ..sprites.projectile import Projectile

import numpy as np

class BaseController(Bot):

    def __init__(self, team, game, type=0, position=None, rotation=None):
        super(BaseController, self).__init__(team,game,type,position,rotation)

    def take_action(self):
        target = self.get_opponents()[0]

        self.rotate_towards(target)

        # Sounds good, it doesn't work
        if self.is_target_visible(target):
            self.shoot()

    def rotate_towards(self, target):
        # parameters for the target location
        distance_vec = target.position - self.position
        direction = np.arctan2(distance_vec[1], distance_vec[0])
        direction = (-direction + np.pi / 2) % (np.pi * 2)
        distance = np.linalg.norm(distance_vec)

        # Match rotation
        diff_rotation = (direction - self.rotation) % (np.pi * 2)

        # Minimum deviation
        eps = np.pi/128

        if min(abs((np.pi * 2 - diff_rotation) % (np.pi * 2)), abs(diff_rotation)) < eps:
            self.ang_speed = 0
        elif abs(diff_rotation) < abs((np.pi * 2 - diff_rotation) % (np.pi * 2)):
            self.ang_speed = np.sign(diff_rotation)
        else:
            self.ang_speed = -np.sign(diff_rotation)

    def is_target_visible(self, target):
        # Create a very thin rectangular obstacle (line between bots) and check its collisions
        # Calculate distance and direction of target
        distance_vec = target.position - self.position
        distance = np.linalg.norm(distance_vec)
        direction = np.arctan2(distance_vec[1], distance_vec[0])
        direction = (-direction + np.pi / 2) % (np.pi * 2)

        # Create the obstacle
        thickness = Projectile.RADIUS * 2
        length = abs(distance - (self.RADIUS + target.RADIUS) - 5)
        obs = Obstacle((target.position + self.position) / 2, length, thickness, direction)

        # Loop through game objects and check if it collides with other obstacles
        for obj in self.game.get_game_objects('obstacle'):
            if colliding(obs, obj):
                return False

        return True

    def is_target_visible_new(self, target):
        distance_vec = target.position - self.position

        # Raycasting
        steps = 25

        for i in range(steps):
            displacement = distance_vec * (i / float(steps))

            for obj in self.game.get_game_objects('obstacle'):
                if not obj.is_wall and colliding(Point(self.position + displacement), obj):
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
        for obj in self.game.get_game_objects('obstacle'):
            if colliding(obs, obj):
                obstacles.append(obj)

        return obstacles