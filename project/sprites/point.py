from .collidable import Collidable

class Point(Collidable):
    SHAPE = 2

    def __init__(self, position):
        self.position = position