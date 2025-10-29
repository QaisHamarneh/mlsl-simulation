# A Traffic Environment

## Setup

We recommend starting a new virtual environment: 

```
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

## Run Normal

To run the code, just run the `main.py` file. You can change the `render_mode` parameter to switch between gui and non_gui mode. The `show_reservations` can be changed between True and False.
You can also test some properties of the environment manually using the files `gui/pyglet_class_test.py` and `gui/pyglet_gui_manual.py`.

## Run Reinforcement Learning Mode

All previously explained parameters are used in the same way but additionaly the parameters **rl_mode**, **rl_algorithm_type**, **observation_model_type**, **reward_type**, **id_model**, and **id_hyperparams** can be used. If one of **rl_mode**, **rl_algorithm_type**, **observation_model_type** or **reward_type** is not set to None all the others also have to be a non None type.

### rl_mode

With this parameter the reinforcement learning mode can be selected.

RLMode.TRAIN is used for training of a new model.

RLMode.LOAD is used for loading of a previously trained model and can only be used in combination with the id_model parameter. 

RLMode.OPTIMIZE is used for hyperparameter optimization. 

RLMode.OPTIMIZE_AND_TRAIN is used for optimizing hyperparameters and then useing them directly to train a new model.

### rl_algorithm_type

This parameter is used to select the underlying reinforcement learning algorithm for training (e.g. PPO).

### observation_model_type

This parameter is used to select the observations model to be used in training (e.g. NUMERIC_OBSERVATION).

### reward_type

This paraemeter is used to select the reward type to be used in training (e.g. INITIAL_REWARD).

### id_model and id_hyperparams

These two parameters are used to load previously stored models or hyperparameters. 

### Results Structure

In the results directory we have the two sub-directories hyperparameters and models. To save results of the rl_modes RLMode.TRAIN, RLMode.OPTIMIZE and RLMode.OPTIMIZE_AND_TRAIN in these sub-directories, we make use of the selected parameters in main. 

If a model would be trained with the parameters 
- scenario=CIRCUIT
- rl_mode=RLMode.TRAIN
- rl_algorithm_type=RLAlgorithmType.PPO
- observation_model_type=ObservationModelType.NUMERIC_OBSERVATION
- reward_type=RewardType.INITIAL_REWARD

the results would be saved in this structure: *results/models/circuit/PPO/NUMERIC_OBSERVATION/INITIAL_REWARD/* timestamp */best_model.zip*

timestamp: Each time a model or hyperparameters are saved a timestamp is created which can be used to load these model or hyperparameters later (see Examples).

If rl_mode would have been RLMode.OPTIMIZE the results structure would have been as follows: 

*results/hyperparameters/circuit/PPO/NUMERIC_OBSERVATION/INITIAL_REWARD/timestamp/best_params.csv param_importance.html trials.csv*

### Examples

**Load Model**

If one wants to load model a with the path 

*results/models/circuit/PPO/NUMERIC_OBSERVATION/INITIAL_REWARD/2025-10-29 18:26:52/best_model.zip*, 

the parameters have to be set to: 
- rl_mode=RLMode.LOAD
- rl_algorithm_type=RLAlgorithmType.PPO
- observation_model_type=ObservationModelType.NUMERIC_OBSERVATION
- reward_type=RewardType.INITIAL_REWARD
- id_model="2025-10-29 18:26:52"

**Train Model with specific hyperparameters**

If one wants to train a model with a set of previously optimized hyperparameters located at 

*results/hyperparameters/circuit/PPO/NUMERIC_OBSERVATION/INITIAL_REWARD/2025-10-29 18:26:52/*, 

the parameters have to be set to: 
- rl_mode=RLMode.TRAIN
- rl_algorithm_type=RLAlgorithmType.PPO 
- observation_model_type=ObservationModelType.NUMERIC_OBSERVATION 
- reward_type=RewardType.INITIAL_REWARD
- id_hyperparams="2025-10-29 18:26:52"
