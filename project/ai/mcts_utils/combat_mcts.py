from ...sprites.bot import Bot
from ...sprites.obstacle import Obstacle
from ...sprites.point import Point
from ...utils.utils import colliding
from ...utils.utils import get_rot_mat
from ...sprites.projectile import Projectile

import numpy as np

class CombatMCTS():

    current_game = None
    self_bot = None

    simu_self = None
    simu_game = None
    simu_steps = None
    time_depth = 5 # seconds
    fps = 10
    simu_count = 0
    max_simu_count = 30

    # Value-attempt tuples for each action
    action_scores = {"left": [0,0],
                     "right": [0,0],
                     "up": [0,0],
                     "down": [0,0],
                     "turnc": [0,0],
                     "turncc": [0,0],
                     "shoot": [0,0],
                     "wait": [0,0]}

    actions = None
    self_actions = None

    def __init__(self, game, bot):
        self.current_game = game
        self.self_bot = bot
        self.simu_steps = self.time_depth * self.fps

        # Simu actions
        self.actions = {"left": lambda: self.simu_self.set_speed([-1,0]),
                   "right": lambda: self.simu_self.set_speed([1,0]),
                   "up": lambda: self.simu_self.set_speed([0,1]),
                   "down": lambda: self.simu_self.set_speed([0,-1]),
                   "turnc": lambda: self.simu_self.set_angular_speed(1),
                   "turncc": lambda: self.simu_self.set_angular_speed(-1),
                   "shoot": lambda: self.simu_self.shoot(),
                   "wait": lambda: 0}


        # Executable actions
        self.self_actions = {"left": lambda: self.self_bot.set_speed([-1,0]),
                   "right": lambda: self.self_bot.set_speed([1,0]),
                   "up": lambda: self.self_bot.set_speed([0,1]),
                   "down": lambda: self.self_bot.set_speed([0,-1]),
                   "turnc": lambda: self.self_bot.set_angular_speed(1),
                   "turncc": lambda: self.self_bot.set_angular_speed(-1),
                   "shoot": lambda: self.self_bot.shoot(),
                   "wait": lambda: 0}

    def take_action(self):

        for i in range(self.max_simu_count):
            # Choose action on exploration/exploitation
            action_index = np.argmax([self.exploreExploit(x) for x in self.action_scores.keys()])
            action = list(self.action_scores.keys())[action_index[0]]

            # Run a simulation for that action
            self.simulate(action)

        # Choose maximum value action
        action_index = np.argmax([x[0]/x[1] for x in self.action_scores.values()])
        action = list(self.action_scores.keys())[action_index[0]]

        # Execute the action for the self_bot
        self.self_actions[action]()

        pass

    # Run a single simulation and update the action_score
    def simulate(self, action):

        self.simu_count += 1

        # Clone the current game
        self.simu_game = self.current_game.deepcopy()

        # Find the simulated self
        for bot in self.simu_game.get_game_objects("bot"):
            if bot.get_position() == self.self_bot.get_position():
                self.simu_self = bot

        # Run the simulation
        for i in range(self.simu_steps):

            # Execute action
            current_action = action
            self.actions[current_action]()
            self.action_scores[current_action][1] += 1

            # Run a timestep
            self.simu_game.time_step(1 / self.fps)
            self.simu_game.resolve_collisions()

            # In case of getting hit, we decrease the action score
            if self.simu_self.health < self.self_bot.health:
                self.action_scores[current_action][1] -= 2

            # In case of an enemy getting hit, we increase action score
            for bot in self.simu_game.step_hits.keys():
                if self.simu_game.step_hits[bot] > 0 and self.simu_game.step_hits[bot].team == self.simu_self.team:
                    self.action_scores[current_action][1] += 1

    def exploreExploit(self, action):
        wi = self.action_scores[action][0]
        ni = self.action_scores[action][1]

        Ni = self.simu_count
        c = np.sqrt(2)

        return (wi / ni) + (c * np.sqrt(np.log(Ni)/ni))
