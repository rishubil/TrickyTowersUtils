#!/usr/bin/env python
# -*- coding: utf-8 -*-

from io_utils import set_unbufferd
set_unbufferd()

from socketIO_client import SocketIO
from socketIO_client.exceptions import ConnectionError
from config import Config, CONFIG_FILE
from timeit import default_timer
from traceback import format_exc
from pymem import Pymem
from pymem.exception import MemoryReadError, ProcessNotFound, WinAPIError, ProcessError
from memory_parser import parse
from time import sleep
from sys import exit as _exit
from traceback import format_exc
from watchdog.observers import Observer as WatchdogObserver
from watchdog.events import PatternMatchingEventHandler
from os import stat

HOST = None
PORT = 0
DELAY = 0
DEBUG = False
config_updated = False


def load_config():
    global HOST, PORT, DELAY, DEBUG, config_updated
    config = Config()
    HOST = config.get('Observer', 'host')
    PORT = int(config.get('Observer', 'port'))
    DELAY = float(config.get('Observer', 'delay'))
    DEBUG = config.get('Observer', 'debug') == 'true'
    config_updated = True


def reload_config():
    load_config()
    try:
        with SocketIO(HOST, PORT, wait_for_connection=False) as socketIO:
            socketIO.emit('configUpdated', {})
    except ConnectionError as e:
        print(f'[!] TrickyTowersUtils Server is may not running')
        log(format_exc())


def log(text):
    if DEBUG:
        print(text)


class ConfigUpdateHandler(PatternMatchingEventHandler):
    prev_st_mtime = 0

    def __init__(self,
                 patterns=None,
                 ignore_patterns=None,
                 ignore_directories=False,
                 case_sensitive=False):
        super(ConfigUpdateHandler,
              self).__init__(patterns, ignore_patterns, ignore_directories,
                             case_sensitive)
        self.prev_st_mtime = 0

    def on_modified(self, event):
        st_mtime = stat(event.src_path).st_mtime
        if (st_mtime - self.prev_st_mtime) < 0.5:
            self.prev_st_mtime = st_mtime
            return
        self.prev_st_mtime = st_mtime
        try:
            # sleep(0.5)
            reload_config()
        except Exception as e:
            print(f'[!] Configuration is not reloaded. Try again.')
            return
        print(f'[-] Configuration is reloaded successfully.')


if __name__ == '__main__':
    print('Observer is running...')
    load_config()
    config_updated = False
    wo = WatchdogObserver()
    wcuh = ConfigUpdateHandler(patterns=['*.ini'], ignore_directories=True)
    wo.schedule(wcuh, path='.', recursive=False)
    wo.start()

    def teardown():
        wo.stop()
        wo.join()

    while True:
        sleep(DELAY)
        try:
            pass
            with SocketIO(HOST, PORT, wait_for_connection=False) as socketIO:
                pm = Pymem('TrickyTowers.exe')
                while True:
                    if config_updated:
                        config_updated = False
                        break
                    start = default_timer()
                    data = parse(pm)
                    socketIO.emit('json', data)
                    # _exit(0)

                    end = default_timer()

                    delayed = end - start
                    to_sleep = DELAY - delayed
                    if to_sleep > 0:
                        sleep(DELAY - delayed)
        except ConnectionError as e:
            print(f'[!] TrickyTowersUtils Server is may not running')
            log(format_exc())
        except MemoryReadError as e:
            print(f'[!] Tricky Towers is may not running: {repr(e)}')
            log(format_exc())
        except ProcessNotFound as e:
            print(f'[!] Tricky Towers is not running: {repr(e)}')
            log(format_exc())
        except WinAPIError as e:
            print(f'[!] Tricky Towers is may not running: {repr(e)}')
            log(format_exc())
        except ProcessError as e:
            print(f'[!] Tricky Towers is seems to opening now: {repr(e)}')
            log(format_exc())
        except KeyboardInterrupt as e:
            teardown()
            _exit(0)
    teardown()
