"""Analyze simulation results."""
import pandas as pd
from pathlib import Path

events_path = Path(__file__).parent / "simulation_output" / "events.csv"
df = pd.read_csv(events_path)

# Analyze defend events
defend_df = df[df['type'].str.contains('defend', na=False)]
wins = len(df[df['type'] == 'defend_win'])
losses = len(df[df['type'] == 'defend_loss'])
total = wins + losses

print("=" * 60)
print("Defend Contest Analysis")
print("=" * 60)
print(f"Knight wins: {wins} ({wins/total*100:.1f}%)")
print(f"Merc wins: {losses} ({losses/total*100:.1f}%)")
print(f"Total defends: {total}")
print(f"\nP_knight statistics:")
print(f"  Mean: {defend_df['p_knight'].mean():.3f}")
print(f"  Min: {defend_df['p_knight'].min():.3f}")
print(f"  Max: {defend_df['p_knight'].max():.3f}")
print(f"  Std: {defend_df['p_knight'].std():.3f}")

# Show distribution
print(f"\nP_knight distribution:")
bins = [0, 0.3, 0.5, 0.7, 0.9, 1.0]
labels = ['0-0.3', '0.3-0.5', '0.5-0.7', '0.7-0.9', '0.9-1.0']
defend_df['p_bin'] = pd.cut(defend_df['p_knight'], bins=bins, labels=labels)
print(defend_df['p_bin'].value_counts().sort_index())
