from ..utils.utils import get_rot_mat
from .sprite import Sprite
import numpy as np

class Dynamic(Sprite):

    def __init__(self):
        self.speed = None
        self.rotation = None

    def rotate_by(self, delta_rot):
        self.rotation += delta_rot

    def move_by(self, delta_position):
        self.position[0] += delta_position
        self.position[1] += delta_position

    def set_speed(self, new_speed):
        self.speed = np.array(new_speed)

    def add_speed_y(self, value):
        self.speed[1] += value

    def add_speed_x(self, value):
        self.speed[0] += value

    def get_speed(self):
        return self.speed

    def set_ang_speed(self, new_ang_speed):
        self.ang_speed = new_ang_speed

    def get_ang_speed(self):
        return self.ang_speed

        # One iteration step

    def update(self, delta_t):
        if delta_t > 0:
            self.rotation += self.ang_speed * self.MAX_ANG_SPEED * delta_t
            self.rotation = (self.rotation % (np.pi * 2))
        displacement = np.asarray(self.speed * get_rot_mat(self.rotation) * self.MAX_SPEED * delta_t)
        self.position = displacement.flatten() + self.position
