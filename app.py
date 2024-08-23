from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import numpy as np
import librosa

app = Flask(__name__)
socketio = SocketIO(app)

chords = ['I', 'V', 'vi', 'IV']
key = 'C'  # Default key, will be updated
tempo = 60
chord_index = 0
acc_start_flag = False
tempo_key_flag = False

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_listening')
def handle_start_listening():
    global tempo, key
    print("Started listening")
    emit('listening_started', {'tempo': tempo, 'key': key})

@socketio.on('audio_data')
def handle_audio_data(data):
    global tempo, key
    audio_data = np.frombuffer(data['audio'], dtype=np.float32)
    detect_bpm_and_key(audio_data)
    print(f"Detected BPM: {tempo}, Key: {key}")
    emit('detection_result', {'tempo': tempo, 'key': key})

@socketio.on('request_chord')
def handle_chord_request(data):
    global chord_index, chords, key, acc_start_flag
    melody_note = data['melody_note']
    print("<< ", chord_index)

    if (chord_index == 0 and not acc_start_flag):
        acc_start_flag = True
        # Convert Roman numerals to actual chords based on the key
        actual_chords = [get_chord_from_roman(numeral, key) for numeral in chords]
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        melody_index = notes.index(melody_note)
        distances = [abs((notes.index(chord[0]) - melody_index) % 12) for chord in actual_chords]
        chord_index = distances.index(min(distances))

    current_chord = chords[chord_index]
    print(chord_index)
    chord_index = (chord_index + 1) % len(chords)
    print(f"Sending chord: {current_chord}, {chord_index}")
    emit('chord', {'chord': current_chord, 'key': key})

def detect_bpm_and_key(audio_data):
    global key, tempo
    sr = 22050  # Assume a sample rate of 22050 Hz

    # BPM detection
    detected_tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sr)
    detected_tempo = int(detected_tempo)

    # Chroma feature extraction for key detection
    chroma = librosa.feature.chroma_cqt(y=audio_data, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)
    key_idx = np.argmax(chroma_mean)
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    detected_key = keys[key_idx]

    # only update at the start for now:
    global tempo_key_flag
    #print(tempo_key_flag)
    if not tempo_key_flag:
        #tempo_key_flag = True
        tempo = detected_tempo
        key = detected_key

def get_chord_from_roman(numeral, key):
    roman_to_semitones = {'I': 0, 'II': 2, 'III': 4, 'IV': 5, 'V': 7, 'VI': 9, 'VII': 11}
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    key_index = keys.index(key)
    chord_index = (key_index + roman_to_semitones[numeral.upper()]) % 12
    return keys[chord_index]

if __name__ == '__main__':
    socketio.run(app, debug=True)
