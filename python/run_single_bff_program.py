# run_single_bff_program.py

from bin import cubff
import sys

args = sys.argv

if len(args) != 3:
    printf(f"Usage: python3 run_single_bff_program.py <filename> <max_steps_to_run>")
    sys.exit(1)


try:
    filename = args[1]
    with open(filename, 'rb') as f:
        program_bytes = f.read()
    num_steps = int(args[2])

except Exception as e:
    print(f"Error: {e}")

language = cubff.GetLanguage("bff")
cubff.ResetColors()

program = cubff.VectorUint8(program_bytes)
language.PrintProgram(128, program, [64])
language.RunSingleParsedProgram(program, num_steps, True)
