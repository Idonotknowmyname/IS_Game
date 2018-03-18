import numpy as np
from time import time

def get_rot_mat(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.matrix('{} {}; {} {}'.format(c, -s, s, c))

# Check if two collidables objects are colliding
def colliding(obj_1, obj_2):
    shape_1 = obj_1.SHAPE
    shape_2 = obj_2.SHAPE

    dist = np.sqrt(np.dot((obj_1.get_position() - obj_2.get_position()), (obj_1.get_position() - obj_2.get_position())))

    # Both circles
    if shape_1 == 0 and shape_2 == 0:
        if dist < (obj_1.RADIUS + obj_2.RADIUS):
            return True
        else:
            return False
    # If one is a rectangle and the other a circle
    elif (shape_1 == 0 and shape_2 == 1) or (shape_1 == 1 and shape_2 == 0):
        if shape_1 == 1:
            rect = obj_1
            circ = obj_2
        else:
            circ = obj_1
            rect = obj_2

        # Preliminary check, if they could be intersecting or not based on rect circumscribed circle
        rect_half_diag = np.sqrt(np.square(rect.BOX_HEIGHT/2) + np.square(rect.BOX_WIDTH/2))
        if dist > (circ.RADIUS + rect_half_diag):
            return False

        # Assume the circle is NOT! inside the rectangle
        # TODO implement if needed

        # Get the Rect vertices
        rect_bbox = rect.get_bbox()

        # Iter through edges and check if they intersect
        for i in range(4):
            vertex_1 = rect_bbox[i-1]
            vertex_2 = rect_bbox[i]

            # Check if first vertex is inside circle
            if np.sqrt(np.dot((circ.get_position() - vertex_1), (circ.get_position() - vertex_1))) < circ.RADIUS:
                return True

            # Check if we are on the correct side of the edge
            d = np.cross(vertex_2-vertex_1, vertex_1-circ.get_position())
            if d < 0:
                continue

            # Check if edge intersect circle
            dist_from_edge = np.linalg.norm(d)/np.linalg.norm(vertex_2-vertex_1)

            if dist_from_edge < circ.RADIUS:
                return True
    # If both are rectangles
    else:
        # Check for each edge if it can be used as a separating axis
        # (source:https://stackoverflow.com/questions/10962379/how-to-check-intersection-between-2-rotated-rectangles)
        vertices_1 = obj_1.get_bbox()
        vertices_2 = obj_2.get_bbox()

        start = time()

        # Loop over vertices of Obj_1
        for i in range(4):
            vertex_1 = vertices_1[i-1]
            vertex_2 = vertices_1[i]

            normal = np.array([vertex_2[1] - vertex_1[1], vertex_1[0] - vertex_2[0]])

            min_a = max_a = None

            for other_vertex in vertices_1:
                projection = np.dot(normal, other_vertex)
                if min_a is None or projection < min_a:
                    min_a = projection
                if max_a is None or projection > max_a:
                    max_a = projection

            min_b = max_b = None

            for other_vertex in vertices_2:
                projection = np.dot(normal, other_vertex)
                if min_b is None or projection < min_b:
                    min_b = projection
                if max_b is None or projection > max_b:
                    max_b = projection

            # Avg time of execution of method until here = 2.7e-05
            if max_a < min_b or max_b < min_a:
                return False

        # Loop over vertices of Obj_2
        for i in range(4):
            vertex_1 = vertices_2[i - 1]
            vertex_2 = vertices_2[i]

            normal = np.array([vertex_2[1] - vertex_1[1], vertex_1[0] - vertex_2[0]])

            min_a = max_a = None

            for other_vertex in vertices_1:
                projection = np.dot(normal, other_vertex)
                if min_a is None or projection < min_a:
                    min_a = projection
                if max_a is None or projection > max_a:
                    max_a = projection

            min_b = max_b = None

            for other_vertex in vertices_2:
                projection = np.dot(normal, other_vertex)
                if min_b is None or projection < min_b:
                    min_b = projection
                if max_b is None or projection > max_b:
                    max_b = projection

            # Avg time of execution of method until here: 6.6e-05
            if max_a < min_b or max_b < min_a:
                return False

        # Avg time of execution of method until here: 8.6e-05
        return True

    return False


