"""Check trait drip events."""
import json

with open('test_output/ticks.json', 'r') as f:
    data = json.load(f)

print("Checking for agents with copy >= 12 in each tick:")
for tick_data in data[:5]:  # First 5 ticks
    tick = tick_data['tick']
    agents = tick_data['agents']
    high_copy = [a for a in agents if a['wealth']['copy'] >= 12]
    print(f"\nTick {tick}: {len(high_copy)} agents with copy >= 12")
    for agent in high_copy[:3]:  # Show first 3
        print(f"  {agent['id']}: copy={agent['wealth']['copy']}")

# Check events
with open('test_output/events.csv', 'r') as f:
    lines = f.readlines()
    drip_events = [line for line in lines if 'trait_drip' in line]
    print(f"\nTotal trait_drip events: {len(drip_events)}")
    if drip_events:
        print("First 5 trait_drip events:")
        for event in drip_events[:5]:
            print(f"  {event.strip()}")
