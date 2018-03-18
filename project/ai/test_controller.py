from ..sprites.bot import Bot
from ..sprites.obstacle import Obstacle
from ..utils.utils import colliding

import numpy as np

class TestController(Bot):

    def __init__(self, team, game, type=0, position=None, rotation=None):
        super(TestController, self).__init__(team,game,type,position,rotation)

    def take_action(self):

        #Get the first bot from enemy team
        opponents = self.game.team_b if self.team == 'a' else self.game.team_a

        #Choose first opponen as target
        target = opponents[0]

        #parameters for the target location
        distance_vec = target.position - self.position
        direction = np.arctan2(distance_vec[1],distance_vec[0])
        direction = (-direction + np.pi / 2) % (np.pi * 2)
        distance = np.linalg.norm(distance_vec)

        # Match rotation
        diff_rotation = (direction-self.rotation) % (np.pi*2)

        if abs(diff_rotation) < abs((np.pi*2 - diff_rotation) % (np.pi*2)):
            self.ang_speed = np.sign(diff_rotation)
        else:
            self.ang_speed = -np.sign(diff_rotation)

        # Shoot only if sight is clear

        if self.is_target_visible(target):
            self.set_speed([0,1])
            # self.shoot()
        else:
            self.set_speed([1,0])


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

        # If the target is visible
        visible = True
        # Loop through game objects and check if it collides with other obstacles
        for obj in self.game.game_objects:
            if isinstance(obj, Obstacle):
                if colliding(obs, obj):
                    return False

        return True
