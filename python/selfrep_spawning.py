# selfrep_spawning.py

import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + "/bin/"
)
import cubff
import json
import tempfile
import struct
import random

print(cubff.__dict__)

NUM_COPIES = 131072 // 2


def selfrep_spawn_rate(language, parsed_prog, sample_count=NUM_COPIES):
    with tempfile.NamedTemporaryFile(delete_on_close=False) as f:
        params = cubff.SimulationParams()
        params.num_programs = sample_count * 2
        params.seed = 0
        params.eval_selfrep = True
        f.write(struct.pack("=QQQ", 0, sample_count * 2, 0))
        for i in range(NUM_COPIES):
            f.write(parsed_prog)
            # TODO: seeded randomness
            # TODO: more realistic distribution
            f.write(random.randbytes(64))
        f.close()
        params.load_from = f.name
        params.allowed_interactions = [
            cubff.VectorUint32([i ^ 1]) for i in range(NUM_COPIES * 2)
        ]

        state = None

        def callback(s):
            nonlocal state
            state = s
            return True

        language.RunSimulation(params, None, callback)
        return sum([1 if x > 5 else 0 for x in state.replication_per_prog])


if __name__ == "__main__":
    language = cubff.GetLanguage(sys.argv[1])

    parsed_prog = language.Parse(sys.argv[2])

    print(selfrep_spawn_rate(language, parsed_prog))
