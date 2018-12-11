#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import pymem
import models

pymem.logger.disabled = True


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


if __name__ == '__main__':
    pm = pymem.Pymem('TrickyTowers.exe')
    # um_ptr = follow_module_ptr(pm, 'mono.dll', 0x1F40AC, 0x1B4, 0x0)
    # um = models.UserManager(pm, um_ptr)
    # um.print_tree()
    # users = um._implementation._users
    # while True:
    #     time.sleep(1)
    #     print('---')
    #     for i in range(users._size):
    #         user = users.get(i)
    #         print(f'{i}: {user.gameStats.towerHeight.value}')

    # models.GameSetupData(pm, 0x0585E460).print_tree()
    # models.GameSetupData(pm, 0x0585E3C0).print_tree()

    gsc_ptr = follow_module_ptr(pm, 'mono.dll', 0x1F6964, 0x3A0, 0x6A8, 0xC, 0x14, 0x28, 0x0)
    gsc = models.GameStateController(pm, gsc_ptr)
    gsc.print_tree()

    # GameSetupData에 gameTypeFlow중 CupMatchFlowController 에서 player 정보를 얻을 수 있을 것으로 추측됨
    # GameSetupData가 매 매치? 마다 생성되는 것 같은데... 어디서 생성하는건지?
