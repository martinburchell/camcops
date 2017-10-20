#!/usr/bin/python

# http://stackoverflow.com/questions/5173795/how-can-i-generate-a-note-or-chord-in-python  # noqa
# ... and me
# http://blogs.msdn.com/b/dawate/archive/2009/06/23/intro-to-audio-programming-part-2-demystifying-the-wav-format.aspx  # noqa
# ... for 16-bit WAV (sampwidth = 2), data range = -32760 to +32760

import math
import struct
from typing import List, Tuple
import wave

DEBUG = True


def synth_complex(freq_coefs: List[Tuple[float, float]] = None,
                  duration_s: float = 1.0,
                  fname: str = "test.wav",
                  frate_hz: float = 44100.00,
                  amp_proportion: float = 1.0) -> None:
    if freq_coefs is None:
        freq_coefs = [(440, 1)]  # type: List[Tuple[float, float]]
    sine_list = []
    datasize = int(frate_hz * duration_s)
    clipped = False
    for x in range(datasize):
        samp = 0
        for k in range(len(freq_coefs)):
            freq = freq_coefs[k][0]
            coef = freq_coefs[k][1]
            samp += coef * math.sin(2 * math.pi * freq * (x / frate_hz))
            # each component can contribute (+/- coef) to each sample
        if samp > 1 or samp < -1:
            clipped = True
        samp = min(max(samp, -1), 1)
        sine_list.append(samp)
    wav_file = wave.open(fname, "w")
    nchannels = 1
    sampwidth = 2
    maxamp = 32760  # as above
    framerate = int(frate_hz)
    nframes = datasize
    comptype = "NONE"
    compname = "not compressed"
    wav_file.setparams((nchannels, sampwidth, framerate, nframes, comptype,
                        compname))
    ampfactor = amp_proportion * maxamp
    print("writing", fname)
    for s in sine_list:
        wav_file.writeframes(struct.pack('h', int(s * ampfactor)))
    wav_file.close()
    if clipped:
        print("warning: amplitude CLIPPED")


def frequency_hz(note: str, octave: int = 4) -> float:
    badnote = "bad note"
    if (not note or not isinstance(note, str) or len(note) > 2
            or not isinstance(octave, int)):
        raise Exception(badnote)
    basenote = note[0].upper()
    # notenum = 0  # will be: semitones relative to reference A (A4)
    if basenote == 'C':
        notenum = -9
    elif basenote == 'D':
        notenum = -7
    elif basenote == 'E':
        notenum = -5
    elif basenote == 'F':
        notenum = -4
    elif basenote == 'G':
        notenum = -2
    elif basenote == 'A':
        notenum = 0
    elif basenote == 'B':
        notenum = 2
    else:
        raise Exception(badnote)
    if len(note) == 2:
        modifier = note[1]
        if modifier == '#':  # sharp
            notenum += 1
        elif modifier == 'b':  # flat
            notenum -= 1
        else:
            raise Exception(badnote)
    notenum += 12 * (octave - 4)
    # Frequency = (twelfth root of 2) ^ note * 440 Hz
    # Frequency = 2 ^ (note / 12) * 440 Hz
    freq_hz = pow(2, notenum / 12.0) * 440.0
    if DEBUG:
        print(note, octave, " = ", freq_hz, " Hz")
    return freq_hz
    # Test case: frequencyHz("A", 4) should return 440 (pitch standard)
    # Test case: frequencyHz("C", 4) should return 261.626 (middle C)
    # http://en.wikipedia.org/wiki/Scientific_pitch_notation


# noinspection PyPep8Naming
def ided3d() -> None:
    A4 = frequency_hz("A", 4)
    # C4 = frequency_hz("C", 4)
    C5 = frequency_hz("C", 5)
    Eb5 = frequency_hz("Eb", 5)
    E5 = frequency_hz("E", 5)
    Fs5 = frequency_hz("F#", 5)
    G5 = frequency_hz("G", 5)
    C6 = frequency_hz("C", 6)

    synth_complex([(E5, 1 / 3), (G5, 1 / 3), (C6, 1 / 3)],
                  duration_s=0.164, fname="correct.wav")
    synth_complex([(A4, 1 / 4), (C5, 1 / 4), (Eb5, 1 / 4), (Fs5, 1 / 4)],
                  duration_s=0.550, fname="incorrect.wav")


if __name__ == '__main__':
    ided3d()
