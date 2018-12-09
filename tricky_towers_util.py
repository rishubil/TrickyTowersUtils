#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import pymem
import untangle
import pprint
import traceback
from obswebsocket import obsws, requests
import requests as rq
import configparser

pymem.logger.disabled = True

DEBUG = False
DELAY = 0.1
MAX_COUNTUP = int(3 / DELAY)

scoreboard_countup = 0
_is_scoreboard_visible = False
memory_data = None
member_map = {}
ws = None
config = configparser.ConfigParser()


def log(text):
    if DEBUG:
        print(text)


def num_of_online_player():
    global memory_data
    return memory_data['num_of_online_player']


def is_online():
    return num_of_online_player() > 0


def is_playing():
    global memory_data
    return memory_data['is_playing']


def is_finished():
    global memory_data
    return memory_data['is_finished']


def is_scoreboard_visible():
    global _is_scoreboard_visible
    return _is_scoreboard_visible


def get_obs_config(name):
    global config
    return config['OBS'][name]


def get_scene_config(name):
    global config
    return config['SCENE'][name]


def get_text_config(name):
    global config
    return config['TEXT'][name]


def obs_update_player(i):
    global ws, memory_data
    ws.call(
        requests.SetTextGDIPlusProperties(
            scene_name=get_scene_config('play').format(number=4),
            source=get_text_config('player').format(number=i + 1),
            text=f' {get_username(memory_data["players"][i])}'))


def obs_show_scoreboard():
    global ws
    ws.call(
        requests.SetCurrentScene(scene_name=get_scene_config('scoreboard'), ))


def obs_show_username():
    global ws, memory_data
    ws.call(
        requests.SetCurrentScene(
            scene_name=get_scene_config('play').format(
                number=num_of_online_player()), ))


def obs_show_lobby():
    global ws
    ws.call(requests.SetCurrentScene(scene_name=get_scene_config('lobby'), ))


def get_username(steam_id):
    global member_map
    if steam_id <= 0:
        return ''
    if steam_id not in member_map:
        user_xml = rq.get(
            f'https://steamcommunity.com/profiles/{steam_id}/?xml=1').text
        user_info = untangle.parse(user_xml)
        member_map[steam_id] = user_info.profile.steamID.cdata
    return member_map[steam_id]


def request_update_member():
    try:
        if is_online() and (is_scoreboard_visible() or not is_playing()):
            for i in range(num_of_online_player()):
                obs_update_player(i)
    except Exception as e:
        log(f'[!] {repr(e)}')
        log(traceback.format_exc())


def request_chnage_scene():
    try:
        if is_online() and is_playing():
            if is_finished() and is_scoreboard_visible():
                obs_show_scoreboard()
            else:
                obs_show_username()
        else:
            obs_show_lobby()
    except Exception as e:
        log(f'[!] {repr(e)}')
        log(traceback.format_exc())


def check_scoreboard():
    global _is_scoreboard_visible, scoreboard_countup
    # log(f'[>] check_scoreboard({_is_scoreboard_visible}, {scoreboard_countup})')
    if not is_finished():
        _is_scoreboard_visible = False
        scoreboard_countup = 0
        request_chnage_scene()
        return
    if is_scoreboard_visible():
        return
    if scoreboard_countup < MAX_COUNTUP:
        scoreboard_countup += 1
        return
    scoreboard_countup = 0
    _is_scoreboard_visible = True
    request_chnage_scene()


def print_memory(data):
    print('---')
    print(f'게임 타입: {data["game_type"]}')
    print(f'현재 게임상태: {"게임중" if data["is_playing"] else "게임중이 아님"}')
    print(f'레벨 상태: {"종료됨" if data["is_finished"] else "종료되지 않음"}')
    print(f'온라인 플레이: {"예" if data["num_of_online_player"] > 0 else "아니오"}')
    print(f'온라인 플레이어 수: {data["num_of_online_player"]}')
    print(
        f'플레이어명: {[get_username(data["players"][x]) for x in range(data["num_of_online_player"])]}'
    )


def update_memory(data):
    log(f'[>] update_memory({pprint.pformat(data)})')
    print_memory(data)
    request_chnage_scene()
    request_update_member()


def get_base_addr(pm, name):
    return pymem.process.module_from_name(pm.process_handle, name).lpBaseOfDll


