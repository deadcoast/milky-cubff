# Spatial Dynamics - Localized Economic Interactions

**Version**: 0.1.2  
**Status**: Planned  
**Dependencies**: Core economic engine (0.1.1)

## Overview

Spatial dynamics adds a 2D grid where agents have physical locations. This enables:

- **Localized Interactions**: Agents only interact with nearby neighbors
- **Territory Control**: Kings can claim and defend regions
- **Migration**: Agents can move to better economic opportunities
- **Spatial Diffusion**: Wealth and currency spread through space
- **Clustering**: Agents naturally form economic centers
- **Visualization**: Spatial heatmaps of economic activity

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Spatial Dynamics System                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   2D Grid    │───▶│ Neighborhood │───▶│  Interaction │ │
│  │   Manager    │    │   Finder     │    │   Resolver   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Migration   │◀───│   Diffusion  │◀───│  Territory   │ │
│  │   Engine     │    │   Processor  │    │   Manager    │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │   Spatial    │───▶│ Visualization│                      │
│  │   Metrics    │    │   Renderer   │                      │
│  └──────────────┘    └──────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## Grid System

### Grid Structure

```python
class SpatialGrid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells = [[[] for _ in range(width)] for _ in range(height)]
        self.agent_positions = {}  # agent_id -> (x, y)
    
    def place_agent(self, agent: Agent, x: int, y: int):
        """Place an agent at a specific location."""
        if not self.is_valid_position(x, y):
            raise ValueError(f"Invalid position: ({x}, {y})")
        
        # Remove from old position if exists
        if agent.id in self.agent_positions:
            old_x, old_y = self.agent_positions[agent.id]
            self.cells[old_y][old_x].remove(agent.id)
        
        # Add to new position
        self.cells[y][x].append(agent.id)
        self.agent_positions[agent.id] = (x, y)
    
    def get_neighbors(self, x: int, y: int, radius: int) -> List[str]:
        """Get all agent IDs within radius of position."""
        neighbors = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if self.is_valid_position(nx, ny):
                    neighbors.extend(self.cells[ny][nx])
        return neighbors
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is within grid bounds."""
        return 0 <= x < self.width and 0 <= y < self.height
```

### Neighborhood Types

#### Moore Neighborhood (8-connected)
```
┌───┬───┬───┐
│ X │ X │ X │
├───┼───┼───┤
│ X │ A │ X │
├───┼───┼───┤
│ X │ X │ X │
└───┴───┴───┘
```

#### Von Neumann Neighborhood (4-connected)
```
┌───┬───┬───┐
│   │ X │   │
├───┼───┼───┤
│ X │ A │ X │
├───┼───┼───┤
│   │ X │   │
└───┴───┴───┘
```

#### Extended Radius
```
┌───┬───┬───┬───┬───┐
│   │ X │ X │ X │   │
├───┼───┼───┼───┼───┤
│ X │ X │ X │ X │ X │
├───┼───┼───┼───┼───┤
│ X │ X │ A │ X │ X │
├───┼───┼───┼───┼───┤
│ X │ X │ X │ X │ X │
├───┼───┼───┼───┼───┤
│   │ X │ X │ X │   │
└───┴───┴───┴───┴───┘
```

## Localized Interactions

### Spatial Targeting

```python
class SpatialEconomicEngine(EconomicEngine):
    def __init__(self, registry: AgentRegistry, config: EconomicConfig, 
                 grid: SpatialGrid):
        super().__init__(registry, config)
        self.grid = grid
    
    def _execute_interactions(self) -> List[Event]:
        """Execute interactions with spatial constraints."""
        events = []
        
        for merc in self.registry.get_mercenaries():
            # Get mercenary's position
            merc_x, merc_y = self.grid.agent_positions[merc.id]
            
            # Find nearby kings (within raid radius)
            nearby_agent_ids = self.grid.get_neighbors(
                merc_x, merc_y, 
                radius=self.config.spatial.raid_radius
            )
            
            # Filter for kings only
            nearby_kings = [
                self.registry.get_agent(aid) 
                for aid in nearby_agent_ids 
                if self.registry.get_agent(aid).role == Role.KING
            ]
            
            if not nearby_kings:
                continue  # No targets in range
            
            # Pick closest king with highest exposed wealth
            target_king = self._pick_spatial_target(
                merc, nearby_kings, merc_x, merc_y
            )
            
            # Execute interaction (bribe/raid/defend)
            events.extend(self._resolve_interaction(merc, target_king))
        
        return events
    
    def _pick_spatial_target(self, merc: Agent, kings: List[Agent], 
                            merc_x: int, merc_y: int) -> Agent:
        """Pick target based on distance and wealth."""
        def score(king: Agent) -> float:
            king_x, king_y = self.grid.agent_positions[king.id]
            distance = abs(king_x - merc_x) + abs(king_y - merc_y)  # Manhattan
            wealth = economics.wealth_exposed(king, self.config)
            return wealth / (distance + 1)  # Prefer close, wealthy targets
        
        return max(kings, key=score)
```

