#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from json import dumps
from os.path import join as pathjoin
import sys

from config import Config

config = Config()
DEBUG = config.get('Server', 'debug') == 'true'

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS  # pylint: disable=no-member
else:
    base_dir = '.'

app = Flask(
    __name__,
    static_url_path='',
    template_folder=pathjoin(base_dir, 'static', 'dist'),
    static_folder=pathjoin(base_dir, 'static', 'dist'))
app.config['SECRET_KEY'] = config.get('Server', 'secret_key')
app.config['TEMPLATES_AUTO_RELOAD'] = True
socketio = SocketIO(app, async_mode="gevent")


@app.route('/')
@app.route('/overlay')
def overlay():
    return render_template('index.html')


@app.route('/overlay_config.json')
def overlay_config():
    return jsonify(config=dict(Config().items('Overlay')))


@socketio.on('json')
def broadcast_json(message):
    if DEBUG:
        print('received message: ' + str(message))
    emit('json', message, json=True, broadcast=True)


@socketio.on('configUpdated')
def broadcast_config_updated(message):
    if DEBUG:
        print('received configUpdated')
    emit('configUpdated', message, json=True, broadcast=True)


if __name__ == '__main__':
    print('Server is running...')
    socketio.run(
        app,
        host=config.get('Server', 'host'),
        port=int(config.get('Server', 'port')))
