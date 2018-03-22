import numpy as np
from .pathfind_controller import PathfindController
from ..sprites.bot import Bot
from ..sprites.point import Point
from ..utils.utils import get_rot_mat

class StateController(PathfindController):

    states = None
    current_state = None

    def __init__(self, team, game, position=None, rotation=None):
        super(StateController,self).__init__(team,game,position,rotation)
        self.states = {}
        self.initialize_states()

    def initialize_states(self):

        # Roaming
        self.states["Roam"] = self.roam

        # Choose target (not used for now)
        # self.states["Select"] = self.select

        # Search
        self.states["Search"] = self.search

        # Fire at target
        self.states["Shoot"] = self.shoot_action

        # Dodge bullets
        self.states["Dodge"] = self.dodge

        self.current_state = "Roam"

    def take_action(self):

        self.states[self.current_state]()

    def check_for_dodge(self):

        closest_bullet = self.get_closest_enemy_projectile()

        if closest_bullet is not None:
            # Get bullet properties
            rot_mat = get_rot_mat(closest_bullet.get_rotation() + np.pi/2) # +pi/2 to make it normal to the direction
            bullet_direction = np.asarray(closest_bullet.get_speed() * rot_mat).flatten()
            bullet_location = closest_bullet.get_position()

            bot_to_bullet = bullet_location - self.get_position()

            # Get the hit vectors
            h1 = np.array([bot_to_bullet[1],-bot_to_bullet[0]]) / np.linalg.norm(bot_to_bullet)
            h1 *= self.RADIUS + closest_bullet.RADIUS
            h2 = -h1

            bullet_to_h1 = (-bot_to_bullet + h1)
            bullet_to_h1 /= np.linalg.norm(bullet_to_h1)
            bullet_to_h2 = (-bot_to_bullet + h2)
            bullet_to_h2 /= np.linalg.norm(bullet_to_h2)

            dot1 = bullet_direction.dot(bullet_to_h1)
            dot2 = bullet_direction.dot(bullet_to_h2)

            if np.sign(dot1) != np.sign(dot2):
                self.set_ang_speed(0)
                if np.abs(dot1) > np.abs(dot2):
                    self.states["Dodge"] = lambda: self.dodge(h1,bot_to_bullet)
                else:
                    self.states["Dodge"] = lambda: self.dodge(h2,bot_to_bullet)
                return True

        return False

    def roam(self):
        # Check if an opponent is visible for state change
        opponents = list(filter(lambda x: self.is_target_visible(x), self.get_opponents()))
        if len(opponents) > 0:
            # Closest opponent as target
            closest_opponent_index = np.argmin(
                [np.linalg.norm(self.get_position() - x.get_position()) for x in opponents])
            index = closest_opponent_index if type(closest_opponent_index) is np.int64 else closest_opponent_index[0]

            self.target = opponents[index]

            # Change state to shoot
            self.current_state = "Shoot"

        # Check if opponent was visible
        elif self.target is not None and isinstance(self.target, Bot):
            self.target = Point(self.target.get_position())
            self.path_to_target = self.pathfind(self.target)
            self.current_state = "Search"

        # Else, we roam
        elif self.path_to_target is None:
            # Get a random location
            ranges = self.game.grid.shape
            location = (np.random.randint(0,ranges[0]), np.random.randint(0,ranges[1]))

            # Reroll if location is not free
            while not self.game.grid[location]:
                location = (np.random.randint(0,ranges[0]), np.random.randint(0,ranges[1]))

            self.path_to_target = self.pathfind(Point(self.get_cell_pos(location)))

        # Now there's a point to go to for sure
        elif self.is_path_removable():
            self.path_to_target = None
        else:
            self.follow_path()

        if self.check_for_dodge():
            self.current_state = "Dodge"

    def get_bot_type(self):
        return 'State Controller'

    def search(self):
        # Check if an opponent is visible for state change
        opponents = list(filter(lambda x: self.is_target_visible(x), self.get_opponents()))
        if len(opponents) > 0:
            # Closest opponent as target
            closest_opponent_index = np.argmin(
                [np.linalg.norm(self.get_position() - x.get_position()) for x in opponents])
            index = closest_opponent_index if type(closest_opponent_index) is np.int64 else closest_opponent_index[0]

            self.target = opponents[index]

            # Change state to shoot
            self.current_state = "Shoot"

        if not self.is_path_removable():
            self.follow_path()
        else:
            self.target = None
            self.path_to_target = None
            self.current_state = "Roam"

        if self.check_for_dodge():
            self.current_state = "Dodge"

    def dodge(self, direction, bullet_direction):
        self.set_ang_speed(0)

        rot_mat = get_rot_mat(-self.get_rotation())

        can_move_to_direction = True
        for i in range(5):
            if not self.game.grid[self.get_grid_node(self.get_position() + (i / 5) * direction)]:
                can_move_to_direction = False

        move_to_inverse_direction = True
        for i in range(5):
            if not self.game.grid[self.get_grid_node(self.get_position() + (i / 5) * -direction)]:
                move_to_inverse_direction = False

        # Get the direction w.r.t. current rotation, normalized
        dodge_direction = np.asarray(direction * rot_mat).flatten() / np.linalg.norm(direction)

        if can_move_to_direction:
            self.set_speed(dodge_direction)
        elif move_to_inverse_direction:
            print("Moving to inverse")
            self.set_speed(-dodge_direction)
        else:
            print("Backing")
            backing_direction = np.asarray(bullet_direction * rot_mat).flatten() / np.linalg.norm(bullet_direction)
            self.set_speed(backing_direction)

        if not self.check_for_dodge():
            self.current_state = "Roam"

    def shoot_action(self):
        self.set_speed(np.array([0, 0]))

        if self.target is not None and self.rotate_towards(self.target):
            #self.shoot()
            pass

        elif self.target is not None and isinstance(self.target, Bot):
            if not self.is_target_visible(self.target):
                self.target = Point(self.target.get_position())
                self.path_to_target = self.pathfind(self.target)
                self.current_state = "Search"
            else:
                self.rotate_towards(self.target)

        if self.target is not None and isinstance(self.target, Bot) and self.target.health <= 0:
            self.target = None
            self.current_state = "Roam"

        if self.check_for_dodge():
            self.current_state = "Dodge"
