import numpy as np

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
        return dist < (obj_1.RADIUS + obj_2.RADIUS)

    # If one is a rectangle and the other a circle
    if (shape_1 == 0 and shape_2 == 1) or (shape_1 == 1 and shape_2 == 0):
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

            # Check if vertices are inside circle
            if np.sqrt(np.dot((circ.get_position() - vertex_1), (circ.get_position() - vertex_1))) < circ.RADIUS or np.sqrt(
                    np.dot((circ.get_position() - vertex_2), (circ.get_position() - vertex_2))) < circ.RADIUS:
                return True


            # Check if edge intersect circle
            dist_from_edge = np.linalg.norm(np.cross(vertex_2-vertex_1, vertex_1-circ.get_position()))/np.linalg.norm(vertex_2-vertex_1)

            if dist_from_edge < circ.RADIUS:
                return True


    return False


