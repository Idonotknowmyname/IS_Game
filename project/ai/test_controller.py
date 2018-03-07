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
        # Create a very thin rectangular obstacle (line between bots) and check its collisions

        thickness = 2
        length = abs(distance - (self.RADIUS + target.RADIUS) - 5)

        obs = Obstacle((target.position + self.position)/2, length, thickness, direction)

        # If the target is visible
        visible = True
        # Loop through game objects and check if it collides with other obstacles
        for obj in self.game.game_objects:
            if isinstance(obj, Obstacle):
                if colliding(obs, obj):
                    visible = False
                    break

        if visible:
            self.shoot()
