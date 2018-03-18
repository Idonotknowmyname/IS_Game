from ..sprites.bot import Bot
from ..sprites.obstacle import Obstacle
from ..utils.utils import colliding
from ..utils.utils import get_rot_mat
from ..sprites.projectile import Projectile

import numpy as np

class TestController(Bot):

    def __init__(self, team, game, type=0, position=None, rotation=None):
        super(TestController, self).__init__(team,game,type,position,rotation)

    def take_action(self):

        #Get the first bot from enemy team
        opponents = self.game.team_b if self.team == 'a' else self.game.team_a

        #Choose first opponen as target
        target = opponents[0]

        #parameters for the target location
        distance_vec = target.position - self.position
        direction = np.arctan2(distance_vec[1],distance_vec[0])
        direction = (-direction + np.pi / 2) % (np.pi * 2)
        distance = np.linalg.norm(distance_vec)

        # Match rotation
        diff_rotation = (direction-self.rotation) % (np.pi*2)

        if abs(diff_rotation) < abs((np.pi*2 - diff_rotation) % (np.pi*2)):
            self.ang_speed = np.sign(diff_rotation)
        else:
            self.ang_speed = -np.sign(diff_rotation)

        # Shoot only if sight is clear

        if self.is_target_visible(target):
            self.set_speed([0,0])
            # self.shoot()
        else:
            # Find the closest obstacle to avoid
            obstacle_list = self.obstacles_on_path(target)
            obstacle_list = sorted(obstacle_list, key = lambda x:
            np.linalg.norm(x.position - self.position))
            first_obstacle = obstacle_list[0]

            # Normalize vectors
            norm_distance_vec = distance_vec/distance
            rot_matrix_90 = get_rot_mat(np.pi/2)
            norm_obstacle_vec = (first_obstacle.position-self.position)/np.linalg.norm(first_obstacle.position-self.position)
            norm_obstacle_vec = np.asarray(norm_obstacle_vec * rot_matrix_90).flatten()

            # Decide avoidance direction
            if np.dot(norm_distance_vec,norm_obstacle_vec) > 0:
                self.set_speed([1, 0])
            else:
                self.set_speed([-1,0])

        # Avoid incoming bullets
        dodge_direction = self.avoid_bullets()

        if dodge_direction != 0:
            self.set_speed([dodge_direction, 0])


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
        for obj in self.game.game_objects:
            if isinstance(obj, Obstacle):
                if colliding(obs, obj):
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
        for obj in self.game.game_objects:
            if isinstance(obj, Obstacle):
                if colliding(obs, obj):
                    return False

        return True

    def avoid_bullets(self):
        # Get only the bullets
        bullet_list = list(filter(lambda x: isinstance(x,Projectile),self.game.game_objects))

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

