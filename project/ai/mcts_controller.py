import numpy as np
from .state_controller import StateController
from ..sprites.bot import Bot
from ..sprites.point import Point
from .mcts_utils.combat_mcts import CombatMCTS

class MCTSController(StateController):

    is_simulated = False

    def take_action(self):
        if not self.is_simulated:
            super(MCTSController, self).take_action()

    def select_state(self):
        # # Check if an opponent is visible
        # opponents = list(filter(lambda x: self.is_target_visible(x), self.get_opponents()))
        # if  len(opponents) > 0:
        #     # Ask state-MCTS what state to go in
        #     pass
        # # Otherwise, just stay in current state
        # Check if an opponent is visible
        opponents = list(filter(lambda x: self.is_target_visible(x), self.get_opponents()))
        if len(opponents) > 0:
            # Closest opponent as target
            closest_opponent_index = np.argmin(
                [np.linalg.norm(self.get_position() - x.get_position()) for x in opponents])
            index = closest_opponent_index if type(closest_opponent_index) is np.int64 else closest_opponent_index[0]

            self.target = opponents[index]

            # Change state to shoot
            self.current_state = self.states["Shoot"]

        # Check if opponent was visible
        elif self.target is not None and isinstance(self.target, Bot):
            self.target = Point(self.target.get_position())
            self.path_to_target = self.pathfind(self.target)
            self.current_state = self.states["Search"]

        # Else change to roam
        elif self.target is None:
            self.current_state = self.states["Roam"]

    # def roam(self):
    #     if (self.path_to_target is None) | (self.is_path_removable()):
    #         # Ask roam-MCTS for a new path
    #         pass
    #     else:
    #         self.follow_path()

    def search(self):
        if (self.path_to_target is None) | (self.is_path_removable()):
            # Go to roam state
            self.path_to_target = None
            self.current_state = self.states["Roam"]
        else:
            self.follow_path()

    def shoot(self):
        # Ask combat-MCTS for directions
        advisor = CombatMCTS(self.game, self)
        advisor.take_action()
