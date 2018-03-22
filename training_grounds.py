from time import time
import numpy as np
import os
from keras.models import load_model

from project.game_engine.game import Game

from project.sprites.bot import Bot
from project.ai.deep_ql_controller import DeepQLController
from project.ai.base_controller import BaseController
from project.ai.pathfind_controller import PathfindController
from project.ai.state_controller import StateController
from project.ai.test_controller import TestController

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

# Update timestep
delta_t = 1/30

episodes = 30

# Max number of seconds an episode can last
max_episode_length = 100

model_1 = load_model('deep_q_models/test_1_FFNN (30 episodes).h5')
bot_1 = DeepQLController(None, None, model=model_1)

model_2 = load_model('deep_q_models/test_2_FFNN (30 episodes).h5')
bot_2 = DeepQLController(None, None, model=model_2)

insert_bots = [(bot_1, 'a', 1), (bot_2, 'b', 1)]

display_height = 800
display_width = 1600

# Already precomputed values = (5, 10, 15)
grid_path = 15

# Number of agents per team
n_agents = 3

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

for i in range(episodes):

    bot_1.init_memory()
    bot_2.init_memory()

    bot_settings = get_rand_bot_settings(probs=[0, 0.6, 0.4])

    # Init game
    game = Game(n_agents=n_agents, wind_size=[display_height, display_width], bot_settings=bot_settings,
                controllers=controllers, grid_path=grid_path, insert_bots=insert_bots)

    print_with_time('Starting episode {}, team a = {}, team b = {}'.format(i, bot_settings['a'], bot_settings['b']))

    last_iter_time = time()
    tot_shots_hit = {bot_1: 0, bot_2: 0}
    episode_start = time()
    iter_count = 0

    while not game.is_game_over() and iter_count*delta_t < max_episode_length and continue_simulation(game):

        start_iteration = time()

        # Update game
        start_physics = time()
        if not game.is_game_over():
            game.time_step(delta_t)
        time_step_taken = time() - start_physics
        game.resolve_collisions()
        resolve_time = time() - start_physics - time_step_taken
        if not game.is_game_over():
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

        # Update the shots hit
        tot_shots_hit[bot_1] += game.step_hits[bot_1]
        tot_shots_hit[bot_2] += game.step_hits[bot_2]

        iter_count += 1


    print_with_time('Episode {} has ended! The first bot hit {} shots, the second bot hit {} shots'
                    .format(i, tot_shots_hit[bot_1], tot_shots_hit[bot_2]))


bot_1.save_model('test_1_FFNN (60 episodes)')
bot_2.save_model('test_2_FFNN (60 episodes)')