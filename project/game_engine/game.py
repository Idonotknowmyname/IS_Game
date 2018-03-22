import numpy as np
from time import time
import os
from copy import copy

from ..utils.utils import colliding, get_normal_to_surface
from ..utils.rect_grid import RectGrid

from ..sprites.bot import Bot
from ..sprites.dynamic import Dynamic
from ..sprites.obstacle import Obstacle
from ..sprites.collidable import Collidable

from ..ai.ql_controller import QLController

class Game:

    # # Dictionary of the game objects for simplifying retrieval
    # game_objects_dict = {}
    #
    # # Teams of bots
    # team_a = []
    # team_b = []

    def __init__(self, n_agents, wind_size, **kwargs):
        self.team_a = []
        self.team_b = []
        self.game_objects_dict = {}

        self.window_size = wind_size

        # Create bots
        if type(n_agents) is int:
            self.team_a = [self.create_bot('a', i, **kwargs) for i in range(n_agents)]
            self.team_b = [self.create_bot('b', i, **kwargs) for i in range(n_agents)]

        elif type(n_agents) is list:
            self.team_a = [self.create_bot('a', i, **kwargs) for i in range(n_agents[0])]
            self.team_b = [self.create_bot('b', i, **kwargs) for i in range(n_agents[1])]
        else:
            assert False, 'Bad number of bot given! It has to be of types list or int'

        height = wind_size[0]
        width = wind_size[1]

        # Distribute the bots based on the number and teams
        self.base_a_pos = np.array([50, height/2])
        self.base_b_pos = np.array([width-50, height/2])
        dist = self.team_a[0].RADIUS * 2 + 150

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

        # Initialize hit count for the bots
        self.step_hits = {x: 0 for x in self.get_game_objects('bot')}

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

        # If specified, create grid of map with spaces where bot can go
        if 'grid_path' in kwargs.keys():
                size = kwargs['grid_path']
                assert type(size) == int

                path = 'map_grid/{}.npy'.format(size)

                if os.path.isfile(path):
                    self.grid = np.load(path)
                else:
                    self.grid = self.create_grid(kwargs['grid_path'])
                    np.save(path, self.grid)

                self.cell_size = size

    # Deepclone for MCTS's
    def __deepcopy__(self, memodict={}):

        copy_game = Game(n_agents=1, wind_size=self.window_size)
        copy_game.team_a = []
        copy_game.team_b = []
        for bot in copy_game.get_game_objects('bot'): copy_game.remove_game_object(bot, 'bot')

        for projectile in self.get_game_objects("projectile"):
            copy_game.add_projectile(copy(projectile))

        for bot in self.get_game_objects("bot"):
            copy_bot = copy(bot)
            copy_bot.game = copy_game
            copy_game.add_game_object(copy_bot, "bot")
            if copy_bot.team == "a":
                copy_game.team_a.append(copy_bot)
            else:
                copy_game.team_b.append(copy_bot)

        return copy_game


    # Create a graph of the map with the specified coverage of one cell, for pathfinding and such
    def create_grid(self, cell_size):
        graph_height = int(self.window_size[0] / cell_size) + 1
        graph_width = int(self.window_size[1] / cell_size) + 1

        grid = np.empty((graph_height, graph_width), dtype=bool)
        grid[:] = True

        # Check if bot can be in specific cells
        test_bot = Bot('test', self)

        for i in range(graph_height):
            for j in range(graph_width):
                pos = [(j+0.5) * cell_size, (i+0.5) * cell_size]
                test_bot.set_position(np.array(pos))

                for obs in self.get_game_objects('obstacle'):
                    if colliding(test_bot, obs):
                        grid[i, j] = False
                        break

        return grid

    # Add an object obj of specified type (as string)
    def add_game_object(self, obj, type):
        if type not in self.game_objects_dict.keys():
            self.game_objects_dict[type] = [obj]
        else:
            self.game_objects_dict[type].append(obj)

    def remove_game_object(self, obj, type):
        if type in self.game_objects_dict.keys():
            count = 0

            for elem in self.game_objects_dict[type]:
                if obj is elem:
                    self.game_objects_dict[type].pop(count)
                    break
                count += 1

        if type == 'bot':
            count = 0
            team = self.team_a if obj.team == 'a' else self.team_b
            for elem in team:
                if obj is elem:
                    if obj.team == 'a':
                        self.team_a.pop(count)
                    else:
                        self.team_b.pop(count)
                    break
                count += 1

    def create_bot(self, team, index, **kwargs):
        # If some bots are passed from outside
        if 'insert_bots' in kwargs.keys() and kwargs:
            for new_bot, bot_team, bot_index in kwargs['insert_bots']:
                if index == bot_index and team == bot_team:
                    new_bot.game = self
                    new_bot.team = bot_team
                    new_bot.health = new_bot.MAX_HEALTH
                    self.add_game_object(new_bot, 'bot')
                    return new_bot

        # If settings for the bots are defined
        if 'bot_settings' in kwargs.keys():
            settings = kwargs['bot_settings']
            controllers = kwargs['controllers']

            index = index if index < len(settings[team]) else len(settings[team])-1

            new_bot = controllers[settings[team][index]](team, self)
        else:
            new_bot = Bot(team, self)

        self.add_game_object(new_bot, 'bot')
        return new_bot

    def add_projectile(self, projectile):
        self.add_game_object(projectile, 'projectile')

    def create_obstacle(self, position, height, width, rotation=0, is_wall=False):
        obs = Obstacle(position, height, width, rotation, is_wall)
        self.add_game_object(obs, 'obstacle')
        return obs

    # If indexed is true, the returned list consists of
    def get_game_objects(self, *args):
        objects = []

        # If no argument given, return all objects
        if len(args) == 0:
            for obj_type, obj_list in self.game_objects_dict.items():
                objects.extend(obj_list)

        else:
            for obj_type in args:
                assert type(obj_type) == str, 'All inputs have to be strings'

                if obj_type in self.game_objects_dict.keys():
                    objects.extend(self.game_objects_dict[obj_type])
                else:
                    if obj_type == 'collidable':
                        if 'obstacle' in self.game_objects_dict.keys():
                            objects.extend(self.game_objects_dict['obstacle'])

                        if 'bot' in self.game_objects_dict.keys():
                            objects.extend(self.game_objects_dict['bot'])

                        if 'projectile' in self.game_objects_dict.keys():
                            objects.extend(self.game_objects_dict['projectile'])
                    elif obj_type == 'sprite':
                        if 'obstacle' in self.game_objects_dict.keys():
                            objects.extend(self.game_objects_dict['obstacle'])

                        if 'bot' in self.game_objects_dict.keys():
                            objects.extend(self.game_objects_dict['bot'])

                        if 'projectile' in self.game_objects_dict.keys():
                            objects.extend(self.game_objects_dict['projectile'])

                    elif obj_type == 'dynamic':
                        if 'bot' in self.game_objects_dict.keys():
                            objects.extend(self.game_objects_dict['bot'])

                        if 'projectile' in self.game_objects_dict.keys():
                            objects.extend(self.game_objects_dict['projectile'])

        return objects

    def time_step(self, delta_t):
        for obj in self.get_game_objects('dynamic'):
            # Update position based on speed
            obj.update(delta_t)

            if isinstance(obj, Bot):
                if obj.health > 0:
                    # Take action for every bot
                    obj.take_action()

    def update_q_learners(self):
        for bot in self.get_game_objects('bot'):
            if isinstance(bot, QLController):
                bot.learn()

    # Check is everything is good
    # NOTE: if a projectile hits 2 or more bots at the exact same game iter, they both lose life
    def resolve_collisions_old(self, delta_t):
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

    def resolve_collisions(self):

        # Initialize the round hit count
        self.step_hits = {x: 0 for x in self.step_hits.keys()}
        for obj_1 in self.get_game_objects('dynamic'):
                # Check if it is colliding with any collidables
                for obj_2 in self.get_game_objects('collidable'):
                    if obj_1 is not obj_2 and colliding(obj_1, obj_2):
                        res_1 = obj_1.handle_collision(obj_2)
                        # Remove projectile and store the hit if a bot was hit
                        if res_1 == -1:
                            self.remove_game_object(obj_1, 'projectile')
                            if isinstance(obj_2, Bot):
                                self.step_hits[obj_1.shooter] += 1
                        # Push back
                        elif res_1 == 1:
                            normal = get_normal_to_surface(obj_1, obj_2)
                            obj_1.position = obj_1.position + normal

                        res_2 = obj_2.handle_collision(obj_1)
                        # Remove projectile and store the hit if a bot was hit
                        if res_2 == -1:
                            self.remove_game_object(obj_2, 'projectile')
                            if isinstance(obj_1, Bot):
                                self.step_hits[obj_2.shooter] += 1
                        elif res_2 == 1:
                            pass

        # Remove dead bots
        for bot in self.get_game_objects('bot'):
            if bot.health <= 0:
                self.remove_game_object(bot, 'bot')

    def is_game_over(self):
        return len(self.team_a) == 0 or len(self.team_b) == 0
