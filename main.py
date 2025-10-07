import logging
from scenarios.scenarios import *
from controller.game_controller import GameController
from gymnasium_env.rl_constants import NULL, LOAD, TRAIN

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | %(message)s')

def main(players, roads, segmentation, render_mode = None, rl_mode: int = NULL, debug = False, test_mode = None):
    controller = GameController(roads, 
                                players, 
                                render_mode,
                                rl_mode, 
                                debug, 
                                test_mode)
    controller.run()

if __name__ == '__main__':
    main(**CIRCUIT, render_mode='human', rl_mode=TRAIN, debug=False, test_mode=['all'])
