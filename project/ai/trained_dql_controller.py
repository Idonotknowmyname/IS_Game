import numpy as np
from time import time
from keras.layers import InputLayer, Dense
from keras.models import Sequential

from .state_controller import StateController
from .deep_ql_controller import DeepQLController

from ..sprites.obstacle import Obstacle
from ..sprites.point import Point

from ..utils.utils import get_rot_mat

class TrainedDQLController(StateController):

    # Available actions
    avail_actions = ['turn_left', 'turn_right', 'move_left', 'move_right', 'move_forw', 'move_back', 'shoot', 'still']

    # Variables given to the learner
    state_vars = ['pos_x', 'pos_y', 'rot', 'health', 'closest_enemy_direction', 'closest_enemy_dist', 'is_closest_enemy_visible',
                  'closest_proj_x', 'closest_proj_y', 'closest_proj_dot', 'obs_in_front', 'obs_on_right', 'obs_on_left']


    def __init__(self, team, game, position=None, rotation=None, model=None):
        super(TrainedDQLController, self).__init__(team,game,position,rotation)

        self.train_err = []

        if model == None:
            self.init_q_funct()
        else:
            self.q_func = model



    def init_q_funct(self):
        # Number of network inputs
        # The variables of the state we will get
        n_inputs = len(self.state_vars)

        # Number of network outputs
        n_outputs = len(self.avail_actions)

        model = Sequential()
        model.add(InputLayer((n_inputs,)))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(32, activation='tanh'))
        model.add(Dense(n_outputs, activation='linear'))

        model.compile(optimizer='Adam', loss='mse')

        self.q_func = model


    def take_action(self):
        super(TrainedDQLController, self).take_action()
        
        curr_state = self.get_env_state()
        curr_state = np.reshape(curr_state, (1, len(curr_state)))

        action_vals = self.extract_actions()
        action_vals = np.reshape(action_vals, (1, len(action_vals)))

        hist = self.q_func.fit(curr_state, action_vals, epochs=1, verbose=0)

        self.train_err.extend(hist.history['loss'])


    def extract_actions(self):
        l_turn = 1 if self.get_ang_speed() == -1 else 0
        r_turn = 1 if self.get_ang_speed() == 1 else 0

        half = np.sqrt(2)

        l_move = 1 if self.get_speed()[0] < -half else 0
        r_move = 1 if self.get_speed()[0] >= half else 0

        f_move = 1 if self.get_speed()[1] >= half else 0
        b_move = 1 if self.get_speed()[1] < -half else 0

        shoot = 1 if self.current_state == 'Shoot' else 0

        still = 1 if l_move == r_move == f_move == b_move == shoot == 0 else 0

        actions = np.array([l_turn, r_turn, l_move, r_move, f_move, b_move, shoot, still])

        # Choose a random action with value 1 and set it as active, set the rest to zero
        rand_id = np.random.choice(np.arange(len(actions))[actions==1])

        ret_actions = np.zeros(len(actions))
        ret_actions[rand_id] = 1

        return ret_actions

    def get_env_state(self):
        scr_height, scr_width = self.game.window_size
        opp_id = np.argmin([np.linalg.norm(self.get_position() - x.get_position()) for x in self.get_opponents()])
        opponent = self.get_opponents()[opp_id]

        # Compute the state vars
        x = self.get_position()[0] / scr_width
        y = self.get_position()[1] / scr_height
        rot = self.get_rotation() / (2*np.pi)
        health = self.health / self.MAX_HEALTH

        vect_dist = opponent.get_position() - self.get_position()
        opp_dist = np.linalg.norm(vect_dist) / np.linalg.norm([scr_width, scr_height])
        opp_dir = np.arctan2(vect_dist[1], vect_dist[0])
        opp_dir = (-opp_dir + np.pi / 2) % (np.pi * 2) / (np.pi * 2)

        opp_visible = 1 if self.is_target_visible(opponent) else 0
        proj = self.get_closest_enemy_projectile()

        if proj is None:
            proj_x = -1
            proj_y = -1
            proj_dot = 0
        else:

            proj_x = proj.get_position()[0] / scr_width
            proj_y = proj.get_position()[1] / scr_height

            dir_vec = self.get_position() - proj.get_position()

            proj_speed = np.asarray(proj.get_speed() * get_rot_mat(proj.get_rotation())).flatten()

            proj_dot = np.dot(proj_speed, dir_vec / np.linalg.norm(dir_vec))/2 + 0.5

        # Get obstacles around
        # Create a point in front, one on the right and one on the left

        rel_pos_front = np.array([0, self.RADIUS * 4])
        rel_pos_right = np.array([self.RADIUS * 4, 0])
        rel_pos_left = np.array([-self.RADIUS * 4, 0])

        all_pos = np.vstack([rel_pos_front, rel_pos_right, rel_pos_left])

        rel_rot_pos = np.asarray(all_pos * get_rot_mat(self.get_rotation()))

        point_front = Point(self.get_position() + rel_rot_pos[0, :])
        point_right = Point(self.get_position() + rel_rot_pos[1, :])
        point_left = Point(self.get_position() + rel_rot_pos[2, :])

        obs_front = 1 if self.game.collides_with(point_front, 'obstacle') else 0

        obs_right = 1 if self.game.collides_with(point_right, 'obstacle') else 0

        obs_left = 1 if self.game.collides_with(point_left, 'obstacle') else 0

        state = np.array([x, y, rot, health, opp_dist, opp_dir, opp_visible, proj_x, proj_y, proj_dot, obs_front, obs_right, obs_left])

        return state

    def save_model(self, name):
        self.q_func.save('deep_q_models/{}.h5'.format(name))

    def get_bot_type(self):
        return 'Deep QL Controller'