# A Traffic Environemnt

## Setup

We recommend starting a new virtual environment: 

For normal set-up:
```
python3 -m venv .env
source .env/bin/activate
pip install .
```

For a set-up using the reinforcement learning tools:
```
python3 -m venv .env
source .env/bin/activate
pip install '.[rl]'
```

## Quick Start

To run a simple traffic simulation without AI (interactive driving):

```python
from main import main
from gui.render_mode import RenderMode

main(
    **SCENARIOS["TWO_CROSSINGS"],   # Use predefined scenario
    render_mode=RenderMode.GUI,    # Show GUI window
    show_reservation=True          # Display segments reserved by cars
)
```

## Function Parameters

### `main()` Function Signature

```python
def main(
    players,                          # Number of cars
    roads,                            # List of Road objects
    segmentation,                     # Road segmentation flag
    scenario_name,                    # Name of the scenario
    render_mode,                      # RenderMode.GUI or RenderMode.NO_GUI
    show_reservation,                 # Show reserved segments of cars
    rl_mode=None,                     # Which RL mode to use (train, optimize_hyperparams, etc.)
    rl_algorithm_type=None,           # Which RL algorithm to use
    observation_model_type=None,      # How agent perceives the world
    reward_type=None,                 # Reward strategy for learning
    id_model=None,                    # ID of saved model to load
    id_history=None,                  # ID of saved episode to replay
    id_hyperparams=None               # ID of saved hyperparameters
)
```

### Core Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `players` | int | Yes | Number of a* controlled vehicles in simulation |
| `roads` | list | Yes | Road network configuration (from SCENARIOS) |
| `segmentation` | bool | Yes | Enable road segmentation (from SCENARIOS) |
| `scenario_name` | str | Yes | Name of scenario (for logging/saving) |
| `render_mode` | RenderMode | Yes | `RenderMode.GUI` (show window) or `RenderMode.NO_GUI` (headless) |
| `show_reservation` | bool | Yes | Show reserved segments of cars |

### Reinforcement Learning Parameters

