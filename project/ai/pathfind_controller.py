import numpy as np
from time import time
from .base_controller import BaseController

from ..utils.utils import get_rot_mat
from ..utils.rect_grid import RectGrid
from ..utils.priority_queue import PriorityQueue

from ..sprites.point import Point

class PathfindController(BaseController):

    target = None
    path_to_target = None

    def take_action(self):

        self.target = self.get_opponents()[0]
        target = self.target

        if self.is_target_visible(target):
            self.set_speed(np.array([0,0]))
            self.path_to_target = None
            if self.rotate_towards(target):
                self.shoot()
        else:
            self.reach_target(target)


    def reach_target(self, target):
        if self.path_to_target is None:
            self.path_to_target = self.pathfind(target)
            self.path_step = 0
        elif self.is_path_removable():
            self.path_to_target = None
        else:
            self.follow_path()

    def follow_path(self):
        target_cell = self.path_to_target[self.path_step]
        curr_cell = self.get_grid_node(self.get_position())

        # If the next step in the path is reached
        if target_cell == curr_cell:
            self.path_step += 1
        else:
            target_pos = self.get_cell_pos(target_cell)
            dist_vec = target_pos - self.get_position()

            abs_dir_vec = dist_vec/np.linalg.norm(dist_vec)
            speed = np.asarray(abs_dir_vec * get_rot_mat(-self.get_rotation())).flatten()

            self.rotate_towards(Point(target_pos))
            self.set_speed(speed)

    def pathfind(self, target, algorithm='A*'):

        rect_grid = RectGrid(self.game.grid, self.game.cell_size)

        start_node = self.get_grid_node(self.get_position())
        target_node = self.get_grid_node(target.get_position())

        frontier = PriorityQueue()
        frontier.put(start_node, 0)

        cost_so_far = np.empty(rect_grid.array.shape, dtype=float)
        cost_so_far[:] = -1
        came_from = np.empty(rect_grid.array.shape, dtype=object)

        came_from[start_node] = None
        cost_so_far[start_node] = 0

        # A* algorithm
        while not frontier.empty():
            current = frontier.get()
            if current == target_node:
                break
            for next, cost in rect_grid.get_neighbours(current):
                new_cost = cost_so_far[current] + cost
                if cost_so_far[next] == -1 or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + self.heuristics(target_node, next)
                    frontier.put(next, priority)
                    came_from[next] = current

        # Backtrack to find path
        path = []
        current = target_node
        print('Traceback starting node {} [target]'.format(current))
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()

        print('Path found of length {}'.format(len(path)))

        return path

    def is_path_removable(self):
        if self.path_step == len(self.path_to_target) - 1:
            return True

        return False


    def heuristics(self, target_node, current_node, mode='eucl'):
        curr_x, curr_y = current_node
        tar_x, tar_y = target_node

        if mode == 'eucl':
            return np.linalg.norm((tar_x - curr_x, tar_y - curr_y))


    def get_grid_node(self, position):
        size = self.game.cell_size
        i = int(position[1]/size)
        j = int(position[0]/size)
        return (i, j)

    def get_cell_pos(self, node):
        size = self.game.cell_size
        x = (node[1] + 0.5) * size
        y = (node[0] + 0.5) * size

        return np.array([x,y])
