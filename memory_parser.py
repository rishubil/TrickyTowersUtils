#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time
import models
from utils import follow_module_ptr
import json
import os


def dump_obj(obj, name):
    # obj.print_tree()
    with open(f'{name}-{str(int(time()))}.json', 'w') as log_json_file:
        json.dump({name: obj.serialize()}, log_json_file, indent=2)


def try_get_value(obj, *args):
    target = obj
    for path in args:
        if not hasattr(target, path):
            print(f'[?] target {target} does not have attr {path}')
            return None
        target = getattr(target, path)
    return target


def parse(pm):
    useful_data = {}
    is_playing_ptr = follow_module_ptr(pm, 'TrickyTowers.exe', 0x01010BD0, 0x8)
    is_finished_ptr = follow_module_ptr(pm, 'TrickyTowers.exe', 0x010494D8, 0x1C, 0x59C, 0x214, 0x48, 0x228)

    game_state_controller_ptr = follow_module_ptr(
        pm, 'mono.dll', 0x1F6964, 0x3A0, 0x6A8, 0xC, 0x14, 0x28, 0x0)

    user_manager_ptr = follow_module_ptr(pm, 'mono.dll', 0x1F40AC, 0x1B4, 0x0)

    useful_data['is_playing'] = pm.read_short(is_playing_ptr) == 1
    useful_data['is_finished'] = pm.read_short(is_finished_ptr) == 1

    game_state_controller = models.GameStateController(
        pm, game_state_controller_ptr)
    user_manager = models.UserManager(pm, user_manager_ptr)

    game_mode = try_get_value(game_state_controller, '_gameSetup', 'gameMode',
                              'id')
    if game_mode:
        useful_data['game_mode'] = game_mode.value

    game_type = try_get_value(game_state_controller, '_gameSetup', 'gameType')
    if game_type:
        useful_data['game_type'] = game_type.type.value

    game_type_flow = try_get_value(game_state_controller, '_gameSetup',
                                   'gameTypeFlow')
                                
    if isinstance(game_type_flow, models.CupMatchFlowController):
        cup_type = try_get_value(game_type_flow, '_cupType')
        useful_data['cup_type'] = cup_type.value

        net_player_startups = try_get_value(game_type_flow,
                                            '_netPlayersStartup')

        if net_player_startups:
            useful_data['players'] = []
            for i in range(net_player_startups.length):
                useful_data['players'].append({})
                net_player_startup = net_player_startups.get(i)
                username = try_get_value(net_player_startup, 'username')
                if username.value:
                    printable_username = username.value.encode(
                        'utf8', 'replace').decode()
                useful_data['players'][i]['username'] = printable_username

                _id = try_get_value(net_player_startup, 'id')
                useful_data['players'][i]['id'] = _id.value

                steam_id = try_get_value(net_player_startup, 'steamId')
                useful_data['players'][i]['steam_id'] = steam_id

                elo = try_get_value(net_player_startup, 'eloScore')
                useful_data['players'][i]['elo'] = elo

                netPlayer = try_get_value(net_player_startup, 'netPlayer')
                useful_data['players'][i]['is_online'] = netPlayer.is_initialized()

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

    return useful_data
