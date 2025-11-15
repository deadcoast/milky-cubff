# runit.py

import sys
import os
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + "/bin/"
)
import cubff
import json


language = cubff.GetLanguage(sys.argv[1])


def callback(state):
    print(json.dumps({"epoch": state.epoch, "higher_entropy": state.higher_entropy}))
    return state.higher_entropy > 3.0


params = cubff.SimulationParams()
params.num_programs = 131072
params.seed = int(sys.argv[2])

language.RunSimulation(params, None, callback)