def follow_ptr(pm, *args):
    l = len(args)
    if l == 0:
        raise ValueError('You have to pass the address of memory')
    elif l == 1:
        return args[0]
    elif l == 2:
        return args[0] + args[1]
    ptr = pm.read_int(args[0] + args[1])
    return follow_ptr(pm, ptr, *(args[2:]))


def follow_module_ptr(pm, module_name, *args):
    return follow_ptr(pm, get_base_addr(pm, module_name), *args)


def read_short(pm, ptr):
    try:
        return pm.read_short(ptr)
    except pymem.exception.MemoryReadError as e:
        return -1


def read_longlong(pm, ptr):
    try:
        return pm.read_longlong(ptr)
    except pymem.exception.MemoryReadError as e:
        return -1


def get_memory_data(pm, base_address):
    fmp = lambda name, *args: follow_module_ptr(pm, name, *args)
    fmpt = lambda *args: fmp('TrickyTowers.exe', *args)
    fmpm = lambda *args: fmp('mono.dll', *args)

    is_playing_ptr = fmpt(0x01010BD0, 0x8)
    is_finished_ptr = fmpt(0x010494D8, 0x1C, 0x59C, 0x214, 0x48, 0x228)
    num_online_player_ptr = fmpm(0x001F40AC, 0x1A8, 0x24, 0x4C, 0xEC, 0xCC)
    num_race_base_ptr = fmpt(0x010494D8, 0x1C, 0x71C, 0x6F8, 0xC, 0x748)
    player1_steamid_ptr = fmpm(0x0020C574, 0x4, 0x8, 0x1E8, 0x24, 0x48)
    player2_steamid_ptr = fmpm(0x0020C574, 0x4, 0x8, 0x1E8, 0x24, 0x50)
    player3_steamid_ptr = fmpm(0x0020C574, 0x4, 0x8, 0x1E8, 0x24, 0x58)
    player4_steamid_ptr = fmpm(0x0020C574, 0x4, 0x8, 0x1E8, 0x24, 0x60)

    is_playing = read_short(pm, is_playing_ptr) == 1
    is_finished = read_short(pm, is_finished_ptr) == 1
    num_of_online_player = read_short(pm, num_online_player_ptr)

    if not is_playing:
        game_type = None
    elif read_short(pm, num_race_base_ptr) > 0:
        game_type = 'race'
    # elif read_short(pm, num_survival_base_ptr) > 0:
    #     game_type = 'survival'
    else:
        game_type = 'unknown'

    return {
        'is_playing':
        is_playing,
        'is_finished':
        is_finished,
        'num_of_online_player':
        num_of_online_player,
        'game_type':
        game_type,
        'players': [
            read_longlong(pm, player1_steamid_ptr),
            read_longlong(pm, player2_steamid_ptr),
            read_longlong(pm, player3_steamid_ptr),
            read_longlong(pm, player4_steamid_ptr),
        ]
    }


if __name__ == '__main__':
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
        ws = obsws(
            get_obs_config('host'), int(get_obs_config('port')),
            get_obs_config('password'))
    except Exception as e:
        print(f'[!] Cannot get configuration: {repr(e)}')
        log(traceback.format_exc())
        sys.exit(-1)

    try:
        ws.connect()
    except Exception as e:
        print(f'[!] Cannot connect to OBS: {repr(e)}')
        log(traceback.format_exc())
        sys.exit(-1)

    while True:
        time.sleep(DELAY)
        try:
            pm = pymem.Pymem('TrickyTowers.exe')
            base_address = pm.process_base.lpBaseOfDll
            while True:
                time.sleep(DELAY)
                local_memory_data = get_memory_data(
                    pm, pm.process_base.lpBaseOfDll)
                if local_memory_data != memory_data:
                    memory_data = local_memory_data
                    update_memory(memory_data)
                check_scoreboard()

        except pymem.exception.MemoryReadError as e:
            print(f'[!] Tricky Towers is may not running: {repr(e)}')
            log(traceback.format_exc())
        except pymem.exception.ProcessNotFound as e:
            print(f'[!] Tricky Towers is not running: {repr(e)}')
            log(traceback.format_exc())
        except pymem.exception.WinAPIError as e:
            print(f'[!] Tricky Towers is may not running: {repr(e)}')
            log(traceback.format_exc())
        except pymem.exception.ProcessError as e:
            print(f'[!] Tricky Towers is seems to opening now: {repr(e)}')
            log(traceback.format_exc())
        except KeyboardInterrupt as e:
            sys.exit(0)
