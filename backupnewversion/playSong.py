# to build, use "cd (playsong directory)"
# pyinstaller --onefile playSong.py

import pyMIDI
import threading
import random

import keyboard

from pynput.keyboard import Key, Controller, Listener

global isPlaying
global infoTuple
global storedIndex
global playback_speed
global elapsedTime
global origionalPlaybackSpeed
global speedMultiplier
global legitModeActive

isPlaying = False
legitModeActive = False

storedIndex = 0
elapsedTime = 0
origionalPlaybackSpeed = 1.0
speedMultiplier = 1.05

keyboardController = Controller()

key_delete = 'delete'
key_shift = 'shift'
key_end = 'end'
key_home = 'home'
key_load = 'f5'
key_speed_up = 'page_up'
key_slow_down = 'page_down'
key_legit_mode = 'insert'

def runPyMIDI():
    try:
        pyMIDI.main()
    except Exception as e:
        print(f"pyMIDI.py was interrupted or encountered an error: {e}")

def toggleLegitMode(event):
    global legitModeActive
    legitModeActive = not legitModeActive
    status = "ON" if legitModeActive else "OFF"
    print(f"Legit Mode turned {status}")

def calculateTotalDuration(notes):
    total_duration = sum([note[0] for note in notes])
    return total_duration

def onDelPress():
    global isPlaying
    isPlaying = not isPlaying

    if isPlaying:
        print("Playing...")
        playNextNote()
    else:
        print("Stopping...")

def speedUp(event):
    global playback_speed
    playback_speed *= speedMultiplier
    print(f"Speeding up: Playback speed is now {playback_speed:.2f}x")

def slowDown(event):
    global playback_speed
    playback_speed /= speedMultiplier
    print(f"Slowing down: Playback speed is now {playback_speed:.2f}x")


def pressLetter(strLetter):
    if strLetter == 'z':
        keyboard.press('f1')
        keyboardController.press(strLetter)
        keyboard.release('f1')
        keyboardController.release(strLetter)
    elif strLetter == 'x':
        keyboard.press('f2')
        keyboardController.press(strLetter)
        keyboard.release('f2')
        keyboardController.release(strLetter)
    elif strLetter == 'c':
        keyboard.press('f3')
        keyboardController.press(strLetter)
        keyboard.release('f3')
        keyboardController.release(strLetter)
    else:
        keyboardController.press(strLetter)
        keyboardController.release(strLetter)
	
def releaseLetter(strLetter):
    if strLetter == 'z':
        keyboardController.release(strLetter)
        keyboard.release('f1')
        print('key pressed')
    elif strLetter == 'x':
        keyboardController.release(strLetter)
        keyboard.release('f2')
        print('key pressed')
    elif strLetter == 'c':
        keyboardController.release(strLetter)
        keyboard.release('f3')
        print('key pressed')
    else:
        keyboardController.release(strLetter)
        print('key not pressed')
	
def processFile():
    global playback_speed
    with open("song.txt", "r") as macro_file:
        lines = macro_file.read().split("\n")
        tOffsetSet = False
        tOffset = 0

        if len(lines) > 0 and "=" in lines[0]:
            try:
                playback_speed = float(lines[0].split("=")[1])
                print("Playback speed is set to %.2f" % playback_speed)
            except ValueError:
                print("Error: Invalid playback speed value")
                return None
        else:
            print("Error: Invalid playback speed format")
            return None

        tempo = None
        processedNotes = []
        
        for line in lines[1:]:
            if 'tempo' in line:
                try:
                    tempo = 60 / float(line.split("=")[1])
                except ValueError:
                    print("Error: Invalid tempo value")
                    return None
            else:
                l = line.split(" ")
                if len(l) < 2:
                    continue
                try:
                    waitToPress = float(l[0])
                    notes = l[1]
                    processedNotes.append([waitToPress, notes])
                    if not tOffsetSet:
                        tOffset = waitToPress
                        tOffsetSet = True
                except ValueError:
                    print("Error: Invalid note format")
                    continue

        if tempo is None:
            print("Error: Tempo not specified")
            return None

    return [tempo, tOffset, processedNotes]

def floorToZero(i):
	if(i > 0):
		return i
	else:
		return 0

