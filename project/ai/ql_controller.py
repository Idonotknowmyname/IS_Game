import numpy as np
from collections import deque
from .state_controller import StateController

'''
    It's not the best source, but at least there is some pseudocode:
        https://github.com/yenchenlin/DeepLearningFlappyBird/blob/master/README.md
'''

class QLController(StateController):

    # Probability of choosing a random action
    # TODO make it as a decreasing function over time
    eps = None

    # Discount factor for future steps
    lam = None

    def __init__(self, team, game, position=None, rotation=None, eps=0.1, lam=0.9, memory_size=3000):
        super(QLController,self).__init__(team,game,position,rotation)
        self.eps = eps
        self.lam = lam
        self.memory_size = memory_size

        self.init_q_funct()
        self.init_memory()

    # No need to override
    def take_action(self):

        state = self.get_env_state()
        actions = self.get_action_list(state)

        # Might select a random action
        if np.random.rand() < self.eps:
            action = np.random.choice(actions)
        else:
            # Get Q values
            q_values = self.get_q_val(state, actions)

            # Get best action (highest Q value)
            action = actions[np.argmax(q_values)]

        self.last_action = action
        self.last_state = state

        self.execute_action(action)

    # This is called in game.update_q_learners() (at the end of the game.time_step(), after the take_action is done)
    # No need to override
    def learn(self):
        reward = self.get_reward()
        new_state = self.get_env_state()

        # Add state transition to memory
        self.add_to_memory(self.last_state, self.last_action, reward, new_state)

        # For the update, forget about current env and learn from a random state transition in the memory
        state, action, reward, next_state = self.sample_from_memory()

        # If state is terminal
        if self.game.is_game_over():
            target = reward
        else:
            actions = self.get_action_list(next_state)
            q_values = self.get_q_val(next_state, actions)
            best_action_value = q_values[0, np.argmax(q_values)]
            target = reward + self.lam * best_action_value

        self.update_q_func(state, action, target)

    # Optional override (already pretty optimized)
    def init_memory(self):
        self.memory = deque()

    # Optional override (already pretty optimized)
    def add_to_memory(self, last_state, last_action, reward, new_state):

        self.memory.append((last_state, last_action, reward, new_state))
        if len(self.memory) > self.memory_size:
            self.memory.popleft()

    # Optional override
    def sample_from_memory(self, last=False):
        # Sample a random scenario
        index = np.random.randint(len(self.memory)) if not last else len(self.memory)-1

        return self.memory[index]

    # All the following methods are to be overridden

    def init_q_funct(self):
        pass

    def get_reward(self):
        pass

    def update_q_func(self, state, action, target):
        pass

    def execute_action(self, action):
        pass

    def get_action_list(self, env_state):
        pass

    def get_env_state(self):
        pass

    def get_q_val(self, state, actions):
        pass
