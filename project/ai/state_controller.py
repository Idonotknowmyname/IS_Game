import numpy as np
from .pathfind_controller import PathfindController
from ..sprites.bot import Bot
from ..sprites.point import Point

class StateController(PathfindController):

    states = {}
    current_state = None

    def __init__(self, team, game, type=0, position=None, rotation=None):
        super(StateController,self).__init__(team,game,type,position,rotation)
        self.initialize_states()

    def initialize_states(self):

        # Roaming
        self.states["Roam"] = self.roam

        # Choose target
        self.states["Select"] = self.select

        # Search
        self.states["Search"] = self.search

        # Fire at target
        self.states["Shoot"] = self.shoot

        self.current_state = self.states["Roam"]

    def take_action(self):

        self.select_state()

        self.current_state()

    def select_state(self):
        # Check if an opponent is visible
        opponents = list(filter(lambda x: self.is_target_visible(x), self.get_opponents()))
        if len(opponents) > 0:
            # Closest opponent as target
            closest_opponent_index = np.argmin([np.linalg.norm(self.position() - x.position) for x in opponents])
            self.target = opponents[closest_opponent_index[0]]
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

    def roam(self):
        if (self.path_to_target is None):
            # Get a random location
            ranges = self.game.grid.shape
            location = (np.random.randint(0,ranges[0]), np.random.randint(0,ranges[1]))

            # Reroll if location is not free
            while not self.game.grid[location]:
                location = (np.random.randint(0,ranges[0]), np.random.randint(0,ranges[1]))

            self.path_to_target = self.pathfind(Point(self.get_cell_pos(location)))

        # Now there's a point to go to for sure
        if self.is_path_removable():
            self.path_to_target = None
            pass
        else:
            self.follow_path()

    def select(self):
        pass

    def search(self):
        if not self.is_path_removable():
            self.follow_path()
        else:
            self.target = None
            self.path_to_target = None

    def shoot(self):
        if self.target is not None and self.rotate_towards(self.target):
            self.shoot()

    class State:

        state_action = None

        def __init__(self, action):
            self.state_action = action

        def take_action(self):
            self.state_action(self)
