import configparser
import json
import csv
import os
import sys
import logging
from enum import Enum
from random import choice, uniform
from math import sqrt, hypot
from argparse import ArgumentParser

logger = logging.getLogger(__name__)

MAX_ROUNDS = 50
SHEEP_NUMBER = 15
POSITION_LIMIT = 10
SHEEP_STEP = 0.5
WOLF_STEP = 1.0

def euclidean_distance2(point1, point2):
    return sum((cor1-cor2)**2 for cor1, cor2 in zip(point1, point2))

class Direction(Enum):
    # sheep can move only in the four main directions
    NORTH = (0, 1) # (x,y)
    SOUTH = (0, -1)
    EAST = (1, 0)
    WEST = (-1, 0)

class Sheep:
    def __init__(self, index, position: tuple):
        self.index = index
        self._position = position
        self.alive = False
        self.step = SHEEP_STEP

        logger.debug(f'Sheep number {self.index} initialized on position {position}')

    @property
    def position(self):
        return self._position if self.alive else None
    @position.setter
    def position(self, value):
        self._position = value

    def __str__(self):
        return f'Sheep {self.index} on position {self._position} is {'Alive' if self.alive else 'Dead'} and can move {self.step} steps'

    def move(self):
        direction = choice(list(Direction))
        logger.debug('Sheep moving in ', direction)

        if direction in (Direction.NORTH, Direction.SOUTH):
            self.position = (self._position[0] + direction.value[0] * self.step, self._position[1])
        elif direction in (Direction.EAST, Direction.WEST):
            self.position = (self._position[0], self._position[1] + direction.value[1] * self.step)

        logger.debug('Sheep moved to ', self._position)

class Wolf:
    def __init__(self, position: tuple):
        self.position = position
        self.prey = None
        self.step = WOLF_STEP

    def __str__(self):
        return f'Wolf on position {self.position} can move {WOLF_STEP}'

    # check are all sheeps in herd alive in the main before parsing here

    def move(self, herd: list['Sheep']):
        logger.info('Wolf is chasing!')

        self.prey = herd[0]
        for sheep in herd[1:]:
            if euclidean_distance2(self.position, sheep.position) < euclidean_distance2(self.position, self.prey.position):
                self.prey = sheep
        logger.debug('Wolf prey is ', self.prey)

        distance = sqrt(euclidean_distance2(self.position, self.prey.position))
        logger.debug('The distance from the wolf to the sheep is ', distance)

        if distance <= self.step:
            self.position = self.prey.position
            self.prey.alive = False
            logger.info(f'Wolf has moved to a position {self.position} and eaten a sheep {self.prey.index}')
        else:
            move_vector = self.prey.position[0]-self.position[0], self.prey.position[1]-self.position[1]
            logger.debug('Wolf will be moved in a direction of ', move_vector, 'vector')

            step_length = hypot(*move_vector)
            logger.debug(f'Wolf will move by a {step_length} step')

            x = move_vector[0]/step_length
            x *= self.step
            y = move_vector[1]/step_length
            y *= self.step

            self.position = (self.position[0]+x,self.position[1]+y)

            logger.info(f'Wolf is still chasing! The pray {self.prey.alive} stays alive!')
        logger.debug(f'Wolf moved to position {self.position}')


if __name__ == '__main__':
    max_rounds = MAX_ROUNDS
    sheep_number = SHEEP_NUMBER
    position_limit = POSITION_LIMIT

    arg_parser = ArgumentParser(
        prog = 'Chasing Sheep',
        description = 'Simulator of a wolf chasing a herd of sheep'
    )

    arg_parser.add_argument('-c', '--config', type=str, help='Load configuration from .ini file')
    arg_parser.add_argument('-l', '-log', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Logging level')
    arg_parser.add_argument('-r', '--rounds', type=int, default=MAX_ROUNDS, help='Number of sheep rounds')
    arg_parser.add_argument('-s', '--sheep', type=int, default=SHEEP_NUMBER, help='Sheep number')
    arg_parser.add_argument('-w', '--wait', action='store_true', help='Wait until sheep moved for a set time')

    args = arg_parser.parse_args(sys.argv[1:])

    if args.log:
        logging.basicConfig(filename='chase.log', level=getattr(logging, args.l.upper()))
    else:
        logging.disable()

    if args.rounds:
        if args.round <= 0:
            raise ValueError('Round cannot be less than 0')
        max_rounds = args.rounds

    if args.sheep:
        if args.sheep <= 0:
            raise ValueError('Sheep number cannot be less than 0')
        sheep_number = args.sheep

    if args.config:
        config = configparser.ConfigParser()
        config.read(args.config)

        if os.path.isfile(args.config):
            config.read(args.config)

            position_limit = float(['Sheep'], ['InitPosLimit'])
            if position_limit <= 0: raise ValueError('Position limit must be positive')

            sheep_step = float(['Sheep'], ['MoveDist'])
            if sheep_step <= 0: raise ValueError('Sheep step must be positive')

            wolf_step = float(['Wolf'], ['MoveDist'])
            if wolf_step <= 0: raise ValueError('Wolf step must be positive')

            logger.debug(f'.ini configuration file loded with positition {position_limit}, sheep step {sheep_step}, wolf step {wolf_step}')
        else:
            raise FileNotFoundError('Configuration file not found')


    Sheep.step = sheep_step
    Wolf.step = wolf_step

    ''' 
    random.uniform(a, b)
    Return a random floating-point number N such that a <= N <= b for a <= b and b <= N <= a for b < a.
    '''
    sheep_cor = uniform(-position_limit, position_limit)
    herd = [Sheep(i, (sheep_cor, sheep_cor)) for i in range(sheep_number)]
    alive_herd = [s for s in herd if s.alive ]
    logger.info('Herd is ready for the game!')

    wolf = Wolf((0,0))

    results = []

    for r in range(max_rounds):
        logger.info(f'Round {r} started!')
        print('New round started! Get ready!')
        print('Round: ', r, ' Alive sheep: ', len(alive_herd))

        for sheep in alive_herd:
            sheep.move()
        logger.info(f'All alive sheep have moved!')

        wolf.move(alive_herd)















