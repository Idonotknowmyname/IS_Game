from ..sprites .bot import Bot
import numpy as np

class CrudeController(Bot):

    def __init__(self, team, game, type=0, position=None, rotation=None):
        super(CrudeController, self).__init__(self,team,game,type,position,rotation)

    def take_action(self):

        #Get the first bot from enemy team
        opponents = self.game.team_b if self.team == 'a' else self.game.team_a

        #Choose first opponen as target
        target = opponents[0]

        #parameters for the target location
        distance_vec = target.position - self.position
        direction = np.arctan2(distance_vec[1],distance_vec[0])
        distance = np.linalg.norm(distance_vec)

        #Match rotation
        self.ang_speed = np.sign(direction-self.rotation-np.pi/2)

