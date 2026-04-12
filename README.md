# Balatro Certamen - Desktop Card Game Application

A Python-based desktop implementation of a strategic card game featuring dynamic auction mechanics, joker modifiers, and an AI opponent with heuristic-based decision making.

## Getting Started

### Download the Source Code

Clone the repository from GitHub:

```bash
git clone https://github.com/thegrublord/BalatroCartemenPrototyping.git
cd BalatroCartemenPrototyping/app
```

Or [download as ZIP](https://github.com/thegrublord/BalatroCartemenPrototyping/archive/refs/heads/main.zip) and extract the files.

### Prerequisites

- **Python 3.8+** - [Download from python.org](https://www.python.org/downloads/)
- **pip** (comes with Python)

### Installation

1. **Install required dependencies:**

```bash
pip install -r requirements.txt
```

Key dependencies:
- `PySide6` - GUI framework for desktop application
- `pandas` - Data analysis and CSV output for simulations
- `numpy` - Numerical computations

2. **Verify installation:**

```bash
python main.py
```

## Project Structure

```
app/
├── main.py                          # Entry point for the desktop application
├── run_simulation.py                # Entry point for running simulations
├── game/                            # Core game logic
│   ├── __init__.py
│   ├── models.py                    # Card and game data models
│   ├── rules.py                     # Game rules and scoring logic
│   ├── state.py                     # Game state management
│   ├── ai.py                        # AI opponent with heuristic decision-making
├── simulation/                      # Standalone simulation engine
│   ├── __init__.py
│   ├── runner.py                    # Simulation runner
│   ├── game_engine.py               # Game simulation engine
│   ├── auction_manager.py           # Auction mechanics
│   ├── hand_evaluator.py            # Hand evaluation and scoring
│   ├── models.py                    # Simulation data models
├── ui/                              # Desktop GUI components
│   ├── __init__.py
│   ├── main_window.py               # Main application window
│   ├── card_widgets.py              # Card display widgets
│   ├── panels.py                    # Game UI panels
├── assets/                          # Game card assets (JSON data)
│   ├── auction_cards/               # Auction card definitions
│   ├── jokers/                      # Joker card data
│   ├── planets/                     # Planet card data
└── requirements.txt                 # Python dependencies
```

## Running the Application

### Desktop Game (GUI)

Launch the interactive desktop game:

```bash
python main.py
```

This opens a graphical window where you can:
- Play against an AI opponent
- Bid on cards in auctions
- Select and play hands
- Use joker modifiers to enhance scoring
- Progress through multiple rounds

### Running Simulations

Run automated game simulations to analyze AI strategy and card outcomes:

```bash
python run_simulation.py
```

Or use the simulation module directly:

```bash
python -m simulation.runner
```

**Output files:**
- `simulation_results.csv` - Per-game statistics (one row per simulation game)
- `simulation_summary.csv` - Aggregated joker statistics across all simulations
- `simulation_hand_summary.csv` - Hand evaluation metrics

The simulation engine runs headless games between AI players and generates detailed statistics on card performance, scoring patterns, and strategy effectiveness.

## Features

- **Interactive Desktop GUI** - Play against AI opponent with visual card display
- **AI Decision Making** - Heuristic-based AI for bidding, hand selection, and card play
- **Dynamic Scoring** - Joker modifiers, planet effects, and momentum-based scoring
- **Auction Mechanics** - Real-time auction system for card acquisition
- **Simulation Engine** - Run thousands of automated games and analyze results
- **Card Asset System** - Extensible card definitions with JSON-based assets

## Game Concepts

### Auction System
Players bid on cards in auction rounds. Strategic bidding determines card acquisition and game progression.

### Jokers
Special modifier cards that enhance scoring through multiplicative or additive effects. Different jokers have different strategies and synergies.

### Hand Evaluation
The game evaluates card hands using scoring rules including joker modifiers, planet effects, and momentum bonuses.

### AI Strategy
The AI uses heuristic-based decision making for:
- Auction bidding strategies
- Hand selection and play
- Resource management
- Long-term planning

## Troubleshooting

**ImportError: No module named 'PySide6'**
- Install dependencies: `pip install -r requirements.txt`

**GUI doesn't appear**
- Ensure Python 3.8+ is installed
- Verify PySide6 installation: `python -c "import PySide6; print(PySide6.__version__)"`

**Simulation produces no output**
- Check that `simulation/` folder contains all required modules
- Verify CSV files are created in the working directory

## Author

Developed for Balatro Certamen competition.

## License

[Specify your license here]