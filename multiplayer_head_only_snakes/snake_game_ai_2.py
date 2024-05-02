import pygame
import random
from enum import Enum
from collections import namedtuple
import numpy as np

pygame.init()
font = pygame.font.SysFont('arial', 25)


class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4


Point = namedtuple('Point', 'x, y')

# rgb colors
WHITE = (255, 255, 255)
BGREEN = (0, 200, 200)
BLUE1 = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLUE3 = (0, 100, 150)

RED1 = (255, 0, 0)
RED2 = (255, 100, 0)
RED3 = (150, 100, 0)
YELLOW = (255, 170, 51)

COLORS = [(153, 0, 0), (255,102, 102), (255, 128, 0),
          (255, 255, 0), (102, 204, 0), (0, 255, 255),
          (127, 0, 255), (255, 0, 255), (224, 224, 224)]

BLACK = (0, 0, 0)

SPEED = 40


def dist(p1, p2):
    return np.linalg.norm([p1.x - p2.x, p1.y - p2.y])


class SnakeGameAI2:

    def __init__(self, players=2, w=640, h=480, block_size=20, render=False):
        self.players = players
        self.n_actions = 3
        # self.w = max(w, self.players * 320)
        # self.h = max(h, self.players * 240)
        self.w = 800
        self.h = 800
        self.block_size = block_size
        self.render = render
        # init display
        if self.render:
            self.display = pygame.display.set_mode((self.w, self.h))
            pygame.display.set_caption('Multi Player Snake')
            self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        # init game state
        self.directions = [Direction.LEFT if i % 2 ==
                           0 else Direction.RIGHT for i in range(self.players)]

        self.cars = [Point(self.w / 2, i * self.h / (self.players + 1))
                     for i in range(1, self.players + 1)]

        self.scores = [0] * self.players
        self.foods = [None] * self.players
        self.got_food = [0] * self.players
        self.useless_iterations = 0
        for i in range(self.players):
            self._place_food(i)

    def _place_food(self, player):
        self.got_food[player] = 1
        if all([self.got_food[i] == 1 for i in range(self.players)]):
            self.useless_iterations = 0
            self.got_food = [0] * self.players

        x = random.randint(0, (self.w-self.block_size) //
                           self.block_size)*self.block_size
        y = random.randint(0, (self.h-self.block_size) //
                           self.block_size)*self.block_size
        while any([Point(x, y) == self.cars[i] for i in range(self.players)]):
            x = random.randint(0, (self.w-self.block_size) //
                               self.block_size)*self.block_size
            y = random.randint(0, (self.h-self.block_size) //
                               self.block_size)*self.block_size

        self.foods[player] = Point(x, y)

    def play_step(self, player, action):
        self.useless_iterations += 1

        # 1. collect user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # 2. move
        old_dist_to_food = dist(self.cars[player], self.foods[player])
        self._move(player, action)  # update the head

        new_dist_to_food = dist(self.cars[player], self.foods[player])

        # 3. check if game over
        reward = 0
        if self.useless_iterations > (self.h / self.block_size) + (self.w / self.block_size):
            reward = -5

        reward = 0
        if new_dist_to_food >= old_dist_to_food:
            reward = -.5
        else:
            reward = .5
        game_over = False
        if self.is_collision(player) or self.useless_iterations > (self.h / self.block_size) * (self.w / self.block_size):
            game_over = True
            reward = -1000
            return reward, game_over, self.scores[player]

        # 4. place new food or just move
        if self.cars[player] == self.foods[player]:
            self.scores[player] += 1
            reward = 1000
            self._place_food(player)

        if self.scores[player] > 100:
            game_over = True
            reward = 1000_000
            return reward, game_over, self.scores[player]

        # 5. update ui and clock
        if self.render and player == self.players - 1:
            self._update_ui()
            self.clock.tick(SPEED)
        # 6. return game over and score
        return reward, game_over, self.scores[player]

    def is_collision(self, player, pt=None):
        if pt is None:
            pt = self.cars[player]
        # hits boundary
        if pt.x > self.w - self.block_size or pt.x < 0 or pt.y > self.h - self.block_size or pt.y < 0:
            return True
        # hits other cars
        if any([pt == self.cars[i] for i in range(self.players) if i != player]):
            return True
        return False

    def _move(self, player, action):
        # [straight, right, left]

        clock_wise = [Direction.RIGHT, Direction.DOWN,
                      Direction.LEFT, Direction.UP]

        idx = clock_wise.index(self.directions[player])

        if np.array_equal(action, [1, 0, 0]):
            new_dir = clock_wise[idx]  # no change
        elif np.array_equal(action, [0, 1, 0]):
            next_idx = (idx + 1) % 4
            new_dir = clock_wise[next_idx]  # right turn r -> d -> l -> u
        else:  # [0, 0, 1]
            next_idx = (idx - 1) % 4
            new_dir = clock_wise[next_idx]  # left turn r -> u -> l -> d

        x = self.cars[player].x
        y = self.cars[player].y
        if new_dir == Direction.RIGHT:
            x += self.block_size
        elif new_dir == Direction.LEFT:
            x -= self.block_size
        elif new_dir == Direction.DOWN:
            y += self.block_size
        elif new_dir == Direction.UP:
            y -= self.block_size

        self.directions[player] = new_dir
        self.cars[player] = Point(x, y)

    def _update_ui(self):
        self.display.fill(BLACK)

        for player in range(self.players):
            pygame.draw.rect(self.display, COLORS[player], pygame.Rect(
                self.cars[player].x, self.cars[player].y, self.block_size, self.block_size))

            pygame.draw.rect(self.display, COLORS[player], pygame.Rect(
                self.foods[player].x, self.foods[player].y, self.block_size, self.block_size))

        text = font.render(
            f"High Score: {max(self.scores)}", True, WHITE)
        self.display.blit(text, [0, 0])
        pygame.display.flip()

    def get_state(self, player):
        head = self.cars[player]
        point_l = Point(head.x - self.block_size, head.y)
        point_r = Point(head.x + self.block_size, head.y)
        point_u = Point(head.x, head.y - self.block_size)
        point_d = Point(head.x, head.y + self.block_size)

        point_ll = Point(head.x - 2 * self.block_size, head.y)
        point_rr = Point(head.x + 2 * self.block_size, head.y)
        point_uu = Point(head.x, head.y - 2 * self.block_size)
        point_dd = Point(head.x, head.y + 2 * self.block_size)

        dir_l = self.directions[player] == Direction.LEFT
        dir_r = self.directions[player] == Direction.RIGHT
        dir_u = self.directions[player] == Direction.UP
        dir_d = self.directions[player] == Direction.DOWN

        state = [
            # Danger straight
            (dir_r and self.is_collision(player, point_r)) or
            (dir_l and self.is_collision(player, point_l)) or
            (dir_u and self.is_collision(player, point_u)) or
            (dir_d and self.is_collision(player, point_d)),

            (dir_r and self.is_collision(player, point_rr)) or
            (dir_l and self.is_collision(player, point_ll)) or
            (dir_u and self.is_collision(player, point_uu)) or
            (dir_d and self.is_collision(player, point_dd)),

            # Danger right
            (dir_u and self.is_collision(player, point_r)) or
            (dir_d and self.is_collision(player, point_l)) or
            (dir_l and self.is_collision(player, point_u)) or
            (dir_r and self.is_collision(player, point_d)),

            (dir_u and self.is_collision(player, point_rr)) or
            (dir_d and self.is_collision(player, point_ll)) or
            (dir_l and self.is_collision(player, point_uu)) or
            (dir_r and self.is_collision(player, point_dd)),

            # Danger left
            (dir_d and self.is_collision(player, point_r)) or
            (dir_u and self.is_collision(player, point_l)) or
            (dir_r and self.is_collision(player, point_u)) or
            (dir_l and self.is_collision(player, point_d)),

            # Move direction
            dir_l,
            dir_r,
            dir_u,
            dir_d,

            # Food location
            self.foods[player].x < head.x,  # food left
            self.foods[player].x > head.x,  # food right
            self.foods[player].y < head.y,  # food up
            self.foods[player].y > head.y  # food down
        ]

        return np.array(state, dtype=int)


if __name__ == '__main__':
    players = 8
    game = SnakeGameAI2(render=True, players=players)
    scores = [0] * players
    episodes = 10
    for epi in range(episodes):
        game_over = False
        game.reset()
        # game loop
        while True:
            for player in range(players):
                action = [0, 0, 0]
                ran = random.choice(range(3))
                action[ran] = 1
                _, p_game_over, scores[player] = game.play_step(player, action)
                game_over = game_over or p_game_over

            if game_over:
                break

        print(f"Episode {epi}:")

        print(
            [f"Score {player}: {scores[player]}" for player in range(players)])

    pygame.quit()
