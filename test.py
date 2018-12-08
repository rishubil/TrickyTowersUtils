#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import pymem
import untangle
import pprint
from obswebsocket import obsws, requests
import requests as rq

pymem.logger.disabled = True

DEBUG = False
DEBUG = True

DELAY = 0.2
MAX_COUNTUP = int(3.6 / DELAY)

scoreboard_countup = 0
_is_scoreboard_visible = False

memory_data = None

member_map = {}

ws = obsws('localhost', 4444, 'temptemp')


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


def obs_update_player(i):
    global ws, memory_data
    ws.call(
        requests.SetTextGDIPlusProperties(
            scene_name='Tricky Towers (Auto, in-game 4p)',
            source=f'player name {i + 1}',
            text=f' {get_username(memory_data["players"][i])}'))


def obs_show_scoreboard():
    global ws
    ws.call(
        requests.SetCurrentScene(
            scene_name=f'Tricky Towers (Auto, scoreboard)', ))


def obs_show_username():
    global ws, memory_data
    ws.call(
        requests.SetCurrentScene(
            scene_name=
            f'Tricky Towers (Auto, in-game {num_of_online_player()}p)', ))


def obs_show_lobby():
    global ws
    ws.call(
        requests.SetCurrentScene(scene_name=f'Tricky Towers (Auto, lobby)', ))


def get_username(steam_id):
    global member_map
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


def update_memory(data):
    log(f'[>] update_memory({pprint.pformat(data)})')
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

    is_playing = pm.read_short(is_playing_ptr) == 1
    is_finished = pm.read_short(is_finished_ptr) == 1
    num_of_online_player = pm.read_short(num_online_player_ptr)

    if not is_playing:
        game_type = None
    elif pm.read_short(num_race_base_ptr) > 0:
        game_type = 'race'
    # elif pm.read_short(num_survival_base_ptr) > 0:
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
            pm.read_longlong(player1_steamid_ptr),
            pm.read_longlong(player2_steamid_ptr),
            pm.read_longlong(player3_steamid_ptr),
            pm.read_longlong(player4_steamid_ptr),
        ]
    }


if __name__ == '__main__':
    ws.connect()
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
            print('[!] Tricky Towers is may not running')
        except pymem.exception.ProcessNotFound as e:
            print('[!] Tricky Towers is not running')
        except pymem.exception.WinAPIError as e:
            print('[!] Tricky Towers is may not running')
        except pymem.exception.ProcessError as e:
            print('[!] Tricky Towers is seems to opening now')