# for this method, we instead use delays as l[0] and work using indexes with delays instead of time
# we'll use recursion and threading to press keys
def parseInfo():
	
	tempo = infoTuple[0]
	notes = infoTuple[2][1:]
	
	# parse time between each note
	# while loop is required because we are editing the array as we go
	i = 0
	while i < len(notes)-1:
		note = notes[i]
		nextNote = notes[i+1]
		if "tempo" in note[1]:
			tempo = 60/float(note[1].split("=")[1])
			notes.pop(i)

			note = notes[i]
			if i < len(notes)-1:
				nextNote = notes[i+1]
		else:
			note[0] = (nextNote[0] - note[0]) * tempo
			i += 1

	# let's just hold the last note for 1 second because we have no data on it
	notes[len(notes)-1][0] = 1.00

	return notes

def playNextNote():
    global isPlaying, storedIndex, playback_speed, elapsedTime, legitModeActive

    notes = infoTuple[2]
    total_duration = calculateTotalDuration(notes)

    if isPlaying and storedIndex < len(notes):
        noteInfo = notes[storedIndex]
        delay = floorToZero(noteInfo[0])
        # Legit Mode
        if legitModeActive:
            delay_variation = random.uniform(0.90, 1.10)
            delay *= delay_variation

            if random.random() < 0.05:
                if random.random() < 0.5 and len(noteInfo[1]) > 1:
                    noteInfo[1] = noteInfo[1][1:]
                else:
                    if storedIndex == 0 or notes[storedIndex-1][0] > 0.3:
                        delay += random.uniform(0.1, 0.5)

        elapsedTime += delay

        # Regular Mode
        if noteInfo[1][0] == "~":
            for n in noteInfo[1][1:]:
                releaseLetter(n)
        else:
            for n in noteInfo[1]:
                pressLetter(n)

        if "~" not in noteInfo[1]:
            elapsed_mins, elapsed_secs = divmod(elapsedTime, 60)
            total_mins, total_secs = divmod(total_duration, 60)
            print(f"[{int(elapsed_mins)}m {int(elapsed_secs)}s/{int(total_mins)}m {int(total_secs)}s] {noteInfo[1]}")

        storedIndex += 1
        if delay == 0:
            playNextNote()
        else:
            threading.Timer(delay/playback_speed, playNextNote).start()
    elif storedIndex >= len(notes):
        isPlaying = False
        storedIndex = 0
        elapsedTime = 0

def rewind(KeyboardEvent):
	global storedIndex
	if storedIndex - 10 < 0:
		storedIndex = 0
		
	else:
		storedIndex -= 10
	print("Rewound to %.2f" % storedIndex)

def skip(KeyboardEvent):
	global storedIndex
	if storedIndex + 10 > len(infoTuple[2]):
		isPlaying = False
		storedIndex = 0
	else:
		storedIndex += 10
	print("Skipped to %.2f" % storedIndex)

def onKeyPress(key):
    global isPlaying, storedIndex, playback_speed, legitModeActive

    try:
        if key == Key.delete:
            onDelPress()
        elif key == Key.home:
            rewind(None)
        elif key == Key.end:
            skip(None)
        elif key == Key.page_up:
            speedUp(None)
        elif key == Key.page_down:
            slowDown(None)
        elif key == Key.insert:
            toggleLegitMode(None)
        elif key == Key.f5:
            runPyMIDI()
        elif key == Key.esc:
            return False
    except AttributeError:
        pass

def printControls():
    title = "Controls"
    controls = [
        ("DELETE", "Play/Pause"),
        ("HOME", "Rewind"),
        ("END", "Advance"),
        ("PAGE UP", "Speed Up"),
        ("PAGE DOWN", "Slow Down"),
        ("INSERT", "Toggle Legit Mode"),
        ("F5", "Load New Song (NOT RECOMMENDED)"),
        ("ESC", "Exit")
    ]

    print(f"\n{'=' * 20}\n{title.center(20)}\n{'=' * 20}")

    for key, action in controls:
        print(f"{key.ljust(10)} : {action}")

    print(f"{'=' * 20}\n")

def main():
    global isPlaying, infoTuple, playback_speed

    infoTuple = processFile()
    if infoTuple is None:
        return

    infoTuple[2] = parseInfo()

    printControls()

    with Listener(on_press=onKeyPress) as listener:
        listener.join()
			
if __name__ == "__main__":
	main()
