# Introduction
Humanoid explores Android apps like human. It uses deep learning to borrow experiences from app usage traces from human.

# Prerequisite

- Python 3.x
- [RICO](http://interactionmining.org/rico) dataset

# Getting Started

## Generate training data from RICO dataset

    $ cd rico

Edit `config.json` for custom configurations like dataset path, then

    $ python3 prepare_data.py -c config.json

## Visualize the dataset

    $ python3 visualizer.py -c config.json -i /path/to/training_data.pickle
