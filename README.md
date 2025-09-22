<div align="center">

# // Mindfall
A 2D top-down puzzle-adventure game where you are a student trapped inside a corrupted reality. Navigate the glitched simulation of your college, solve puzzles using a command-line interface, and reboot the system before you're deleted.

Made for GlitchCET 's Ctrl+Create Event
<br>

<img width="1602" height="940" alt="image" src="https://github.com/user-attachments/assets/3d06c994-b245-48e6-8868-23e394784cac" />
<img width="1602" height="940" alt="image" src="https://github.com/user-attachments/assets/236ef2ad-da88-44f9-b5a5-f1cafc188af1" />
<img width="1602" height="940" alt="image" src="https://github.com/user-attachments/assets/3196ea91-01e7-42e1-86c3-5a6d2270e074" />

</div>

# Story
- TO BE ADDED

# Gameplay
Your goal is to navigate through five chapters of the corrupted simulation and initiate a system reboot.

- Explore: Move through the 2D levels, which are glitched representations of familiar locations in the College of Engineering, Trivandrum.

- Interact: Discover objects like flickering terminals, corrupted data logs, and notice boards to piece together the story and find clues.

- Solve Puzzles: Each level has puzzles themed around campus life and computer science. Solving them reveals crucial override codes.

- Use the Terminal: Access the main terminal and use a Unix-like command-line interface. Use commands like ls, cat, and override to use the codes you've found and increase your Privilege Level.

- Escape: Once you achieve the maximum Privilege Level (3/3), you can unlock the final door and progress to the next stage of the simulation.

# Features
- Narrative-Driven Progression: A complete story that unfolds through level intros, in-game items, and terminal files.

- Interactive Terminal: An authentic-feeling terminal interface with commands (status, override, ls, cat, etc.) and command history.

- Atmospheric Effects: Dynamic glitch effects, screen shake, and flickering lights create a tense, unstable atmosphere.

- Rich Audio: Unique background music for the menu, game, and terminal states, along with a suite of sound effects for interaction, UI, and glitches.

- Persistent Settings: A full settings menu to control Master, Music, and SFX volume, as well as UI preferences. All settings are saved to a settings.json file.

- Dynamic Story Display: Story and level intros are presented with a typewriter effect and sound for maximum immersion.

# Controls

- W, A, S, D / ↑,←,↓,→	 |  Move the player
- E	| Interact with highlighted objects
- M	| Toggle the mini-map on/off
- ESC	| Exit the Terminal, or go back from menus
- Any Key	| Speed up / Skip story intros

# Project Structure

```

src/
├── assets/
│   ├── audios/
│   │   ├── ambience.mp3
│   │   ├── glitch.mp3
│   │   ├── menu.mp3
│   │   └── ... (and all other .mp3 files)
│   └── images/
│       ├── terminal.png
│       ├── door_locked.png
│       └── ... (and all other .png files)
        data/
│       ├── settings.json
├── main.py                 

```

# Technology Stack

- Language: Python 3

- Core Library: Pygame

- Standard Libraries: json, webbrowser, time, random
