import numpy as np
from .pathfind_controller import PathfindController
from ..sprites.bot import Bot
from ..sprites.point import Point
from ..utils.utils import get_rot_mat

class ClusterHiveBot(PathfindController):

    # State vars
    states = None
    current_state = None

    # Dodging vars
    can_dodge_direction = None
    can_dodge_inverse_direction = None
    backing_direction = None
    dodge_direction = None

    def __init__(self, team, game, position=None, rotation=None):
        super(ClusterHiveBot,self).__init__(team,game,position,rotation)
        self.states = {}
        self.initialize_states()

    def initialize_states(self):

        # Search
        self.states["Go"] = self.go

        # Fire at target
        self.states["Shoot"] = self.shoot_action

        # Dodge bullets
        self.states["Dodge"] = self.dodge

        # Wait
        self.states["Wait"] = self.wait

        self.last_state = None

    def take_action(self):

        if self.check_for_dodge():
            self.current_state = "Dodge"

        self.states[self.current_state]()

        if not self.current_state == self.last_state:
            pass
            # print('State transition! From {} to {}'.format(self.last_state, self.current_state))

        self.last_state = self.current_state

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

    def go(self):

        # Now there's a point to go to for sure
        if self.path_to_target is not None and self.is_path_removable():
            self.path_to_target = None
            self.current_state = "Wait"
        elif self.path_to_target is not None:
            self.follow_path()
        else:
            self.current_state = "Wait"

    def get_bot_type(self):
        return 'Cluster Hive Bot'

    def dodge(self, direction, bullet_direction):
        self.set_ang_speed(0)

        if self.dodge_direction is None:
            rot_mat = get_rot_mat(-self.get_rotation())

            self.can_dodge_direction = True
            for i in range(5):
                if not self.game.grid[self.get_grid_node(self.get_position() + (i / 5) * direction)]:
                    self.can_dodge_direction = False

            self.can_dodge_inverse_direction = True
            for i in range(5):
                if not self.game.grid[self.get_grid_node(self.get_position() + (i / 5) * -direction)]:
                    self.can_dodge_inverse_direction = False

            # Get the direction w.r.t. current rotation, normalized
            self.dodge_direction = np.asarray(direction * rot_mat).flatten() / np.linalg.norm(direction)
            self.backing_direction = np.asarray(bullet_direction * rot_mat).flatten() / np.linalg.norm(bullet_direction)

        if self.can_dodge_direction:
            self.set_speed(self.dodge_direction)
        elif self.can_dodge_inverse_direction:
            self.set_speed(-self.dodge_direction)
        else:
            self.set_speed(self.backing_direction)

        if not self.check_for_dodge():
            self.current_state = "Wait"
            self.dodge_direction = None

    def shoot_action(self):
        self.set_speed(np.array([0, 0]))

        if self.target is not None and self.rotate_towards(self.target):
            self.shoot()
            pass

        if self.target is not None and isinstance(self.target, Bot) and self.target.health <= 0:
            self.target = None
            self.current_state = "Wait"

        if self.check_for_dodge():
            self.current_state = "Dodge"

    def wait(self):
        pass
