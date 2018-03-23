from ..sprites.bot import Bot
from ..sprites.obstacle import Obstacle
from ..utils.utils import colliding
from ..utils.utils import get_rot_mat
from ..sprites.projectile import Projectile
from ..sprites.point import Point

import numpy as np
from time import time

class TestController(Bot):

    def __init__(self, team, game, position=None, rotation=None):
        super(TestController, self).__init__(team,game,position,rotation)

    def take_action(self):

        # Put point in front and check for collisions with obstacles
        rel_pos_front = np.array([0, self.RADIUS * 4])
        rel_pos_right = np.array([self.RADIUS * 4, 0])
        rel_pos_left = np.array([-self.RADIUS * 4, 0])

        all_pos = np.vstack([rel_pos_front, rel_pos_right, rel_pos_left])

        rel_rot_pos = np.asarray(all_pos * get_rot_mat(self.get_rotation()))

        point_front = Point(self.get_position() + rel_rot_pos[0,:])
        point_right = Point(self.get_position() + rel_rot_pos[1,:])
        point_left = Point(self.get_position() + rel_rot_pos[2,:])

        if self.game.collides_with(point_front, 'obstacle'):
            print('I am colliding in front!')

        if self.game.collides_with(point_right, 'obstacle'):
            print('I am colliding on the right!')

        if self.game.collides_with(point_left, 'obstacle'):
            print('I am colliding on the left!')


    def obstacles_on_path(self, target):
        # Create a very thin rectangular obstacle (line between bots) and check its collisions
        # Calculate distance and direction of target
        distance_vec = target.position - self.position
        distance = np.linalg.norm(distance_vec)
        direction = np.arctan2(distance_vec[1], distance_vec[0])
        direction = (-direction + np.pi / 2) % (np.pi * 2)

        # Create the obstacle
        thickness = 2
        length = abs(distance - (self.RADIUS + target.RADIUS) - 5)
        obs = Obstacle((target.position + self.position) / 2, length, thickness, direction)

        # List of obstacles
        obstacles = []

        # If the target is visible
        visible = True
        # Loop through game objects and check if it collides with other obstacles
        for obj in self.game.get_game_objects('obstacle'):

            collision = colliding(obs, obj)
            if collision:
                obstacles.append(obj)

        return obstacles

    def is_target_visible(self, target):
        # Create a very thin rectangular obstacle (line between bots) and check its collisions
        # Calculate distance and direction of target
        distance_vec = target.position - self.position
        distance = np.linalg.norm(distance_vec)
        direction = np.arctan2(distance_vec[1], distance_vec[0])
        direction = (-direction + np.pi / 2) % (np.pi * 2)

        # Create the obstacle
        thickness = 2
        length = abs(distance - (self.RADIUS + target.RADIUS) - 5)
        obs = Obstacle((target.position + self.position) / 2, length, thickness, direction)

        # Loop through game objects and check if it collides with other obstacles
        for obj in self.game.get_game_objects('obstacle'):
            if colliding(obs, obj):
                return False

        return True

    def avoid_bullets(self):
        # Get only the bullets
        bullet_list = self.game.get_game_objects('projectile')

        # Get only bullets that will collide
        bullet_positions = list(filter(lambda x: self.bullet_collides(x), bullet_list))

        if len(bullet_positions) > 0:
            return sum(list(map(lambda x: self.dodge_direction(x),bullet_positions)))

        return 0

    bullet_pointer = None

    def bullet_collides(self, bullet):
        bullet_dir_mat = get_rot_mat(bullet.rotation)
        bullet_norm_vec = np.asarray(bullet.get_speed()/np.linalg.norm(bullet.get_speed()) * bullet_dir_mat).flatten()
        bullet_loc_vec = (bullet.position - self.position)/np.linalg.norm(bullet.position - self.position)

        # # Tracking
        # obs_direction = np.arctan2(bullet_norm_vec[1],bullet_norm_vec[0])
        # obs_direction = (-obs_direction + np.pi / 2) % (np.pi * 2)
        # if self.bullet_pointer is None:
        #     self.bullet_pointer = self.game.create_obstacle(position=self.position, height=50, width=1, rotation=obs_direction)
        # else:
        #     self.bullet_pointer.set_rotation(obs_direction)

        #print(np.dot(bullet_norm_vec, bullet_loc_vec))
        return np.dot(bullet_norm_vec, bullet_loc_vec) <  -0.93

    def dodge_direction(self, bullet):
        bullet_dir_mat = get_rot_mat(bullet.rotation)
        bullet_norm_vec = np.asarray(bullet.get_speed() / np.linalg.norm(bullet.get_speed()) * bullet_dir_mat).flatten()
        bullet_loc_vec = (bullet.position - self.position) / np.linalg.norm(bullet.position - self.position)

        rot_mat_90 = get_rot_mat(90)
        bullet_loc_vec = np.asarray(bullet_loc_vec * rot_mat_90).flatten()

        # Tracking
        obs_direction = np.arctan2(bullet_loc_vec[1],bullet_loc_vec[0])
        obs_direction = (-obs_direction + np.pi / 2) % (np.pi * 2)
        if self.bullet_pointer is None:
            self.bullet_pointer = self.game.create_obstacle(position=self.position, height=50, width=1, rotation=obs_direction)
        else:
            self.bullet_pointer.set_rotation(obs_direction)

        print(np.dot(bullet_norm_vec, bullet_loc_vec))
        return np.sign(np.dot(bullet_norm_vec, bullet_loc_vec))

    def get_bot_type(self):
        return 'Test Controller'