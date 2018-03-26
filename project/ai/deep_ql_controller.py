from .ql_controller import QLController
import numpy as np
from time import time

from keras.models import Sequential
from keras.layers import Dense, InputLayer

from ..sprites.projectile import Projectile
from ..sprites.point import Point

from ..utils.utils import get_rot_mat

class DeepQLController(QLController):

    # Available actions
    avail_actions = ['turn_left', 'turn_right', 'move_left', 'move_right', 'move_forw', 'move_back', 'shoot', 'still']

    # Variables given to the learner
    state_vars = ['pos_x', 'pos_y', 'rot', 'health', 'closest_enemy_x', 'closest_enemy_y', 'is_closest_enemy_visible',
                  'closest_proj_x', 'closest_proj_y', 'closest_proj_dot', 'obs_in_front', 'obs_on_right', 'obs_on_left']

    def __init__(self, team, game, position=None, rotation=None, eps=0.1, lam=0.9, memory_size=3000, model=None):
        super(DeepQLController, self).__init__(team, game, position=None, rotation=None, eps=0.3, lam=0.9, memory_size=5000)

        if model is not None:
            self.q_func = model

    # Create a basic feedforward neural network
    def init_q_funct(self):
        # Number of network inputs
        # The variables of the state we will get
        n_inputs = len(self.state_vars)

        # Number of network outputs
        n_outputs = len(self.avail_actions)

        model = Sequential()
        model.add(InputLayer((n_inputs,)))
        model.add(Dense(12, activation='relu'))
        model.add(Dense(20, activation='relu'))
        model.add(Dense(n_outputs, activation='linear'))

        model.compile(optimizer='Adam', loss='mse')

        self.q_func = model

    def learn(self):
        reward = self.get_reward()
        new_state = self.get_env_state()

        # Add state transition to memory
        self.add_to_memory(self.last_state, self.last_action, reward, new_state)

        # If the reward is non-zero, 50% chance of learning already from last seq_length transitions
        if not reward == 0 and np.random.rand() < 0.5:
            state, action, reward, next_state = self.sample_from_memory(last=True)
        else:
            # Otherwise learn from a random sample in memory
            state, action, reward, next_state = self.sample_from_memory()

        # If state is terminal, update with reward
        if self.game.is_game_over():
            target = reward
        # Otherwise update with reward + lambda * expected_future_reward
        else:
            actions = self.get_action_list(next_state)
            q_values = self.get_q_val(next_state, actions)
            best_action_value = q_values[0, np.argmax(q_values)]
            target = reward + self.lam * best_action_value

        self.update_q_func(state, action, target)

    # Might not add to memory if reward is == 0
    def add_to_memory(self, last_state, last_action, reward, new_state):
        super(DeepQLController, self).add_to_memory(last_state, last_action, reward, new_state)

    def get_reward(self):

        # How many of my projectiles hit other bots
        enemy_hit = self.game.step_hits[self]

        # How many projectiles hit me
        if len(self.memory) <= 1:
            self_hit = 0
        else:
            # Get health in last state and compare with now
            self_hit = (self.last_state[3]*self.MAX_HEALTH - self.health)/Projectile.DAMAGE

        return (3 * enemy_hit - 2 * self_hit) * 2

    def get_env_state(self):
        scr_height, scr_width = self.game.window_size
        opp_id = np.argmin([np.linalg.norm(self.get_position() - x.get_position()) for x in self.get_opponents()])
        opponent = self.get_opponents()[opp_id]

        # Compute the state vars
        x = self.get_position()[0] / scr_width
        y = self.get_position()[1] / scr_height
        rot = self.get_rotation() / (2*np.pi)
        health = self.health / self.MAX_HEALTH
        opp_x = opponent.get_position()[0] / scr_width
        opp_y = opponent.get_position()[1] / scr_height
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

        state = np.array([x, y, rot, health, opp_x, opp_y, opp_visible, proj_x, proj_y, proj_dot, obs_front, obs_right, obs_left])

        return state

    def get_bot_type(self):
        return 'Deep QL Controller'

    def update_q_func(self, state, action, target):
        # Get what the other action values should be
        q_vals = self.get_q_val(state, None)

        # Update the value for the action to target
        q_vals[0, action] = target

        # Update the model
        self.q_func.fit(np.reshape(state, (1, len(state))), q_vals, verbose=False)

    def execute_action(self, action):
        # Order of the actions corresponds to the order in which they are enumerated at the top of the class

        if action == 0:
            # Turn left
            self.set_ang_speed(-1)
        elif action == 1:
            # Turn right
            self.set_ang_speed(1)
        elif action == 2:
            # Move left
            self.set_speed([-1, 0])
        elif action == 3:
            # Move right
            self.set_speed([1, 0])
        elif action == 4:
            # Move forward
            self.set_speed([0, 1])
        elif action == 5:
            # Move backward
            self.set_speed([0, -1])
        elif action == 6:
            # Shoot
            self.shoot()
        elif action == 7:
            # Stand still
            self.set_ang_speed(0)
            self.set_speed([0, 0])

    def get_action_list(self, env_state):
        return np.arange(len(self.avail_actions))

    def get_q_val(self, state, actions=None):
        if len(state.shape) == 1:
            return self.q_func.predict(np.reshape(state, (1, len(state))))
        else:
            return self.q_func.predict(state)

    def save_model(self, name):
        self.q_func.save('deep_q_models/{}.h5'.format(name))