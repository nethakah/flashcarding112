# Spaced Repetition Flashcard App

A desktop flashcard application implementing the **SM-2 spaced repetition algorithm** (used by Anki) for optimized long-term memory retention.

## Features

- **Adaptive Scheduling**: Intervals increase/decrease according to the official Anki algorithm, adjusted via 4 rating options (Again, Hard, Good, Easy)
- **Persistent Storage**: Decks and card progress auto-saved to JSON, preserved across sessions
- **Learning Phases**: New cards progress through learning steps before graduating to review
- **Real-time Statistics**: Track new, learning, and due cards per deck

### UI

- **Navigation Bar**
  - *Decks*: Return to menu screen
  - *Add*: Add a card to the current deck (open a deck first, or select an empty deck from menu then press Add)
  - *Delete Card*: Appears when editing a card (top right)
  - *Delete Deck*: Appears when studying a deck (top left)

- **Screens**
  - Menu screen (default/starter view)
  - Create deck screen (press "Create Deck" on menu)
  - Card screen (add or edit cards)
  - Study screen (study cards one by one)

## Algorithm

The SM-2 algorithm adjusts review intervals based on a 4-point rating scale:

| Rating | Effect |
|--------|--------|
| Again (1) | Reset to learning phase |
| Hard (2) | Small interval increase, ease factor decreases |
| Good (3) | Normal interval increase (interval x ease factor) |
| Easy (4) | Large interval increase + ease factor bonus |

Cards in the **learning phase** use fixed steps:
- Step 0: 1 minute
- Step 1: 10 minutes  
- Step 2: 1 day (graduates to review)

In the **review phase**, intervals grow exponentially based on the ease factor (default 2.5x, capped between 1.3x and 4x).

## Controls

### Keyboard
| Key | Action |
|-----|--------|
| Space | Reveal answer |
| 1, 2, 3, 4 | Rate card (Again / Hard / Good / Easy) |
| Tab | Switch input fields |
| Enter | Confirm/Submit |
| Esc | Cancel/Close |

### Mouse
- Click decks to open them
- Click buttons to interact
- Click input fields to select them

### Debug Shortcuts (Menu Screen Only)
| Key | Action |
|-----|--------|
| s | Create sample deck with Python basics |
| t | Skip forward 1 day (for testing intervals) |

## Requirements

**Python 3.10 - 3.13 as of 12/2025**

```bash
pip install cmu-graphics
```

> **Note:** This project uses CMU Graphics, an educational library developed by Carnegie Mellon University. The library is no longer actively maintained and has limited Python version support. If you encounter issues, check their website at CMU Academy to verify the supported versions of Python.

## Usage

```bash
python flashcarding112.py
```

Data is automatically saved to `flashcard_data.json` in the same directory. No manual save/load required.

## Project Structure

```
spaced-repetition-flashcards/
├── flashcarding112.py    # Main application
├── flashcard_data.json   # Auto-generated save file
├── requirements.txt      # Dependencies
├── README.md
└── LICENSE
```

## References

- [Anki Deck Options Documentation](https://docs.ankiweb.net/deck-options.html)
- [Anki Spaced Repetition Algorithm FAQ](https://faqs.ankiweb.net/what-spaced-repetition-algorithm)
- [Open Spaced Repetition](https://github.com/open-spaced-repetition)

## License

MIT License - see LICENSE file