| Parameter | Type | Required | Description |
|-----------|------|---------|-------------|
| `rl_mode` | RLMode | No | Control mode (see [RL Modes](#rl-modes) below) |
| `rl_algorithm_type` | RLAlgorithmType | No | Learning algorithm |
| `observation_model_type` | ObservationModelType | No | How agent sees the world |
| `reward_type` | RewardType | No | How agent is rewarded |
| `id_model` | str | No | Timestamp to load saved model |
| `id_history` | str | No | Filename to replay saved episode |
| `id_hyperparams` | str | No | Timestamp to load optimized hyperparameters |

---

### Example: Run Different Scenarios

```python
from main import main
from gui.render_mode import RenderMode
from scenarios.scenarios import SCENARIOS

# Simple circuit
main(**SCENARIOS["CIRCUIT"], render_mode=RenderMode.GUI, show_reservation=True)

# More complex
main(**SCENARIOS["TWO_CROSSINGS"], render_mode=RenderMode.GUI, show_reservation=True)

# Advanced
main(**SCENARIOS["BIG_SCENARIO"], render_mode=RenderMode.GUI, show_reservation=True)
```

---

## RL Modes

Control how the simulation runs. Use with `rl_mode` parameter:

### `RLMode.TRAIN`

Train an agent from scratch with default hyperparameters.

```python
main(
    **SCENARIOS["TWO_CROSSINGS"],
    render_mode=RenderMode.GUI,
    show_reservation=True,
    rl_mode=RLMode.TRAIN,
    rl_algorithm_type=RLAlgorithmType.PPO,
    observation_model_type=ObservationModelType.NUMERIC_OBSERVATION,
    reward_type=RewardType.INITIAL_REWARD
)
```

**Output:** Saves trained model to `rl_results/models/`

### `RLMode.OPTIMIZE`

Find best hyperparameters using Optuna.

```python
main(
    **SCENARIOS["TWO_CROSSINGS"],
    render_mode=RenderMode.NO_GUI,  # Faster without rendering
    show_reservation=False,
    rl_mode=RLMode.OPTIMIZE,
    rl_algorithm_type=RLAlgorithmType.PPO,
    observation_model_type=ObservationModelType.NUMERIC_OBSERVATION,
    reward_type=RewardType.INITIAL_REWARD
)
```

**Output:** Saves best hyperparameters to `rl_results/hyperparameters/`

### `RLMode.OPTIMIZE_AND_TRAIN`

Find best hyperparameters, then train model with them.

```python
main(
    **SCENARIOS["TWO_CROSSINGS"],
    render_mode=RenderMode.NO_GUI,
    show_reservation=False,
    rl_mode=RLMode.OPTIMIZE_AND_TRAIN,
    rl_algorithm_type=RLAlgorithmType.PPO,
    observation_model_type=ObservationModelType.NUMERIC_OBSERVATION,
    reward_type=RewardType.INITIAL_REWARD
)
```

**Output:** Both hyperparameters and trained model saved

### `RLMode.LOAD_TRAINED_MODEL`

Load and run a previously trained model.

```python
main(
    **SCENARIOS["TWO_CROSSINGS"],
    render_mode=RenderMode.GUI,
    show_reservation=True,
    rl_mode=RLMode.LOAD_TRAINED_MODEL,
    rl_algorithm_type=RLAlgorithmType.PPO,
    observation_model_type=ObservationModelType.NUMERIC_OBSERVATION,
    reward_type=RewardType.INITIAL_REWARD,
    id_model="2025-10-29 18:26:52"  # Timestamp of saved model
)
```

### `RLMode.LOAD_HISTORY`

Replay a recorded episode.

```python
main(
    **SCENARIOS["TWO_CROSSINGS"],
    render_mode=RenderMode.GUI,
    show_reservation=True,
    rl_mode=RLMode.LOAD_HISTORY,
    id_model="2025-10-29 18:26:52",      # Model that created recording
    id_history="23:41:20_1768.pkl"       # Episode to replay
)
```

---

## Rendering Modes

### `RenderMode.GUI`

Shows interactive visualization window.

```python
render_mode=RenderMode.GUI
```

### `RenderMode.NO_GUI`

Headless mode (no window).

```python
render_mode=RenderMode.NO_GUI
```

---

## RL Algorithms

Currently supported (expand with more algorithms):

### `RLAlgorithmType.PPO`

Proximal Policy Optimization.

```python
rl_algorithm_type=RLAlgorithmType.PPO
```

---

## Observation Models

How the agent perceives the world. Currently supported (expand with other observation models):

### `ObservationModelType.NUMERIC_OBSERVATION`

Flattened vector of normalized numeric values:
- Lane positions and directions
- Car speeds and positions
- Segment reservations

```python
observation_model_type=ObservationModelType.NUMERIC_OBSERVATION
```

---

## Reward Functions

Guidance signal for learning. Currently supported (expand with other reward types):

### `RewardType.INITIAL_REWARD`

Default reward strategy.

```python
reward_type=RewardType.INITIAL_REWARD
```

---

## Common Workflows

### Workflow 1: Quick Test of New Scenario

```python

# Test scenario visually
main(
    **SCENARIOS["TWO_CROSSINGS"],
    render_mode=RenderMode.GUI,
    show_reservation=True
)
```

### Workflow 2: Train New Agent

```python

# Train agent from scratch
main(
    **SCENARIOS["TWO_CROSSINGS"],
    render_mode=RenderMode.NO_GUI,
    show_reservation=False,
    rl_mode=RLMode.TRAIN,
    rl_algorithm_type=RLAlgorithmType.PPO,
    observation_model_type=ObservationModelType.NUMERIC_OBSERVATION,
    reward_type=RewardType.INITIAL_REWARD
)
```

### Workflow 3: Optimize Hyperparameters

```python

main(
    **SCENARIOS["TWO_CROSSINGS"],
    render_mode=RenderMode.NO_GUI,
    show_reservation=False,
    rl_mode=RLMode.OPTIMIZE,
    rl_algorithm_type=RLAlgorithmType.PPO,
    observation_model_type=ObservationModelType.NUMERIC_OBSERVATION,
    reward_type=RewardType.INITIAL_REWARD
)
```

### Workflow 4: Optimize Then Train

```python

# Optimize hyperparameters, then train with best ones
main(
    **SCENARIOS["TWO_CROSSINGS"],
    render_mode=RenderMode.NO_GUI,
    show_reservation=False,
    rl_mode=RLMode.OPTIMIZE_AND_TRAIN,
    rl_algorithm_type=RLAlgorithmType.PPO,
    observation_model_type=ObservationModelType.NUMERIC_OBSERVATION,
    reward_type=RewardType.INITIAL_REWARD
)
```

### Workflow 5: Test Trained Agent

```python

# Load and visualize trained model
main(
    **SCENARIOS["TWO_CROSSINGS"],
    render_mode=RenderMode.GUI,
    show_reservation=True,
    rl_mode=RLMode.LOAD_TRAINED_MODEL,
    rl_algorithm_type=RLAlgorithmType.PPO,
    observation_model_type=ObservationModelType.NUMERIC_OBSERVATION,
    reward_type=RewardType.INITIAL_REWARD,
    id_model="2025-10-29 18:26:52"  # Replace with your model timestamp
)
```

### Workflow 6: Replay Episode

```python

# Replay a recorded episode
main(
    **SCENARIOS["TWO_CROSSINGS"],
    render_mode=RenderMode.GUI,
    show_reservation=True,
    rl_mode=RLMode.LOAD_HISTORY,
    id_model="2025-10-29 18:26:52",
    id_history="23:41:20_1768.pkl"
)
```

---

## Finding Model/History IDs

Models and episodes are saved with timestamps. Find them in:

```
rl_results/
├── models/
│   └── {scenario}/PPO/NUMERIC_OBSERVATION/INITIAL_REWARD/
│       ├── 2025-10-29 18:26:52/         ← model ID (timestamp)
│       │   ├── best_model
│       │   └── history/
│       │       ├── 23:41:20_1768.pkl    ← history ID (episode file)
│       │       └── ...
│       └── ...
└── hyperparameters/
    └── ...
```

Use the exact timestamp format: `"YYYY-MM-DD HH:MM:SS"`

---

## Advanced Usage

### Hyperparameter Configuration

Edit `reinforcement_learning/rl_constants.py`:

```python
TRAINING_TIMESTEPS = 10_000              # Training length
HYPERPARAMS_TRAINING_TIMESTEPS = 1_000   # Optuna trial length
OPTUNA_TRIALS = 2                        # Number of optimization trials
```

---

## Output Structure

After running with RL:

```
rl_results/
├── models/
│   └── two_crossings/PPO/NUMERIC_OBSERVATION/INITIAL_REWARD/
│       └── 2025-10-29 18:26:52/
│           ├── best_model              # Trained agent
│           └── history/                # Recorded episodes
│               ├── 23:41:20_1768.pkl
│               └── ...
└── hyperparameters/
    └── two_crossings/PPO/NUMERIC_OBSERVATION/INITIAL_REWARD/
        └── 2025-10-29 18:26:52/
            ├── best_params.parquet     # Optimized settings
            ├── trials.csv              # All trial results
            └── param_importance.html   # Visualization
```

---