## Migration

### Movement Rules

```python
class MigrationEngine:
    def __init__(self, grid: SpatialGrid, config: SpatialConfig):
        self.grid = grid
        self.config = config
    
    def process_migrations(self, agents: List[Agent], tick: int) -> List[Event]:
        """Process agent migrations based on economic incentives."""
        events = []
        
        for agent in agents:
            if not self._should_migrate(agent, tick):
                continue
            
            current_x, current_y = self.grid.agent_positions[agent.id]
            
            # Evaluate neighboring cells
            best_position = self._find_best_position(agent, current_x, current_y)
            
            if best_position != (current_x, current_y):
                # Pay migration cost
                migration_cost = self.config.migration_cost
                if agent.currency >= migration_cost:
                    agent.add_currency(-migration_cost)
                    new_x, new_y = best_position
                    self.grid.place_agent(agent, new_x, new_y)
                    
                    events.append(Event(
                        tick=tick,
                        type=EventType.MIGRATION,
                        agent=agent.id,
                        from_position=(current_x, current_y),
                        to_position=(new_x, new_y),
                        cost=migration_cost
                    ))
        
        return events
    
    def _should_migrate(self, agent: Agent, tick: int) -> bool:
        """Determine if agent should consider migrating."""
        # Migrate every N ticks
        if tick % self.config.migration_frequency != 0:
            return False
        
        # Role-specific migration rates
        migration_rates = {
            Role.KING: 0.05,      # Kings rarely move
            Role.KNIGHT: 0.15,    # Knights move to defend
            Role.MERCENARY: 0.30  # Mercenaries move to raid
        }
        
        return random.random() < migration_rates[agent.role]
    
    def _find_best_position(self, agent: Agent, x: int, y: int) -> tuple[int, int]:
        """Find best neighboring position for agent."""
        best_score = self._evaluate_position(agent, x, y)
        best_pos = (x, y)
        
        # Check all neighbors
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = x + dx, y + dy
                if not self.grid.is_valid_position(nx, ny):
                    continue
                
                score = self._evaluate_position(agent, nx, ny)
                if score > best_score:
                    best_score = score
                    best_pos = (nx, ny)
        
        return best_pos
    
    def _evaluate_position(self, agent: Agent, x: int, y: int) -> float:
        """Evaluate desirability of a position for an agent."""
        neighbors = self.grid.get_neighbors(x, y, radius=3)
        
        if agent.role == Role.KING:
            # Kings prefer areas with knights and few mercenaries
            knights = sum(1 for aid in neighbors if self.registry.get_agent(aid).role == Role.KNIGHT)
            mercs = sum(1 for aid in neighbors if self.registry.get_agent(aid).role == Role.MERCENARY)
            return knights - mercs * 2
        
        elif agent.role == Role.KNIGHT:
            # Knights prefer areas near their employer
            if agent.employer:
                employer_pos = self.grid.agent_positions.get(agent.employer)
                if employer_pos:
                    dist = abs(employer_pos[0] - x) + abs(employer_pos[1] - y)
                    return 10 / (dist + 1)
            return 0
        
        else:  # Mercenary
            # Mercenaries prefer areas with wealthy kings
            kings = [self.registry.get_agent(aid) for aid in neighbors 
                    if self.registry.get_agent(aid).role == Role.KING]
            return sum(k.wealth_total() for k in kings)
```

## Spatial Diffusion

### Wealth Diffusion

```python
class DiffusionProcessor:
    def __init__(self, grid: SpatialGrid, config: SpatialConfig):
        self.grid = grid
        self.config = config
    
    def process_diffusion(self, agents: Dict[str, Agent], tick: int) -> List[Event]:
        """Diffuse wealth and currency across space."""
        events = []
        
        # Create wealth density map
        wealth_map = self._create_wealth_map(agents)
        
        # Apply diffusion
        new_wealth_map = self._apply_diffusion(wealth_map)
        
        # Update agent wealth based on new map
        for agent_id, agent in agents.items():
            x, y = self.grid.agent_positions[agent_id]
            old_wealth = wealth_map[y][x]
            new_wealth = new_wealth_map[y][x]
            
            if new_wealth != old_wealth:
                delta = new_wealth - old_wealth
                # Distribute delta across traits proportionally
                self._distribute_wealth_delta(agent, delta)
                
                events.append(Event(
                    tick=tick,
                    type=EventType.DIFFUSION,
                    agent=agent_id,
                    wealth_delta=delta
                ))
        
        return events
    
    def _create_wealth_map(self, agents: Dict[str, Agent]) -> List[List[float]]:
        """Create 2D map of wealth density."""
        wealth_map = [[0.0 for _ in range(self.grid.width)] 
                     for _ in range(self.grid.height)]
        
        for agent_id, agent in agents.items():
            x, y = self.grid.agent_positions[agent_id]
            wealth_map[y][x] += agent.wealth_total()
        
        return wealth_map
    
    def _apply_diffusion(self, wealth_map: List[List[float]]) -> List[List[float]]:
        """Apply diffusion equation to wealth map."""
        rate = self.config.diffusion_rate
        new_map = [[0.0 for _ in range(self.grid.width)] 
                   for _ in range(self.grid.height)]
        
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                # Current cell
                current = wealth_map[y][x]
                
                # Neighbors (von Neumann)
                neighbors = []
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if self.grid.is_valid_position(nx, ny):
                        neighbors.append(wealth_map[ny][nx])
                
                # Diffusion: current + rate * (avg_neighbors - current)
                if neighbors:
                    avg_neighbors = sum(neighbors) / len(neighbors)
                    new_map[y][x] = current + rate * (avg_neighbors - current)
                else:
                    new_map[y][x] = current
        
        return new_map
```

