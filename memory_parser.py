#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time
import models
from utils import follow_module_ptr, MemoryFollowError
import json
import os


def dump_obj(obj, name):
    obj.print_tree()
    # with open(f'{name}-{str(int(time() * 1000))}.json', 'w') as log_json_file:
    #     json.dump({name: obj.serialize()}, log_json_file, indent=2)


def parse_is_playing(pm, useful_data):
    try:
        ptr = follow_module_ptr(pm, 'TrickyTowers.exe', 0x01010BD0, 0x8)
        useful_data['game_info']['is_playing'] = pm.read_short(ptr) == 1
    except (MemoryFollowError, AttributeError) as e:
        print(f'[!] Cannot get is_playing = {e}')
        useful_data['game_info']['is_playing'] = False


def parse_is_finished(pm, useful_data):
    try:
        ptr = follow_module_ptr(pm, 'TrickyTowers.exe', 0x010494D8, 0x1C,
                                0x59C, 0x214, 0x48, 0x228)
        useful_data['game_info']['is_finished'] = pm.read_short(ptr) == 1
    except (MemoryFollowError, AttributeError) as e:
        print(f'[!] Cannot get is_finished = {e}')
        useful_data['game_info']['is_finished'] = False


def get_game_state_controller(pm):
    try:
        ptr = follow_module_ptr(pm, 'mono.dll', 0x1F6964, 0x3A0, 0x6A8, 0xC,
                                0x14, 0x28, 0x0)
        return models.GameStateController(pm, ptr)
    except (MemoryFollowError, AttributeError) as e:
        print(f'[!] Cannot get GameStateController = {e}')
        return None


def get_user_manager(pm):
    try:
        ptr = follow_module_ptr(pm, 'mono.dll', 0x1F40AC, 0x1B4, 0x0)
        return models.UserManager(pm, ptr)
    except (MemoryFollowError, AttributeError) as e:
        print(f'[!] Cannot get UserManager = {e}')
        return None


def get_game_info_popup(pm):
    try:
        ptr = follow_module_ptr(pm, 'mono.dll', 0x1F40AC, 0x1B4, 0x10, 0x2C,
                                0x48, 0x20, 0xAC, 0x0)
        return models.GameInfoPopup(pm, ptr)
    except (MemoryFollowError, AttributeError) as e:
        print(f'[!] Cannot get GameInfoPopup = {e}')
        return None


def parse_game_state_controller(pm, useful_data):
    game_state_controller = get_game_state_controller(pm)
    # dump_obj(game_state_controller, 'game_state_controller')

    try:
        game_mode = game_state_controller._gameSetup.gameMode
        if game_mode and game_mode.is_initialized():
            game_mode_id = game_mode.id
            if game_mode_id and game_mode_id.is_initialized():
                useful_data['game_info']['game_mode'] = game_mode_id.value
    except (TypeError, AttributeError):
        pass
    finally:
        if 'game_mode' not in useful_data['game_info']:
            print(f'[?] game_info.game_mode is not defined')
            useful_data['game_info']['game_mode'] = None

    try:
        game_type = game_state_controller._gameSetup.gameType
        if game_type:
            useful_data['game_info']['game_type'] = game_type.type.value
    except (TypeError, AttributeError):
        pass
    finally:
        if 'game_type' not in useful_data['game_info']:
            print(f'[?] game_info.game_type is not defined')
            useful_data['game_info']['game_type'] = None

    try:
        game_type_flow = game_state_controller._gameSetup.gameTypeFlow
        # dump_obj(game_type_flow, 'game_type_flow')
        useful_data['temp']['game_type_flow'] = game_type_flow
    except (TypeError, AttributeError):
        pass
    finally:
        if 'game_type_flow' not in useful_data['temp']:
            useful_data['temp']['game_type_flow'] = None


def parse_user_manager(pm, useful_data):
    # Not used
    # user_manager = get_user_manager(pm)
    # dump_obj(user_manager, 'user_manager')
    pass


