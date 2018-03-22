import numpy as np
from .state_controller import StateController
from ..sprites.bot import Bot
from ..sprites.point import Point

class MCTSController(StateController):


    def __init__(self, team, game, type=0, position=None, rotation=None):
        super(StateController,self).__init__(team,game,type,position,rotation)
        # Adding additional states
        self.states["Select"] = self.select()

    def select_state(self):
        # Check if an opponent is visible
        opponents = list(filter(lambda x: self.is_target_visible(x), self.get_opponents()))
        if  len(opponents) > 0:
            # Ask state-MCTS what state to go in
            pass
        # Otherwise, just stay in current state

    def roam(self):
        if (self.path_to_target is None) | (self.is_path_removable()):
            # Ask roam-MCTS for a new path
            pass
        else:
            self.follow_path()

    def search(self):
        if (self.path_to_target is None) | (self.is_path_removable()):
            # Go to roam state
            self.path_to_target = None
            self.current_state = self.states["Roam"]
        else:
            self.follow_path()

    def shoot(self):
        # Ask combat-MCTS for directions
        pass
