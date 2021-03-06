import pyaudio
import numpy as np
import matplotlib.pyplot as plt

from math import log2, pow

import musicalbeeps

import sf2_loader as sf
import time

flute_font = r'synths/Milton_Pan_flute.SF2'
sax_font = r'synths/AltoSoft_Vib.sf2'

loader = sf.sf2_loader(sax_font)
loader.load(sax_font)

A4 = 440
C0 = A4*pow(2, -4.75)
name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

player = musicalbeeps.Player(volume = 0.3,
                            mute_output = False)

np.set_printoptions(suppress=True) # don't use scientific notation

CHUNK = 22050 # number of data points to read at a time
RATE = 44100 # time resolution of the recording device (Hz)
VU_THRESH = 700 # minimum volume (vu) needed to trigger note detection

p=pyaudio.PyAudio() # start the PyAudio class
stream=p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True,
              frames_per_buffer=CHUNK) #uses default input device

last_note=""             

def pitch(freq):
    h = round(12*log2(freq/C0))
    octave = h // 12
    n = h % 12
    if octave < 1:
        octave = 1
    if len(name[n]) > 1:
        return name[n][0] + str(octave) + "#"

    return name[n] + str(octave)

# create a numpy array holding a single read of audio data
while True:
    data = np.frombuffer(stream.read(CHUNK),dtype=np.int16)
    data = data * np.hanning(len(data)) # smooth the FFT by windowing data
    fft = abs(np.fft.fft(data).real)
    fft = fft[:int(len(fft)/2)] # keep only first half
    freq = np.fft.fftfreq(CHUNK,1.0/RATE)
    freq = freq[:int(len(freq)/2)] # keep only first half
    freqPeak = freq[np.where(fft==np.max(fft))[0][0]]+1
    pitch_str = pitch(freqPeak)
    vu_peak = np.average(np.abs(data))*2
    # print("peak frequency: %d Hz, pitch: %s" % (freqPeak, pitch_str))
    if vu_peak > VU_THRESH:
        if last_note != pitch_str:
            print("peak frequency: %d Hz, Volume: %d VUs, pitch: %s" % (freqPeak, vu_peak, pitch_str))
            last_note=pitch_str
            loader.stop()
            loader.play_note(pitch_str, duration=10, volume=127) # play a note C5 for 3 seconds
            time.sleep(0.2)
            # player.play_note(pitch_str, 0.5)
    elif last_note != "":
        last_note = ""
        loader.stop()
        print("silence")

# close the stream gracefully
stream.stop_stream()
stream.close()
p.terminate()