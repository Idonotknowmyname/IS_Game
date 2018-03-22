from .deepql_controller import DeepQLController
import numpy as np

from keras.models import Sequential
from keras.layers import Dense, InputLayer

from ..sprites.projectile import Projectile

class TestQLController(DeepQLController):

    # Available actions
    avail_actions = ['turn_left', 'turn_right', 'move_left', 'move_right', 'move_forw', 'move_back', 'shoot']

    # Variables given to the learner
    state_vars = ['pos_x', 'pos_y', 'rot', 'health', 'closest_enemy_x', 'closest_enemy_y', 'is_closest_enemy_visible']

    # Create a basic feedforward neural network
    def init_q_funct(self):
        # Number of network inputs
        # The variables of the state we will get
        n_inputs = len(self.state_vars)

        # Number of network outputs
        n_outputs = len(self.avail_actions)

        model = Sequential()
        model.add(InputLayer((n_inputs,)))
        model.add(Dense(10, activation='relu'))
        model.add(Dense(10, activation='relu'))
        model.add(Dense(n_outputs, activation='linear'))

        model.compile(optimizer='Adam', loss='mse')

        self.q_func = model

    def get_reward(self):

        # How many of my projectiles hit other bots
        enemy_hit = self.game.step_hits[self]

        # How many projectiles hit me
        if len(self.memory) <= 1:
            self_hit = 0
        else:
            # Get health in last state and compare with now
            self_hit = (self.last_state[4]*self.MAX_HEALTH - self.health)/Projectile.DAMAGE

        return enemy_hit - self_hit

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
        visible = 1 if self.is_target_visible(opponent) else 0

        state = np.array([x, y, rot, health, opp_x, opp_y, visible])

        return state

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

    def get_action_list(self, env_state):
        return np.arange(len(self.avail_actions))

    def get_q_val(self, state, actions):
        return self.q_func.predict(np.reshape(state, (1, len(state))))