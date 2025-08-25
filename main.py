import logging
from scenarios.scenarios import *
from controller.game_controller import GameController

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | %(message)s')

def main(players, roads, segmentation, render_mode = None, ai: bool = False, debug = False, test_mode = None):
    controller = GameController(roads, 
                                players, 
                                render_mode,
                                ai, 
                                debug, 
                                test_mode)
    controller.run()

if __name__ == '__main__':
    main(**CIRCUIT, render_mode='human', ai=True, debug=False, test_mode=['all'])
