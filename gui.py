#!/usr/bin/env python
# -*- coding: utf-8 -*-
import atexit
import tkinter as tk
from tkinter import scrolledtext
import subprocess
from queue import Queue
from queue import Empty as QueueEmpty
from threading import Thread
from pathlib import Path
from ctypes import wintypes, windll, byref, WinError, GetLastError
import msvcrt
import sys
import os
import time

IS_FROZEN = getattr(sys, 'frozen', False)

PIPE_NOWAIT = wintypes.DWORD(0x00000001)
ERROR_NO_DATA = 232

PROCESS_STATE_START = 'START'
PROCESS_STATE_STOP = 'STOP'


# https://gist.github.com/techtonik/48c2561f38f729a15b7b
def pipe_no_wait(pipefd):
    """ pipefd is a integer as returned by os.pipe """

    SetNamedPipeHandleState = windll.kernel32.SetNamedPipeHandleState
    SetNamedPipeHandleState.argtypes = [
        wintypes.HANDLE, wintypes.LPDWORD, wintypes.LPDWORD, wintypes.LPDWORD
    ]
    SetNamedPipeHandleState.restype = wintypes.BOOL

    h = msvcrt.get_osfhandle(pipefd)

    res = windll.kernel32.SetNamedPipeHandleState(h, byref(PIPE_NOWAIT), None,
                                                  None)
    if res == 0:
        raise WinError()
        return False
    return True


class AutoScrolledText(scrolledtext.ScrolledText):
    def __init__(self, master, queue, **options):
        scrolledtext.ScrolledText.__init__(self, master, **options)
        self.queue = queue
        self.update_text()

    def append_text(self, text):
        self.queue.put(text)

    def clear_text(self):
        self.queue.put(None)

    def update_text(self):
        try:
            while True:
                line = self.queue.get_nowait()
                if line is None:
                    self.configure(state=tk.NORMAL)
                    self.delete(1.0, tk.END)
                    self.configure(state=tk.DISABLED)
                    self.see(tk.END)
                else:
                    need_autoscroll = self.yview()[1] >= 1.0
                    self.configure(state=tk.NORMAL)
                    self.insert(tk.END, str(line))
                    self.configure(state=tk.DISABLED)
                    if need_autoscroll:
                        self.see(tk.END)
                self.update_idletasks()
        except QueueEmpty:
            pass
        self.after(10, self.update_text)


class MainFrame(tk.Frame):
    def __init__(self, master, queue_map):
        tk.Frame.__init__(self, master)
        self.master = master
        self.queue_map = queue_map
        self.init_menu()
        self.init_view()

    def init_menu(self):
        self.menu_option = tk.Menu(self.master)
        self.submenu_option = tk.Menu(self.menu_option, tearoff=0)
        self.submenu_option.add_command(
            label='Open config.ini', command=self.open_config)
        self.menu_option.add_cascade(label='Options', menu=self.submenu_option)
        self.master.config(menu=self.menu_option)

    def init_view(self):
        self.server_top_frame = tk.Frame(self)
        self.server_top_frame.pack(fill=tk.BOTH, padx=8, pady=(8, 0))
        self.server_label = tk.Label(self.server_top_frame, text='Server log:')
        self.server_label.pack(side=tk.LEFT)

        self.server_stop_button = tk.Button(
            self.server_top_frame,
            text="Stop server",
            command=self.stop_server)
        self.server_stop_button.pack(side=tk.RIGHT, padx=8)

        self.server_start_button = tk.Button(
            self.server_top_frame,
            text="Start server",
            command=self.start_server)
        self.server_start_button.pack(side=tk.RIGHT)

        self.server_log = AutoScrolledText(
            self,
            self.queue_map['server_log'],
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED)
        self.server_log.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 0))

        self.observer_top_frame = tk.Frame(self)
        self.observer_top_frame.pack(fill=tk.BOTH, padx=8, pady=(8, 0))
        self.observer_label = tk.Label(
            self.observer_top_frame, text='Observer log:')
        self.observer_label.pack(side=tk.LEFT)

        self.observer_stop_button = tk.Button(
            self.observer_top_frame,
            text="Stop observer",
            command=self.stop_observer)
        self.observer_stop_button.pack(side=tk.RIGHT, padx=8)

        self.observer_start_button = tk.Button(
            self.observer_top_frame,
            text="Start observer",
            command=self.start_observer)
        self.observer_start_button.pack(side=tk.RIGHT)

        self.observer_log = AutoScrolledText(
            self,
            self.queue_map['observer_log'],
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED)
        self.observer_log.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def start_server(self):
        self.queue_map['server_process'].put(PROCESS_STATE_START)

    def stop_server(self):
        self.queue_map['server_process'].put(PROCESS_STATE_STOP)

    def start_observer(self):
        self.queue_map['observer_process'].put(PROCESS_STATE_START)

    def stop_observer(self):
        self.queue_map['observer_process'].put(PROCESS_STATE_STOP)

    def open_config(self):
        config_path = Path('config.ini').resolve()
        if not config_path.is_file():
            config_path.touch()
        subprocess.Popen(['start', str(config_path)], shell=True)


def start_tk(queue_map):
    root = tk.Tk()
    root.geometry('800x600+0+0')
    root.title('TrickyTowersUtils')
    app = MainFrame(root, queue_map)
    app.pack(fill=tk.BOTH, expand=True)
    root.update()
    root.minsize(width=300, height=400)
    root.mainloop()


def process_task(queue_map, process_name):
    if IS_FROZEN:
        cmd = f'{process_name}.exe'
    else:
        cmd = f'python {process_name}.py'

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    state = PROCESS_STATE_STOP
    process = None

    while True:
        command = None
        try:
            command = queue_map[f'{process_name}_process'].get_nowait()
        except QueueEmpty:
            pass

        if command == PROCESS_STATE_START and state == PROCESS_STATE_STOP:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                close_fds=False,
                bufsize=1,
                universal_newlines=True,
                startupinfo=startupinfo)
            pipe_no_wait(process.stdout.fileno())
            state = PROCESS_STATE_START

        if state == PROCESS_STATE_START:
            while True:
                try:
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break
                        queue_map[f'{process_name}_log'].put(line)
                except OSError:
                    if GetLastError() == ERROR_NO_DATA:
                        break
                    raise
                if process.poll() is not None:
                    queue_map[f'{process_name}_process'].put(
                        PROCESS_STATE_STOP)
                    break

        if command == PROCESS_STATE_STOP and state == PROCESS_STATE_START:
            # process.kill()
            subprocess.call(['taskkill', '/F', '/T', '/PID',
                             str(process.pid)],
                            startupinfo=startupinfo)
            process = None
            state = PROCESS_STATE_STOP
            queue_map[f'{process_name}_log'].put('Successfully stopped.\n')

        time.sleep(0.1)


def cleanup(queue_map):
    queue_map['server_process'].put(PROCESS_STATE_STOP)
    queue_map['observer_process'].put(PROCESS_STATE_STOP)
    time.sleep(1)  # wait for kill processes


def main():
    queue_map = {
        'server_log': Queue(),
        'observer_log': Queue(),
        'server_process': Queue(),
        'observer_process': Queue()
    }

    server_thread = Thread(target=process_task, args=(queue_map, 'server'))
    server_thread.daemon = True
    server_thread.start()

    observer_thread = Thread(target=process_task, args=(queue_map, 'observer'))
    observer_thread.daemon = True
    observer_thread.start()

    atexit.register(cleanup, queue_map)

    start_tk(queue_map)


if __name__ == '__main__':
    main()
