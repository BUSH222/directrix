import pyaudio
import wave
import math
import time
import threading
import os
import platform


WINDOWS = platform.system() == "Windows"

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512
WAVE_OUTPUT_FOLDER = "recordings"
WORDLIST_FOLDER = "wordlists"
WORDLISTS = ["chars.txt", "exceptions.txt", "english3333.txt"]
device_index = 2
audio = pyaudio.PyAudio()

info = audio.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

if not os.path.exists(WAVE_OUTPUT_FOLDER):
    os.makedirs(WAVE_OUTPUT_FOLDER)

devicelist = []
for i in range(0, numdevices):
    if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        devicelist.append(i)

if len(devicelist) > 1:
    print("Select the device you want to record on.")
    print("Device list:")

    for i in devicelist:
        print("Input Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))

    print()

    index = int(input("Select the device id: "))
elif len(devicelist) < 1:
    raise ValueError("no devices, something broken")
elif len(devicelist) == 1:
    index = 0

print(f"recording via device {audio.get_device_info_by_host_api_device_index(0, index).get('name')}")
INDEX = index

class Recorder:
    def __init__(self):
        self.command = None # "record <word>" or None
        self.stop_flag = False
        self.threads = []
        self.recorder_running = True
    
    def receive_command(self, command):
        if self.command is not None:
            print("Recorder is busy. Please wait until the current recording is finished.")
            return
        else:
            self.command = command
    
    def stop_recording(self):
        self.stop_flag = True

    def shutdown(self):
        self.recorder_running = False

    def process_commands(self):
        while self.recorder_running:
            if self.command is not None:
                command = self.command
                self.command = None
                if command.startswith("record"):
                    word = command.split(" ")[1]
                    thread = threading.Thread(target=self.record_word, args=(word,))
                    thread.start()
                    self.threads.append(thread)
            time.sleep(0.05)
    
    def record_word(self, word):
        try:
            stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True, input_device_index = INDEX,
                            frames_per_buffer=CHUNK)
            
            Recordframes = []
            for i in range(0, math.ceil(RATE / CHUNK * 60)):  # Record for 60 seconds or until stopped
                data = stream.read(CHUNK)
                Recordframes.append(data)
                if self.stop_flag:
                    self.stop_flag = False
                    break

            stream.stop_stream()
            stream.close()

            waveFile = wave.open(f"{WAVE_OUTPUT_FOLDER}/{word}.wav", 'wb')
            waveFile.setnchannels(CHANNELS)
            waveFile.setsampwidth(audio.get_sample_size(FORMAT))
            waveFile.setframerate(RATE)
            waveFile.writeframes(b''.join(Recordframes))
            waveFile.close()
        except Exception as e:
            print(f"Error recording word '{word}': {e}")

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'




words = []
for L in WORDLISTS:
    with open(f"{WORDLIST_FOLDER}/{L}", "r") as f:
        words += [line.strip() for line in f.readlines()]
print(f"Loaded {len(words)} words from {len(WORDLISTS)} wordlists.")

print("TUTORIAL")
print("The program will prompt you with a word to say. The recording starts automatically. Say the word and press enter when done.")
print("If you want to pause the recording, type 'p' and press enter. To restart the current word, type 'r' and press enter.")


recorder = Recorder()

master_thread = threading.Thread(target=recorder.process_commands)
master_thread.start()

print("Ready? press enter", flush=True, end="")
input()
print()

for i, word in enumerate(words):
    restarted = True
    while restarted:
        restarted = False
        recorder.receive_command(f"record {word}")
        if not WINDOWS:
            print(f"[{i+1}/{len(words)} | {i/len(words)*100:.2f}%] say {bcolors.OKCYAN}{word.upper()}{bcolors.ENDC} ", flush=True, end="")
        else:
            print(f"[{i+1}/{len(words)} | {i/len(words)*100:.2f}%] say {word.upper()} ", flush=True, end="")
        a = input()
        if a == "":
            recorder.stop_recording()
        elif a == "p":
            print("Pausing. Press enter to continue.")
            recorder.stop_recording()
            restarted = True
            input()
        elif a == "r":
            print("Restarting current word.")
            recorder.stop_recording()
            restarted = True
        else:
            recorder.stop_recording()
            print("Unknown command. Continuing.")

        print()
            