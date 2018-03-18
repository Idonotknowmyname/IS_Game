import numpy as np
from time import time

from ..utils.utils import colliding

from ..sprites.bot import Bot
from ..sprites.dynamic import Dynamic
from ..sprites.obstacle import Obstacle
from ..sprites.collidable import Collidable

class Game:

    # Size of arena
    ARENA_WIDTH = 600
    ARENA_HEIGHT = 600

    # List of all game_objects
    game_objects = []

    # Teams of bots
    team_a = []
    team_b = []

    cfg = {}

    def __init__(self, n_agents, wind_size, **kwargs):
        self.team_a = []
        self.team_b = []

        self.window_size = wind_size

        # Create bots
        if type(n_agents) is int:
            self.team_a = [self.create_bot('a', i, **kwargs) for i in range(n_agents)]
            self.team_b = [self.create_bot('b', i, **kwargs) for i in range(n_agents)]

        elif type(n_agents) is list:
            self.team_a = [self.create_bot('a', i, **kwargs) for i in range(n_agents[0])]
            self.team_b = [self.create_bot('b', i, **kwargs) for i in range(n_agents[1])]
        else:
            assert False, 'Bad number of bot given!'

        height = wind_size[0]
        width = wind_size[1]

        # Distribute the bots based on the number and teams
        self.base_a_pos = np.array([50, height/2])
        self.base_b_pos = np.array([width-50, height/2])
        dist = self.team_a[0].RADIUS * 2 + 50

        # Team a
        length = len(self.team_a)
        for i in range(length):
            shift = np.array([[0, dist * (i - length / 2 + 0.5)]])
            self.team_a[i].set_position(self.base_a_pos + shift)
            self.team_a[i].set_rotation(np.pi / 2)

        # Team b
        length = len(self.team_b)
        for i in range(length):
            shift = np.array([[0, dist * (i - length / 2 + 0.5)]])
            self.team_b[i].set_position(self.base_b_pos + shift)
            self.team_b[i].set_rotation(-np.pi / 2)

        # Create walls
        wall_thickness = 10

        # Bottom
        self.create_obstacle([int(width/2),wall_thickness/2], wall_thickness, width, 0, is_wall=True)
        # Left
        self.create_obstacle([wall_thickness/2,int(height/2)], height, wall_thickness, 0, is_wall=True)
        # Top
        self.create_obstacle([int(width/2),height - wall_thickness/2], wall_thickness, width, 0, is_wall=True)
        # Right
        self.create_obstacle([width - wall_thickness/2,int(height/2)], height, wall_thickness, 0, is_wall=True)

        # Other obstacles
        size = 150

        # Center
        self.create_obstacle([int(width/2), int(height/2)], size, size, np.pi/4)
        # Bot-left, bot-right, top-left, top-right,
        self.create_obstacle([int(width/4 + 50), int(height/4)], size, size, np.pi/4)
        self.create_obstacle([int(width*3/4 - 50), int(height/4)], size, size, np.pi/4)
        self.create_obstacle([int(width/4 + 50), int(height*3/4)], size, size, np.pi/4)
        self.create_obstacle([int(width*3/4 - 50), int(height*3/4)], size, size, np.pi/4)


    def create_bot(self, team, index, **kwargs):
        # If settings for the bots are defined
        if 'bot_settings' in kwargs.keys():
            settings = kwargs['bot_settings']
            controllers = kwargs['controllers']

            index = index if index < len(settings[team]) else len(settings[team])-1

            new_bot = controllers[settings[team][index]](team, self)
        else:
            new_bot = Bot(team, self)

        self.game_objects.append(new_bot)
        return new_bot

    def add_projectile(self, projectile):
        self.game_objects.append(projectile)

    def create_obstacle(self, position, height, width, rotation=0, is_wall=False):
        obs = Obstacle(position, height, width, rotation, is_wall)
        self.game_objects.append(obs)
        return obs

    def time_step(self, delta_t):
        for obj in self.game_objects:
            if isinstance(obj, Dynamic):
                # Update position based on speed
                obj.update(delta_t)
            if isinstance(obj, Bot):
                # Take action for every bot
                obj.take_action()

    # Check is everything is good
    # NOTE: if a projectile hits 2 or more bots at the exact same game iter, they both lose life
    def resolve_collisions(self, delta_t):
        to_remove = []
        for i in range(len(self.game_objects)):
            obj_1 = self.game_objects[i]
            if isinstance(obj_1, Dynamic) and isinstance(obj_1, Collidable):
                # Check if it is colliding with any collidables
                for j in range(len(self.game_objects)):
                    obj_2 = self.game_objects[j]
                    if i != j and isinstance(obj_2, Collidable) and colliding(obj_1, obj_2):
                        res_1 = obj_1.handle_collision(obj_2)
                        # Remove
                        if res_1 == -1:
                            to_remove.append(i)
                        # Push back
                        elif res_1 == 1:
                            obj_1.update(-delta_t)

                        res_2 = obj_2.handle_collision(obj_1)
                        # Remove
                        if res_2 == -1:
                            to_remove.append(j)
                        elif res_2 == 1:
                            obj_2.update(-delta_t)


        # Order by decreasing index in game objects
        to_remove = sorted(list(set(to_remove)), reverse=True)

        # Remove
        for index in to_remove:
            self.game_objects.pop(index)

        # TODO add code for bot elimination

