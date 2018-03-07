from .sprite import Sprite
import numpy as np
from ..utils.utils import get_rot_mat

class Collidable(Sprite):

    BOX_WIDTH = 0
    BOX_HEIGHT = 0
    RADIUS = 0
    # Shape of 0 = circle
    #          1 = rectangle
    SHAPE = None

    def __init__(self):
        pass

    # Return a list of vertices in the following order [top_left, bot_left, bot_right, top_right]
    # To be moved in Collidable
    def get_bbox(self):

        rel_pos_tl = np.array([-self.BOX_WIDTH / 2, self.BOX_HEIGHT / 2])
        rel_pos_bl = rel_pos_tl - np.array([0, self.BOX_HEIGHT])

        rot_mat = get_rot_mat(self.rotation)
        # Obtain top-left corner relative position
        rotated_top_left = np.asarray(rel_pos_tl * rot_mat).flatten()

        # Obtain bottom_left corner relative position
        rotated_bot_left = np.asarray(rel_pos_bl * rot_mat).flatten()

        vertices = np.vstack([rotated_top_left, rotated_bot_left, -rotated_top_left, -rotated_bot_left])
        rep_pos = np.array([self.position] * 4)
        vertices = rep_pos + vertices
        return vertices


    # Returns 0 if nothing should happen, -1 if the object is to be removed after collision, 1 if the object should be
    # moved backwards (e.g. bot into bot or bot into wall)
    # Other codes might have other meanings (not implemented yet)
    def handle_collision(self, collidable):
        return -1