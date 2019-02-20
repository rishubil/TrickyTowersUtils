from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from json import dumps

from config import Config

config = Config()

app = Flask(
    __name__,
    static_url_path='',
    template_folder='static/dist',
    static_folder='static/dist')
app.config['SECRET_KEY'] = config.get('Server', 'secret_key')
app.config['TEMPLATES_AUTO_RELOAD'] = True
socketio = SocketIO(app)


@app.route('/')
@app.route('/overlay')
def overlay():
    return render_template('index.html')


@app.route('/overlay_config.json')
def overlay_config():
    return jsonify(config=dict(config.items('Overlay')))


@socketio.on('json')
def broadcast(message):
    print('received message: ' + str(message))
    emit('json', message, json=True, broadcast=True)


if __name__ == '__main__':
    socketio.run(
        app,
        host=config.get('Server', 'host'),
        port=int(config.get('Server', 'port')))