## Territory Control

### Territory System

```python
class TerritoryManager:
    def __init__(self, grid: SpatialGrid):
        self.grid = grid
        self.territories = {}  # (x, y) -> king_id
        self.territory_strength = {}  # (x, y) -> strength
    
    def claim_territory(self, king: Agent, x: int, y: int, strength: int):
        """King claims a territory cell."""
        current_owner = self.territories.get((x, y))
        current_strength = self.territory_strength.get((x, y), 0)
        
        if current_owner is None or strength > current_strength:
            self.territories[(x, y)] = king.id
            self.territory_strength[(x, y)] = strength
            return True
        return False
    
    def get_territory_owner(self, x: int, y: int) -> Optional[str]:
        """Get the king who owns this territory."""
        return self.territories.get((x, y))
    
    def get_king_territory_size(self, king_id: str) -> int:
        """Get total territory controlled by a king."""
        return sum(1 for owner in self.territories.values() if owner == king_id)
    
    def process_territory_decay(self, tick: int):
        """Reduce territory strength over time."""
        decay_rate = 0.95
        for pos in list(self.territory_strength.keys()):
            self.territory_strength[pos] *= decay_rate
            if self.territory_strength[pos] < 1.0:
                del self.territories[pos]
                del self.territory_strength[pos]
```

## Visualization

### Spatial Heatmaps

```python
class SpatialVisualizer:
    def __init__(self, grid: SpatialGrid):
        self.grid = grid
    
    def generate_wealth_heatmap(self, agents: Dict[str, Agent]) -> np.ndarray:
        """Generate wealth density heatmap."""
        heatmap = np.zeros((self.grid.height, self.grid.width))
        
        for agent_id, agent in agents.items():
            x, y = self.grid.agent_positions[agent_id]
            heatmap[y, x] += agent.wealth_total()
        
        return heatmap
    
    def generate_activity_heatmap(self, events: List[Event]) -> np.ndarray:
        """Generate activity heatmap from events."""
        heatmap = np.zeros((self.grid.height, self.grid.width))
        
        for event in events:
            if hasattr(event, 'position'):
                x, y = event.position
                heatmap[y, x] += 1
        
        return heatmap
    
    def render_to_image(self, heatmap: np.ndarray, colormap: str = 'viridis') -> Image:
        """Render heatmap to image."""
        import matplotlib.pyplot as plt
        from matplotlib.colors import Normalize
        
        fig, ax = plt.subplots(figsize=(10, 10))
        im = ax.imshow(heatmap, cmap=colormap, norm=Normalize())
        plt.colorbar(im, ax=ax)
        
        # Convert to image
        fig.canvas.draw()
        image = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        
        plt.close(fig)
        return Image.fromarray(image)
```

## Configuration

```yaml
spatial:
  enabled: true
  
  # Grid settings
  grid_size: [100, 100]
  wrap_edges: false  # Toroidal topology if true
  
  # Neighborhood
  neighborhood_type: "moore"  # moore, von_neumann, or extended
  interaction_radius: 5
  raid_radius: 3
  
  # Migration
  migration_enabled: true
  migration_cost: 10
  migration_frequency: 5  # Every N ticks
  
  # Diffusion
  diffusion_enabled: true
  diffusion_rate: 0.1
  diffusion_frequency: 1
  
  # Territory
  territory_enabled: true
  territory_decay_rate: 0.95
  
  # Visualization
  heatmap_update_frequency: 10
  heatmap_colormap: "viridis"
```

## Performance Considerations

- **Grid Size**: O(width × height) memory
- **Neighbor Lookup**: O(radius²) per agent
- **Diffusion**: O(width × height) per tick
- **Migration**: O(agents) per migration tick

**Optimization**: Use spatial indexing (quadtree) for large grids

---

**Next**: [Learning Agents Architecture](learning-agents.md)
