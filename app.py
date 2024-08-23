from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

chords = ['I', 'V', 'vi', 'IV']
key = 'D'
tempo = 30
chord_index = 0

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_listening')
def handle_start_listening():
    global tempo, key
    print("Started listening")
    emit('listening_started', {'tempo': tempo, 'key': key})

@socketio.on('request_chord')
def handle_chord_request():
    global chord_index
    current_chord = chords[chord_index]
    chord_index = (chord_index + 1) % len(chords)
    print(f"Sending chord: {current_chord}")
    emit('chord', {'chord': current_chord})

if __name__ == '__main__':
    socketio.run(app, debug=True)
