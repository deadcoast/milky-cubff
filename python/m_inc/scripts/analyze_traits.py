"""Analyze agent traits."""
import pandas as pd
from pathlib import Path

agents_path = Path(__file__).parent / "simulation_output" / "agents_final.csv"
df = pd.read_csv(agents_path)

knights = df[df['role'] == 'knight']
mercs = df[df['role'] == 'mercenary']

print("=" * 60)
print("Trait Analysis")
print("=" * 60)

print("\nKnights - Defensive traits:")
print(f"  Mean defend: {knights['defend'].mean():.1f}")
print(f"  Mean sense: {knights['sense'].mean():.1f}")
print(f"  Mean adapt: {knights['adapt'].mean():.1f}")
knight_total = (knights['defend'] + knights['sense'] + knights['adapt']).mean()
print(f"  Total defensive: {knight_total:.1f}")

print("\nMercenaries - Offensive traits:")
print(f"  Mean raid: {mercs['raid'].mean():.1f}")
print(f"  Mean sense: {mercs['sense'].mean():.1f}")
print(f"  Mean adapt: {mercs['adapt'].mean():.1f}")
merc_total = (mercs['raid'] + mercs['sense'] + mercs['adapt']).mean()
print(f"  Total offensive: {merc_total:.1f}")

print(f"\nTrait delta (knight - merc): {knight_total - merc_total:.1f}")
print(f"This creates a base advantage for knights even without employment bonus")
