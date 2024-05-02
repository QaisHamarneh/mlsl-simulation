import os
import torch
import random
import numpy as np
from collections import deque
from model_2 import Linear_QNet, QTrainer
from snake_game_ai_2 import SnakeGameAI2

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001


class Agent:

    def __init__(self, game, player, eval=False, file_name=None, uniform=False):
        self.game = game
        self.n_actions = game.n_actions
        self.player = player
        self.file_name = file_name
        if self.file_name is None:
            self.file_name = f'model'
        if not uniform:
            self.file_name = f"{self.file_name}_{self.player}.pth"
        self.n_games = 0
        self.epsilon = 0  # randomness
        self.gamma = 0.99  # discount rate
        self.state_size = len(game.get_state(player))
        self.memory = deque(maxlen=MAX_MEMORY)  # popleft()
        self.model = Linear_QNet(
            self.player, self.state_size, 256, self.n_actions)

        if eval:
            self.load_model()
        else:
            self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def load_model(self):
        model_folder_path = './models'
        fn = os.path.join(model_folder_path, self.file_name)
        self.model.load_state_dict(torch.load(fn))

    def remember(self, state, action, reward, next_state, done):
        # popleft if MAX_MEMORY is reached
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(
                self.memory, BATCH_SIZE)  # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        # for state, action, reward, nexrt_state, done in mini_sample:
        #    self.trainer.train_step(state, action, reward, next_state, done)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state, eval=False):
        # random moves: tradeoff exploration / exploitation
        self.epsilon = 250 - self.n_games
        final_move = [0] * self.n_actions
        if not eval and random.randint(0, 500) < self.epsilon:
            move = random.randint(0, self.n_actions - 1)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


def train(episodes, players=2, file_name=None):
    game = SnakeGameAI2(players=players)
    record = 0
    done = [False] * players
    agents = [Agent(game=game, player=i, file_name=file_name)
              for i in range(players)]
    scores = np.asarray([0] * players)
    n_games = 0
    # while True:
    while n_games < episodes:
        for player in range(players):
            if not done[player]:
                # get old state
                state_old = game.get_state(player)

                # get move
                final_move = agents[player].get_action(state_old)

                # perform move and get new state
                reward, done[player], scores[player] = game.play_step(
                    player, final_move)
                state_new = game.get_state(player)

                # train short memory
                agents[player].train_short_memory(
                    state_old, final_move, reward, state_new, done)

                # remember
                agents[player].remember(
                    state_old, final_move, reward, state_new, done)

        if any(done):
            # train long memory, plot result
            game.reset()
            n_games += 1
            for i in range(players):
                agents[i].n_games += 1
                agents[i].train_long_memory()

                if scores[i] > record:
                    record = scores[i]
                    print(f"Game {n_games}: player {i} record {record}")
                    for j in range(players):
                        agents[i].model.save(
                            file_name=agents[j].file_name)
                        agents[j].load_model()

            done = [False] * players


def eval(episodes, players=2, file_name=None, uniform=False):
    game = SnakeGameAI2(render=True, players=players)
    records = [0] * players
    done = [False] * players
    agents = [Agent(game=game, player=i, eval=True, file_name=file_name, uniform=uniform)
              for i in range(players)]
    scores = np.asarray([0] * players)
    n_games = 0
    while n_games < episodes:
        for player in range(players):
            if not done[player]:
                # get old state
                state_old = game.get_state(player)

                # get move
                final_move = agents[player].get_action(state_old, eval=True)

                # perform move and get new state
                _, done[player], scores[player] = game.play_step(
                    player, final_move)

        if any(done):
            # train long memory, plot result
            game.reset()
            n_games += 1

            print(f'Game {n_games}:')
            for player in range(players):
                agents[player].n_games += 1
                print(
                    f'Agent {player}: Score {scores[player]}   Record: {records[player]}')

            done = [False] * players


if __name__ == '__main__':
    # Works for up to 4 players
    fn = "m13"
    # print("\n\n\n\nTraining")
    # train(1000, players=6, file_name=fn)
    print("\n\n\n\nEvaluating")
    eval(5, players=4, file_name=fn)
