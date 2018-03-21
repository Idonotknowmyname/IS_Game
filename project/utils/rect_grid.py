import numpy as np

class RectGrid():

    array = None

    def __init__(self, array, size):
        assert type(array) == np.ndarray, 'Argument array is of type {} (is not np.array)'.format(type(array))
        assert array.dtype == bool

        self.array = array
        self.cell_size = size

    def get_neighbours(self, node):
        neigh = []

        # Vertical and horizontal
        top = (node[0], node[1] + 1)
        bot = (node[0], node[1] - 1)
        left = (node[0] - 1, node[1])
        right = (node[0] + 1, node[1])

        # Diagonal
        tl = (node[0] - 1, node[1] + 1)
        tr= (node[0] + 1, node[1] + 1)
        bl = (node[0] - 1, node[1] - 1)
        br = (node[0] + 1, node[1] - 1)

        all_nodes = [top, bot, left, right, tl, tr, bl, br]

        lengths = [1] * 4
        lengths.extend([1.4142] * 4)

        for node, cost in zip(all_nodes, lengths):
            # If node is on grid and visitable
            if 0 <= node[0] < self.array.shape[0] and 0 <= node[1] < self.array.shape[1] and self.array[node]:
                neigh.append((node, cost))

        return neigh