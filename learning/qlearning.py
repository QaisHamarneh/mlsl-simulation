import numpy as np

class Qlearning:
    def __init__(self, learning_rate, gamma, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.reset_qtable()

    def update(self, state, action, reward, new_state):
        """Update Q(s,a):= Q(s,a) + lr [R(s,a) + gamma * max Q(s',a') - Q(s,a)]"""
        # delta = (
        #     reward
        #     + self.gamma * np.max(self.qtable[new_state, :])
        #     - self.qtable[state, action]
        # )
        # q_update = self.qtable[state, action] + self.learning_rate * delta
        # return q_update
        return None

    def reset_qtable(self):
        """Reset the Q-table."""
        # self.qtable = np.zeros((self.state_size, self.action_size))
        return None