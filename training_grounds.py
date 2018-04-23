from time import time
import pygame as pg
import numpy as np
import os
from keras.models import load_model
import matplotlib.pyplot as plt
from scipy.signal import gaussian

from project.game_engine.game import Game

from project.sprites.bot import Bot
from project.sprites.projectile import Projectile
from project.sprites.obstacle import Obstacle

from project.ai.deep_ql_controller import DeepQLController
from project.ai.base_controller import BaseController
from project.ai.pathfind_controller import PathfindController
from project.ai.state_controller import StateController
from project.ai.test_controller import TestController
from project.ai.trained_dql_controller import TrainedDQLController

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # see issue #152
os.environ["CUDA_VISIBLE_DEVICES"] = ""

start_time = 0
last_time = 0

def print_with_time(data, **kwargs):
    global start_time, last_time

    if start_time == 0:
        start_time = time()

    if last_time == 0:
        last_time = start_time

    now = time()

    time_info = '[{:04.2f}s total | {:03.5f}s from last]'.format(now - start_time, now - last_time)
    print(time_info, ' -> ', data)

    last_time = time()

team_a_sizes = []
team_b_sizes = []

def continue_simulation(game):
    global team_a_sizes, team_b_sizes

    still_QL_in_a = 'Deep QL Controller' in [x.get_bot_type() for x in game.team_a]
    still_QL_in_b = 'Deep QL Controller' in [x.get_bot_type() for x in game.team_b]

    return still_QL_in_a or still_QL_in_b

def get_rand_bot_settings(probs=None, avail_opts=None):

    # Put some random bots in the game
    if probs is None:
        probs = [0.2, 0.3, 0.5]

    # Either TestController, BaseController, PathfindController, StateController
    if avail_opts is None:
        avail_opts = [2, 3, 4]

    team_a_sett = np.random.choice(avail_opts, n_agents, replace=True, p=probs)
    team_b_sett = np.random.choice(avail_opts, n_agents, replace=True, p=probs)

    return {'a': team_a_sett, 'b': team_b_sett}

def draw_sprite(display, sprite):
    if isinstance(sprite, Bot):

        position = sprite.get_position().copy()
        position[1] = display_height - position[1]

        # Draw the shape
        pg.draw.circle(game_display, team_colors[sprite.team], position.astype(int), sprite.RADIUS)

        # Draw inner shape (based on health)
        color = (sprite.health / sprite.MAX_HEALTH) * 255
        pg.draw.circle(game_display, (0,color,0), position.astype(int), sprite.RADIUS - 5)

        # Write health
        health_label = health_font.render("{}".format(sprite.health),
                                            0,
                                           black)
        game_display.blit(health_label,position - np.array([17,10]))

        # Draw the cannon
        sprite_bbox = sprite.get_bbox()
        cannon_center = (sprite_bbox[0] + sprite_bbox[-1])/2
        cannon_center[1] = display_height - cannon_center[1]
        pg.draw.circle(game_display, black, cannon_center.astype(int), 5)
    elif type(sprite) == Projectile:
        position = sprite.get_position().copy()
        position[1] = display_height - position[1]

        pg.draw.circle(game_display, projectile_col, position.astype(int), sprite.RADIUS)
    elif type(sprite) == Obstacle:
        vertices = sprite.get_bbox()
        vertices[:, 1] = display_height - vertices[:, 1]
        pg.draw.polygon(game_display, obstacle_col, vertices, 0)


display_height = 800
display_width = 1600

spectate = False

if spectate:
    pg.init()
    pg.font.init()

    # Define colors
    black = (0,0,0)
    background_col = (255, 255, 255)
    obstacle_col = (0, 204, 0)
    projectile_col = (0,0,0)

    team_colors = {
        'a': (255,0,0), # Red
        'b': (0,0,255) # Blue
    }

    white = (255,255,255)
    red = (255,0,0)
    green = (0,255,0)
    blue = (0,0,255)

    default_font = pg.font.get_default_font()
    health_font = pg.font.Font(default_font, 20)

    # Init window and window params
    game_display = pg.display.set_mode((display_width,display_height))
    pg.display.set_caption('A test game')
    clock = pg.time.Clock()


