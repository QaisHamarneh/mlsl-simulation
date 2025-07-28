import numpy as np
from learning.params import Params

class EpsilonGreedy:
    def __init__(self, epsilon, rng):
        self.epsilon = epsilon
        self.rng = rng

    def choose_action(self, action_space, state, qtable=None):
        """Choose an action `a` in the current world state (s)."""
        # # First we randomize a number
        # explor_exploit_tradeoff = self.rng.uniform(0, 1)

        # # Exploration
        # if explor_exploit_tradeoff < self.epsilon:
        #     action = action_space.sample()

        # # Exploitation (taking the biggest Q-value for this state)
        # else:
        #     # Break ties randomly
        #     # Find the indices where the Q-value equals the maximum value
        #     # Choose a random action from the indices where the Q-value is maximum
        #     max_ids = np.where(qtable[state, :] == max(qtable[state, :]))[0]
        #     action = self.rng.choice(max_ids)
        return (1,0)