def parse_game_info_popup(pm, useful_data):
    game_info_popup = get_game_info_popup(pm)
    # dump_obj(game_info_popup, 'game_info_popup')

    if game_info_popup is None:
        # print(f'[?] game_info_popup(temp) is not defined')
        pass
    useful_data['temp']['game_info_popup'] = game_info_popup


def parse_net_player_startups(useful_data, net_player_startups):
    if net_player_startups is None:
        print(f'[?] players is not defined')
        return
    for i in range(net_player_startups.length):
        net_player_startup = net_player_startups.get(i)
        player = {}
        try:
            player['username'] = net_player_startup.username.value.encode(
                'utf8', 'replace').decode()
        except (TypeError, AttributeError):
            pass
        finally:
            if 'username' not in player:
                print(f'[?] players[{i}].username is not defined')
                player['username'] = None

        try:
            player['id'] = net_player_startup.id.value
        except (TypeError, AttributeError):
            pass
        finally:
            if 'id' not in player:
                print(f'[?] players[{i}].id is not defined')
                player['id'] = None

        try:
            player['steam_id'] = str(net_player_startup.steamId)
        except (TypeError, AttributeError):
            pass
        finally:
            if 'steam_id' not in player:
                print(f'[?] players[{i}].steam_id is not defined')
                player['steam_id'] = None

        try:
            player['elo'] = net_player_startup.eloScore
        except (TypeError, AttributeError):
            pass
        finally:
            if 'elo' not in player:
                print(f'[?] players[{i}].elo is not defined')
                player['elo'] = None

        try:
            player['is_online'] = net_player_startup.netPlayer.is_initialized()
        except (TypeError, AttributeError):
            pass
        finally:
            if 'is_online' not in player:
                print(f'[?] players[{i}].is_online is not defined')
                player['is_online'] = None

        useful_data['players'].append(player)


def parse_results_by_player(useful_data, results_by_player):
    results_by_player_dict = results_by_player.serialize()
    for player in useful_data['players']:
        if not player['id'] in results_by_player_dict:
            continue
        results = results_by_player_dict[player['id']]
        medals = [4 - result['rank'] for result in results]
        player['medals'] = medals
        player['total_score'] = sum(medals)


def parse(pm):
    print(f'\n--- Parse at {int(time() * 1000)} ---')
    useful_data = {'game_info': {}, 'players': [], 'temp': {}}

    parse_is_playing(pm, useful_data)
    parse_is_finished(pm, useful_data)
    parse_game_state_controller(pm, useful_data)
    parse_user_manager(pm, useful_data)
    parse_game_info_popup(pm, useful_data)

    game_type_flow = useful_data['temp']['game_type_flow']
    game_info_popup = useful_data['temp']['game_info_popup']

    # get cup type
    cup_type = None
    try:
        if isinstance(game_type_flow, models.CupMatchFlowController):
            cup_type = game_type_flow._cupType.value
        elif isinstance(game_info_popup, models.GameInfoPopup):
            cup_type = 'QUICK_MATCH'
    except (TypeError, AttributeError):
        pass
    finally:
        if cup_type is None:
            print(f'[?] game_info.cup_type is not defined')
    useful_data['game_info']['cup_type'] = cup_type

    # get basic player info
    try:
        if cup_type is None:
            print(f'[?] players is not defined')
        elif cup_type == 'QUICK_MATCH':
            parse_net_player_startups(useful_data, game_info_popup._netPlayers)
        else:
            parse_net_player_startups(useful_data,
                                      game_type_flow._netPlayersStartup)
    except (TypeError, AttributeError):
        print(f'[?] players is not defined')

    # get player score and target score
    if cup_type is not None and cup_type != 'QUICK_MATCH':
        parse_results_by_player(useful_data, game_type_flow._resultsByPlayer)

        try:
            useful_data['game_info'][
                'target_score'] = game_type_flow._targetScore
        except (TypeError, AttributeError):
            pass
        finally:
            if 'target_score' not in useful_data['game_info']:
                print(f'[?] game_info.target_score is not defined')
                useful_data['game_info']['target_score'] = None

    del (useful_data['temp'])
    return useful_data