# Update timestep
delta_t = 1/30

episodes = 20

# Max number of seconds an episode can last
max_episode_length = 60

bot_1 = TrainedDQLController(None, None)
model_name_1 = 'for presentation_1'

bot_2 = TrainedDQLController(None, None)
model_name_2 = 'for presentation_2'

insert_bots = [(bot_1, 'a', 0), (bot_2, 'b', 0)]

# Already precomputed values = (5, 10, 15)
grid_path = 15

# Number of agents per team
n_agents = 2

# Define bot controllers
controllers = {
    0 : Bot,
    1 : TestController,
    2 : BaseController,
    3 : PathfindController,
    4 : StateController,
    5 : DeepQLController
}

print_time = False
log_every_n_seconds = 10

losses_bot_1 = []
losses_bot_2 = []

last_health_a = None
last_health_b = None

for i in range(episodes):

    bot_settings = get_rand_bot_settings(probs=[0.3, 0.7], avail_opts=[3, 4])

    # Init game
    game = Game(n_agents=n_agents, wind_size=[display_height, display_width], bot_settings=bot_settings,
                controllers=controllers, grid_path=grid_path, insert_bots=insert_bots)

    print_with_time('Starting episode {}, team a = {}, team b = {}'.format(i, bot_settings['a'], bot_settings['b']))

    last_iter_time = time()
    tot_shots_hit = {bot_1.id: 0, bot_2.id: 0}
    bot_1.train_err = []
    bot_2.train_err = []

    episode_start = time()
    iter_count = 0

    while not game.is_game_over() and iter_count*delta_t < max_episode_length and continue_simulation(game):

        start_iteration = time()

        # Update game
        start_physics = time()
        game.time_step(delta_t)
        time_step_taken = time() - start_physics
        game.resolve_collisions()
        resolve_time = time() - start_physics - time_step_taken
        game.update_q_learners()
        q_learner_time = time() - start_physics - time_step_taken - resolve_time

        if print_time:
                print('Time taken for game.time_step() = {}\nTime taken for game.resolve_collisions = {}\nTime taken to update q learners = {}'
                      .format(time_step_taken, resolve_time, q_learner_time))

        if time() - last_iter_time > log_every_n_seconds:

            team_a_health = [x.health for x in game.team_a]
            team_a_types = [x.get_bot_type() for x in game.team_a]

            team_b_health = [x.health for x in game.team_b]
            team_b_types = [x.get_bot_type() for x in game.team_b]

            print('\t\tElapsed game time {}\n\t\tHealth for team a = {} - types = {}\n\t\tHealth for team b = {} - types = {}'
                  .format(iter_count*delta_t, team_a_health, team_a_types, team_b_health, team_b_types))

            print()

            last_iter_time = time()

            if (last_health_a is not None and last_health_a == team_a_health) \
                    and (last_health_b is not None and last_health_b == team_b_health):
                # If the game got stuck
                break

            last_health_a = team_a_health
            last_health_b = team_b_health

        if spectate:
            # Draw objects
            game_display.fill(background_col)

            # draw_grid_path(game, grid_path)

            for sprite in game.get_game_objects('sprite'):
                draw_sprite(game_display, sprite)

            start_update = time()
            pg.display.update()
            clock.tick(1/delta_t)


        # Update the shots hit
        tot_shots_hit[bot_1.id] += game.step_hits[bot_1]
        tot_shots_hit[bot_2.id] += game.step_hits[bot_2]

        iter_count += 1

    losses_bot_1.append(np.mean(bot_1.train_err))
    losses_bot_2.append(np.mean(bot_1.train_err))

    print_with_time('Episode {} has ended! The first bot hit {} shots, the second bot hit {} shots'
                    .format(i, tot_shots_hit[bot_1.id], tot_shots_hit[bot_2.id]))

bot_1.save_model(model_name_1)
bot_2.save_model(model_name_2)


plt.plot(losses_bot_1, label='Bot 1 training error')
plt.figure()
plt.plot(losses_bot_1, label='Bot 2 training error')

np.save('deep_q_models/train_loss_bot_1_20', losses_bot_1)
np.save('deep_q_models/train_loss_bot_2_20', losses_bot_2)

plt.legend()
plt.show()