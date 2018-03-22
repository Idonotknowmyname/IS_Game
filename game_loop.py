import pygame as pg
import numpy as np
from project.sprites.bot import Bot
from project.sprites.projectile import Projectile
from project.sprites.obstacle import Obstacle
from project.game_engine.game import Game

from project.ai.test_controller import TestController
from project.ai.base_controller import BaseController
from project.ai.pathfind_controller import PathfindController
from project.ai.state_controller import StateController
from project.ai.deep_ql_controller import DeepQLController
from project.ai.mcts_controller import MCTSController

from time import time
import os

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # see issue #152
os.environ["CUDA_VISIBLE_DEVICES"] = ""

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

def draw_grid_path(game, size):
    graph = game.grid

    for i in range(graph.shape[0]):
        for j in range(graph.shape[1]):
            if not graph[i, j]:
                col = (255, 153, 153)
                pg.draw.rect(game_display, col, (j*size, i*size, size, size))

pg.init()
pg.font.init()

# Define display size (approx. same as arena size) and frames per second of game
display_height = 800
display_width = 1600
fps = 50
physics_refresh_rate = 1.8/fps

# Already precomputed values = (5, 10, 15)
grid_path = 15

# Number of agents per team
n_agents = 3

# Identify what agent in what team is controlled by keyboard
controlled_agent = [1,0] #Team 1 (B), bot 0

# Define bot controllers
controllers = {
    0 : Bot,
    1 : TestController,
    2 : BaseController,
    3 : PathfindController,
    4 : StateController,
    5 : DeepQLController,
    6 : MCTSController
}
# Define what controllers should be used for each bot
# key is team name ('a', 'b'), value is array of controller id for each bot
bot_settings = {
    'a': [0, 6, 0],
    'b': [0, 0, 0]
}

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

crashed = False

# Init game
game = Game(n_agents=n_agents, wind_size=[display_height, display_width], bot_settings=bot_settings,
            controllers=controllers, grid_path=grid_path)

last_iter_time = time()

print_time = False

while not crashed and not game.is_game_over():

    start_iteration = time()

    # Get inputs
    for event in pg.event.get():
        if event.type == pg.QUIT:
            crashed = True
        elif event.type == pg.KEYDOWN:
            if controlled_agent is not None:
                agent = game.team_a[controlled_agent[1]] if controlled_agent[0] == 0 else game.team_b[controlled_agent[1]]
                speed = agent.get_speed()
                rot_speed = agent.get_ang_speed()
                # Move up
                if event.key == 119:
                    agent.add_speed_y(1)
                # Move left
                elif event.key == 97:
                    agent.add_speed_x(-1)
                # Move down
                elif event.key == 115:
                    agent.add_speed_y(-1)
                # Move right
                elif event.key == 100:
                    agent.add_speed_x(1)
                # Shoot
                elif event.key == 32:
                    agent.shoot()
                # Rotation
                elif event.key == 101:
                    agent.ang_speed += 1
                elif event.key == 113:
                    agent.ang_speed -= 1
                # Sprint
                elif event.key == 304:
                    agent.MAX_SPEED *= 3
                    agent.MAX_ANG_SPEED *= 3

        elif event.type == pg.KEYUP:
            if controlled_agent is not None:
                agent = game.team_a[controlled_agent[1]] if controlled_agent[0] == 0 else game.team_b[controlled_agent[1]]
                speed = agent.get_speed()
                rot_speed = agent.get_ang_speed()
                # Move up
                if event.key == 119:
                    agent.add_speed_y(-1)
                # Move left
                elif event.key == 97:
                    agent.add_speed_x(1)
                # Move down
                elif event.key == 115:
                    agent.add_speed_y(1)
                # Move right
                elif event.key == 100:
                    agent.add_speed_x(-1)

                # Rotation
                elif event.key == 101:
                    agent.ang_speed -= 1
                elif event.key == 113:
                    agent.ang_speed += 1
                    # Sprint
                elif event.key == 304:
                    agent.MAX_SPEED /= 3
                    agent.MAX_ANG_SPEED /= 3

    # Update game
    start_physics = time()
    delta_t = time() - last_iter_time
    last_iter_time = time()
    game.time_step(delta_t)
    time_step_taken = time() - start_physics
    game.resolve_collisions()
    game.update_q_learners()
    resolve_time = time() - start_physics - time_step_taken

    if print_time:
            print('Time taken for game.time_step() = {}\nTime taken for game.resolve_collisions = {}'
                  .format(time_step_taken, resolve_time, physics_refresh_rate))

    start_draw = time()
    # Draw objects
    game_display.fill(background_col)

    # draw_grid_path(game, grid_path)

    for sprite in game.get_game_objects('sprite'):
        draw_sprite(game_display, sprite)

    draw_time = time() - start_draw

    start_update = time()
    pg.display.update()
    clock.tick(fps)

    update_time = time() - start_update

    tot_sum = time_step_taken + resolve_time + draw_time + update_time

    if print_time:
        print('Time taken for drawing = {}\nTime taken for updating = {}\nSum of individual times = {}\n1/fps = {}\n'
              ''.format(draw_time, update_time, tot_sum, 1/fps))

pg.quit()
quit()
