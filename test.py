#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tail
import re
import sys
import os
import time
import pymem
import untangle
from obswebsocket import obsws, requests

pymem.logger.disabled = True

DEBUG = False
DEBUG = True

STATE_NORMAL = 1
STATE_PARSING_LOBBY = 2
state = STATE_NORMAL

lobby_number_re = re.compile(r'^Lobby (\d+) updated:$', flags=re.MULTILINE)
lobby_member_re = re.compile(
    r'^\t(.*) \((\d+)\)(?: \[(SELF)\])?(?: \[(OWNER)\])?$', flags=re.MULTILINE)
lobby_attr_re = re.compile(r'^\t(.*): (.*)$', flags=re.MULTILINE)
level_id_re = re.compile(r'^levelId: (.*)$', flags=re.MULTILINE)

lobby_string = ''
lobby = None

level_id = None
should_chage_scoreboard = False

memory_data = None

ws = obsws('localhost', 4444, 'temptemp')


def log(text):
    if DEBUG:
        print(text)


def request_update_member():
    global ws, lobby
    try:
        if lobby and 'members' in lobby:
            for i, member in enumerate(lobby['members'], 1):
                ws.call(
                    requests.SetTextGDIPlusProperties(
                        scene_name='Tricky Towers (Auto, in-game 4p)',
                        source=f'player name {i}',
                        text=f' {member["name"]}'))
    except e:
        log(f'[!] {repr(e)}')


def request_chnage_scene():
    global ws, lobby, memory_data, should_chage_scoreboard
    try:
        if lobby and 'in_game' in lobby and lobby[
                'in_game'] == 'TRUE' and memory_data and 'is_playing' in memory_data and memory_data[
                    'is_playing']:
            if memory_data and 'is_finished' in memory_data and memory_data[
                    'is_finished'] and should_chage_scoreboard:
                should_chage_scoreboard = False
                ws.call(
                    requests.SetCurrentScene(
                        scene_name=
                        f'Tricky Towers (Auto, scoreboard)',
                    ))
            else:
                ws.call(
                    requests.SetCurrentScene(
                        scene_name=
                        f'Tricky Towers (Auto, in-game {len(lobby["members"])}p)',
                    ))
        else:
            should_chage_scoreboard = False
            ws.call(
                requests.SetCurrentScene(
                    scene_name=f'Tricky Towers (Auto, lobby)', ))
    except e:
        log(f'[!] {repr(e)}')


def update_memory(data):
    log(f'[>] update_memory({data})')
    request_chnage_scene()


def update_lobby(data):
    log(f'[>] update_lobby({data})')
    request_update_member()
    request_chnage_scene()


def update_level_id(data):
    log(f'[>] update_level_id({data})')
    global should_chage_scoreboard
    should_chage_scoreboard = True
    request_chnage_scene()


def detect_level_id(line):
    # log(f'[>] detect_level_id("{line.rstrip()}")')
    global level_id
    m = level_id_re.match(line)
    if not m:
        return False

    local_level_id = m.group(1)
    if local_level_id != level_id:
        level_id = local_level_id
        update_level_id(level_id)

    return True


def detect_lobby(line):
    # log(f'[>] detect_lobby("{line.rstrip()}")')
    global state, lobby_string
    m = lobby_number_re.match(line)
    if not m:
        return False
    state = STATE_PARSING_LOBBY
    lobby_string += line
    return True


def parse_lobby():
    # log(f'[>] parse_lobby()')
    global state, lobby_string, lobby

    lobby_number = lobby_number_re.findall(lobby_string)[0]
    lobby_members = lobby_member_re.findall(lobby_string)
    lobby_attrs = lobby_attr_re.findall(lobby_string)

    local_lobby = {
        'id':
        lobby_number,
        'members': [{
            'id': member[1],
            'name': member[0],
            'is_self': member[2] == 'SELF',
            'is_owner': member[2] == 'OWNER' or member[3] == 'OWNER',
        } for member in lobby_members]
    }
    for attr in lobby_attrs:
        local_lobby[attr[0].lower()] = attr[1]

    if local_lobby != lobby:
        lobby = local_lobby
        update_lobby(lobby)

    lobby_string = ''
    state = STATE_NORMAL


def read_lobby(line):
    # log(f'[>] read_lobby("{line.rstrip()}")')
    global lobby_string
    if line.strip():
        lobby_string += line
        return
    parse_lobby()


def parse_log(line):
    if state == STATE_NORMAL:
        if detect_lobby(line):
            return
        if detect_level_id(line):
            return
    elif state == STATE_PARSING_LOBBY:
        read_lobby(line)
        return


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
        'is_playing': is_playing,
        'is_finished': is_finished,
        'num_of_online_player': num_of_online_player,
        'game_type': game_type,
        'player1_steamid': pm.read_longlong(player1_steamid_ptr),
        'player2_steamid': pm.read_longlong(player2_steamid_ptr),
        'player3_steamid': pm.read_longlong(player3_steamid_ptr),
        'player4_steamid': pm.read_longlong(player4_steamid_ptr),
    }


if __name__ == '__main__':
    t = tail.Tail(
        'C:\Program Files (x86)\Steam\steamapps\common\Tricky Towers\TrickyTowers_Data\output_log.txt'
    )
    t.register_callback(parse_log)
    ws.connect()
    while True:
        time.sleep(0.2)
        with open(t.tailed_file, encoding='utf-8') as file_:
            # Go to the end of file
            file_.seek(0, 2)
            try:
                pm = pymem.Pymem('TrickyTowers.exe')
                base_address = pm.process_base.lpBaseOfDll
                while True:
                    local_memory_data = get_memory_data(
                        pm, pm.process_base.lpBaseOfDll)
                    if local_memory_data != memory_data:
                        memory_data = local_memory_data
                        update_memory(memory_data)

                    curr_position = file_.tell()
                    line = file_.readline()
                    if not line:
                        file_.seek(curr_position)
                        time.sleep(0.2)
                    else:
                        t.callback(line)

            except pymem.exception.MemoryReadError as e:
                print('[!] Tricky Towers is may not running')
            except pymem.exception.ProcessNotFound as e:
                print('[!] Tricky Towers is not running')
            except pymem.exception.WinAPIError as e:
                print('[!] Tricky Towers is may not running')
            except pymem.exception.ProcessError as e:
                print('[!] Tricky Towers is seems to opening now')
