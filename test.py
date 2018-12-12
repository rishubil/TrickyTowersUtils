#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import pymem
import models
import utils

pymem.logger.disabled = True

if __name__ == '__main__':
    pm = pymem.Pymem('TrickyTowers.exe')
    base_ptr = utils.get_base_addr(pm, 'mono.dll')
    gsc_ptr = utils.follow_module_ptr(pm, 'mono.dll', 0x1F6964, 0x3A0, 0x6A8,
                                      0xC, 0x14, 0x28, 0x0)
    gsc = models.GameStateController(pm, gsc_ptr)
    gsc.print_tree()

    # TournamentResultsPopup에서 경기 결과 얻어올 수 있는지 확인할 것
