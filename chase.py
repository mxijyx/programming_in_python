import configparser
import json
import csv
import os
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
    return sum((cor1 - cor2) ** 2 for cor1, cor2 in zip(point1, point2))


class UnitShift(Enum):
    UP = (0, 1)
    DOWN = (0, -1)
    RIGHT = (1, 0)
    LEFT = (-1, 0)


class Sheep:
    def __init__(self, index, position: tuple):
        self.index = index
        self.position = position
        self.alive = True
        self.step = SHEEP_STEP

    def move(self):
        shift = choice(list(UnitShift))
        logger.debug(f'Sheep {self.index + 1} moving {shift.name}')

        if shift in (UnitShift.UP, UnitShift.DOWN):
            self.position = (self.position[0], self.position[1] + shift.value[1] * self.step)
        elif shift in (UnitShift.RIGHT, UnitShift.LEFT):
            self.position = (self.position[0] + shift.value[0] * self.step, self.position[1])

        logger.debug(f'Sheep {self.index + 1} moved to ({self.position[0]:.3f}, {self.position[1]:.3f})')


class Wolf:
    def __init__(self, position: tuple):
        self.position = position
        self.prey = None
        self.step = WOLF_STEP

    def move(self, herd: list['Sheep']):
        logger.info('Wolf is chasing!')

        herd = [s for s in herd if s.alive]

        self.prey = herd[0]
        for sheep in herd[1:]:
            if euclidean_distance2(self.position, sheep.position) < euclidean_distance2(self.position,
                                                                                        self.prey.position):
                self.prey = sheep
        logger.debug('Wolf prey is sheep number %d', self.prey.index + 1)

        distance = sqrt(euclidean_distance2(self.position, self.prey.position))
        logger.debug(f'The distance from the wolf to the sheep is {distance:.3f}')

        if distance <= self.step:
            self.position = self.prey.position
            self.prey.alive = False
            logger.info(
                f'Wolf has moved to a position ({self.position[0]:.3f}, {self.position[1]:.3f}) and eaten a sheep {self.prey.index + 1}')
        else:
            move_vector = self.prey.position[0] - self.position[0], self.prey.position[1] - self.position[1]
            logger.debug(f'Wolf will be moved in a direction of ({move_vector[0]:.3f}, {move_vector[1]:.3f}) vector')

            dist_to_sheep = hypot(*move_vector)

            x = move_vector[0] / dist_to_sheep
            x *= self.step
            y = move_vector[1] / dist_to_sheep
            y *= self.step

            self.position = (self.position[0] + x, self.position[1] + y)

            logger.info(f'Wolf is still chasing! The pray {self.prey.index + 1} stays alive!')
        logger.debug(f'Wolf moved to position ({self.position[0]:.3f}, {self.position[1]:.3f})')


if __name__ == '__main__':
    max_rounds = MAX_ROUNDS
    sheep_number = SHEEP_NUMBER
    position_limit = POSITION_LIMIT
    sheep_step = SHEEP_STEP
    wolf_step = WOLF_STEP

    arg_parser = ArgumentParser(
        prog='Chasing Sheep',
        description='Simulator of a wolf chasing a herd of sheep'
    )

    arg_parser.add_argument('-c', '--config', type=str, help='Load configuration from .ini file')
    arg_parser.add_argument('-l', '--log', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                            help='Logging level')
    arg_parser.add_argument('-r', '--rounds', type=int, default=MAX_ROUNDS, help='Number of sheep rounds')
    arg_parser.add_argument('-s', '--sheep', type=int, default=SHEEP_NUMBER, help='Sheep number')
    arg_parser.add_argument('-w', '--wait', action='store_true', help='Wait until sheep moved for a set time')

    args = arg_parser.parse_args()

    if args.log:
        logging.basicConfig(filename='chase.log', level=getattr(logging, args.log.upper()))
    else:
        logging.disable()

    if args.rounds:
        if args.rounds <= 0:
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

            position_limit = config.getfloat('Sheep', "InitPosLimit")
            if position_limit <= 0: raise ValueError('Position limit must be positive')

            sheep_step = config.getfloat('Sheep', 'MoveDist')
            if sheep_step <= 0: raise ValueError('Sheep step must be positive')

            wolf_step = config.getfloat('Wolf', 'MoveDist')
            if wolf_step <= 0: raise ValueError('Wolf step must be positive')

            logger.debug(
                f'.ini configuration file loaded with position {position_limit}, sheep step {sheep_step}, wolf step {wolf_step}')
        else:
            raise FileNotFoundError('Configuration file not found')

    Sheep.step = sheep_step
    Wolf.step = wolf_step

    herd = []
    for i in range(sheep_number):
        x = uniform(-position_limit, position_limit)
        y = uniform(-position_limit, position_limit)
        sheep = Sheep(i, (x, y))
        logger.debug(
            f'Sheep number {sheep.index + 1} initialized on position ({sheep.position[0]:.3f}, {sheep.position[1]:.3f})')
        herd.append(sheep)

    logger.info('\nHerd is ready for the game!')

    wolf = Wolf((0, 0))

    results = []
    alive_after_r = []

    for r in range(1, max_rounds + 1):
        alive_herd = [s for s in herd if s.alive]
        logger.info(f'Round {r} started!')
        print('--------------\nNew round started! Get ready!')
        #input('\nPress enter to continue...')
        print('Round: ', r, ' Alive sheep: ', len(alive_herd))

        for sheep in alive_herd:
            sheep.move()
        logger.info(f'All alive sheep have moved!')

        print(f'Initial wolf position: ({wolf.position[0]:.3f}, {wolf.position[1]:.3f})')

        wolf.move(alive_herd)

        print(f'Wolf moved to position: ({wolf.position[0]:.3f}, {wolf.position[1]:.3f})')
        if wolf.prey and not wolf.prey.alive:
            print(f'Sheep {wolf.prey.index + 1} was hunted and eaten by the wolf!')
        elif wolf.prey and wolf.prey.alive:
            print(
                f'Wolf is chasing sheep {wolf.prey.index + 1}, which is on the position: ({wolf.prey.position[0]:.3f}, {wolf.prey.position[1]:.3f})')
            print(f'Sheep {wolf.prey.index + 1} has escaped the wolf!')
        alive_herd = [s for s in herd if s.alive]

        results.append(
            {
                'round no': r,
                'wolf_pos': wolf.position,
                'sheep_pos': [s.position if s.alive else None for s in herd]
            }
        )
        alive_after_r.append(len(alive_herd))
        logger.info(f'At the end of the round {r} we have {len(alive_herd)} alive sheep')

        if not alive_herd:
            logger.info('No more alive sheep! Simulation terminated!')
            break
        if args.wait:
            input('Press Enter to continue...')

    else:
        logger.info(f'Simulation terminated after max rounds - {max_rounds} rounds!')

    print('\n---GAME OVER---')

    json_file = 'pos.json'

    with open(json_file, 'w') as f:
        json.dump(results, f, indent=4)
    logger.debug(f'Information was saved to location {os.path.abspath(json_file)}')

    csv_file = 'alive.csv'
    with open(csv_file, 'w') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerow(['Round Number', 'Number of alive sheep'])
        writer.writerows((r + 1, count) for r, count in enumerate(alive_after_r))
    logger.debug(f'Information was saved to location {os.path.abspath(csv_file)}')
