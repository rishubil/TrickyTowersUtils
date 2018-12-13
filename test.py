#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import pymem
import models
import utils
import timeit
import json
import os
from pprint import pprint

pymem.logger.disabled = True

DEBUG = True
DELAY = 0.5


def log(text):
    if DEBUG:
        print(text)


def dump_obj(obj, name):
    # obj.print_tree()
    with open(f'{name}-{str(int(time.time()))}.json', 'w') as log_json_file:
        json.dump({name: obj.serialize()}, log_json_file, indent=2)


def try_get_value(obj, *args):
    target = obj
    for path in args:
        if not hasattr(target, path):
            print(f'[?] target {target} does not have attr {path}')
            return None
        target = getattr(target, path)
    return target


def main(pm):
    os.system('cls')
    game_state_controller_ptr = utils.follow_module_ptr(
        pm, 'mono.dll', 0x1F6964, 0x3A0, 0x6A8, 0xC, 0x14, 0x28, 0x0)

    user_manager_ptr = utils.follow_module_ptr(pm, 'mono.dll', 0x1F40AC, 0x1B4,
                                               0x0)

    useful_data = {}

    game_state_controller = models.GameStateController(
        pm, game_state_controller_ptr)
    user_manager = models.UserManager(pm, user_manager_ptr)

    # dump_obj(game_state_controller, 'GameStateController')
    # dump_obj(user_manager, 'UserManager')

    game_stats = try_get_value(user_manager, '_implementation', '_currentUser',
                               'gameStats')
    useful_data['finished'] = game_stats.finished.value

    game_type_flow = try_get_value(game_state_controller, '_gameSetup',
                                   'gameTypeFlow')
    game_type = try_get_value(game_state_controller, '_gameSetup', 'gameType')
    useful_data['game_type'] = game_type.type.value
    if not isinstance(game_type_flow, models.CupMatchFlowController):
        print(f'[-] You are not in a Cup')
        return

    cup_type = try_get_value(game_type_flow, '_cupType')
    useful_data['cup_type'] = cup_type.value

    net_player_startups = try_get_value(game_type_flow, '_netPlayersStartup')

    if net_player_startups:
        useful_data['players'] = []
        for i in range(net_player_startups.length):
            useful_data['players'].append({})
            net_player_startup = net_player_startups.get(i)
            username = try_get_value(net_player_startup, 'username')
            if username.value:
                printable_username = username.value.encode('utf8',
                                                           'replace').decode()
            useful_data['players'][i]['username'] = printable_username

            _id = try_get_value(net_player_startup, 'id')
            useful_data['players'][i]['id'] = _id.value

            steam_id = try_get_value(net_player_startup, 'steamId')
            useful_data['players'][i]['steam_id'] = steam_id

            elo = try_get_value(net_player_startup, 'eloScore')
            useful_data['players'][i]['elo'] = elo

            # game_stats = try_get_value(net_player_startup, 'netPlayer', '_user', 'gameStats')
            # useful_data['players'][i]['game_stats'] = game_stats

    results_by_player = try_get_value(game_type_flow, '_resultsByPlayer')

    if results_by_player:
        results_by_player_dict = results_by_player.serialize()
        for player in useful_data['players']:
            if not player['id'] in results_by_player_dict:
                continue
            results = results_by_player_dict[player['id']]
            medals = [4 - result['rank'] for result in results]
            player['medals'] = medals
            player['total_score'] = sum(medals)

    target_score = try_get_value(game_type_flow, '_targetScore')
    useful_data['target_score'] = target_score

    game_mode = try_get_value(game_state_controller, '_gameSetup', 'gameMode',
                              'id')
    useful_data['game_mode'] = game_mode.value

    pprint(useful_data)


if __name__ == '__main__':
    # pm = pymem.Pymem('TrickyTowers.exe')
    # main(pm)
    while True:
        pm = pymem.Pymem('TrickyTowers.exe')
        time.sleep(DELAY)
        while True:
            start = timeit.default_timer()
            main(pm)
            end = timeit.default_timer()
            delayed = end - start
            print(f'delay: {delayed}')
            time.sleep(DELAY - delayed)
