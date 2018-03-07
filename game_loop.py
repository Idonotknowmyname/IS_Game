import pygame as pg
import numpy as np
from project.sprites.bot import Bot
from project.sprites.projectile import Projectile
from project.sprites.obstacle import Obstacle
from project.game_engine.game import Game
from time import time

def draw_sprite(display, sprite):
    if type(sprite) == Bot:

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

pg.init()
pg.font.init()

# load image:
# pygame.image.load('path')

display_height = 800
display_width = 800

black = (0,0,0)
background_col = (200, 200, 200)
obstacle_col = (150, 0, 150)
projectile_col = (122,122,0)

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

fps = 60

crashed = False

# Init game
game = Game(n_agents=1, wind_size=[display_height, display_width])
controlled_agent = [1,0] #Team 0 (A), bot 0

last = time()

while not crashed:

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
                    agent.set_ang_speed(1)
                elif event.key == 113:
                    agent.set_ang_speed(-1)

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
                    agent.set_ang_speed(0)
                elif event.key == 113:
                    agent.set_ang_speed(0)

    # Update game
    game.time_step(1/fps)
    game.resolve_collisions(1/fps)

    # Draw objects
    game_display.fill(background_col)

    for sprite in game.game_objects:
        draw_sprite(game_display, sprite)

    pg.display.update()
    clock.tick(fps)

pg.quit()
quit()
