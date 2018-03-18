import numpy as np

class Sprite:

    def __init__(self):
        self.position = None

    def get_position(self):
        return self.position

    def get_rotation(self):
        return self.rotation

    def set_position(self, position):
        self.position = np.array(position).flatten()

    def set_rotation(self, rotation):
        self.rotation = rotation