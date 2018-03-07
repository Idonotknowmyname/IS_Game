from .collidable import Collidable

class Obstacle(Collidable):

    # Collidable properties
    BOX_HEIGHT = 100
    BOX_WIDTH = 100
    SHAPE = 1

    def __init__(self, position, height, width, rotation=0):
        self.BOX_HEIGHT = height
        self.BOX_WIDTH = width
        self.position = position
        self.rotation = rotation

    def handle_collision(self, collidable):
        return 0