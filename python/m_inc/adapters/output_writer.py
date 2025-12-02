"""Output writer for M|inc results."""

import json
import gzip
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.models import TickResult, Event, Agent
from ..core.config import OutputConfig
from ..core.schemas import validate_tick_result


class OutputWriter:
    """Writer for M|inc output files.
    
    Handles:
    - JSON tick snapshots
    - CSV event logs
    - CSV final agent state
    - Schema validation
    - Optional compression
    """
    
    def __init__(self, output_dir: Path | str, config: OutputConfig, 
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize output writer.
        
        Args:
            output_dir: Directory to write output files
            config: Output configuration
            metadata: Optional metadata to include in outputs
        """
        self.output_dir = Path(output_dir)
        self.config = config
        self.metadata = metadata or {}
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize file paths
        self.ticks_path = self.output_dir / "ticks.json"
        self.events_path = self.output_dir / "events.csv"
        self.final_agents_path = self.output_dir / "agents_final.csv"
        
        if self.config.compress:
            self.ticks_path = self.output_dir / "ticks.json.gz"
        
        # Track if we've written headers
        self._events_header_written = False
        
        # Accumulate ticks for batch writing
        self._tick_results: List[TickResult] = []
    
    def write_tick_json(self, tick_result: TickResult) -> None:
        """Write a tick result to JSON.
        
        Args:
            tick_result: Tick result to write
        """
        if not self.config.json_ticks:
            return
        
        # Accumulate for batch writing
        self._tick_results.append(tick_result)
    
    def write_event_csv(self, events: List[Event]) -> None:
        """Write events to CSV log.
        
        Args:
            events: List of events to write
        """
        if not self.config.csv_events or not events:
            return
        
        # Define CSV columns
        fieldnames = [
            "tick", "type", "king", "knight", "merc", "amount", "stake", 
            "p_knight", "notes", "trait", "delta", "invest", "wealth_created",
            "rv", "threshold", "employer", "agent"
        ]
        
        # Open in append mode
        mode = 'a' if self._events_header_written else 'w'
        
        with open(self.events_path, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not self._events_header_written:
                writer.writeheader()
                self._events_header_written = True
            
            for event in events:
                row = event.to_dict()
                # Convert EventType enum to string
                row["type"] = row["type"]
                writer.writerow(row)
    
    def write_final_agents_csv(self, agents: List[Agent]) -> None:
        """Write final agent state to CSV.
        
        Args:
            agents: List of agents to write
        """
        if not self.config.csv_final_agents or not agents:
            return
        
        # Define CSV columns
        fieldnames = [
            "id", "role", "currency", "compute", "copy", "defend", "raid",
            "trade", "sense", "adapt", "wealth_total", "employer", 
            "retainer_fee", "bribe_threshold", "alive"
        ]
        
        with open(self.final_agents_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for agent in agents:
                row = {
                    "id": agent.id,
                    "role": agent.role.value,
                    "currency": agent.currency,
                    "compute": agent.wealth.compute,
                    "copy": agent.wealth.copy,
                    "defend": agent.wealth.defend,
                    "raid": agent.wealth.raid,
                    "trade": agent.wealth.trade,
                    "sense": agent.wealth.sense,
                    "adapt": agent.wealth.adapt,
                    "wealth_total": agent.wealth_total(),
                    "employer": agent.employer or "",
                    "retainer_fee": agent.retainer_fee,
                    "bribe_threshold": agent.bribe_threshold,
                    "alive": agent.alive
                }
                writer.writerow(row)
    
    def flush_ticks(self) -> None:
        """Flush accumulated tick results to JSON file."""
        if not self.config.json_ticks or not self._tick_results:
            return
        
        # Convert to dict format
        ticks_data = []
        for tick_result in self._tick_results:
            tick_dict = tick_result.to_dict()
            # Add metadata to first tick
            if len(ticks_data) == 0:
                tick_dict["meta"] = self.metadata
            ticks_data.append(tick_dict)
        
        # Write to file
        if self.config.compress:
            with gzip.open(self.ticks_path, 'wt', encoding='utf-8') as f:
                json.dump(ticks_data, f, indent=2)
        else:
            with open(self.ticks_path, 'w', encoding='utf-8') as f:
                json.dump(ticks_data, f, indent=2)
        
        # Clear accumulator
        self._tick_results.clear()
    
    def validate_schema(self, data: Dict[str, Any], schema_name: str) -> bool:
        """Validate data against a schema.
        
        Args:
            data: Data to validate
            schema_name: Name of schema to validate against
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if schema_name == "tick_result":
                validate_tick_result(data)
            elif schema_name == "agent":
                from ..core.schemas import validate_agent
                validate_agent(data)
            elif schema_name == "event":
                from ..core.schemas import validate_event
                validate_event(data)
            elif schema_name == "tick_metrics":
                from ..core.schemas import TickMetricsSchema
                TickMetricsSchema(**data)
            elif schema_name == "agent_snapshot":
                from ..core.schemas import AgentSnapshotSchema
                AgentSnapshotSchema(**data)
            else:
                # Unknown schema
                return False
            return True
        except Exception:
            return False
    
    def write_metadata(self, metadata: Dict[str, Any]) -> None:
        """Write metadata to a separate file.
        
        Args:
            metadata: Metadata dictionary
        """
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def get_output_paths(self) -> Dict[str, Path]:
        """Get paths to all output files.
        
        Returns:
            Dict mapping output type to file path
        """
        return {
            "ticks": self.ticks_path,
            "events": self.events_path,
            "final_agents": self.final_agents_path,
            "metadata": self.output_dir / "metadata.json"
        }
    
    def close(self) -> None:
        """Close the output writer and flush any pending data."""
        self.flush_ticks()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


class StreamingOutputWriter(OutputWriter):
    """Output writer that writes immediately without accumulation.
    
    Useful for long-running simulations where you want to see results
    as they happen.
    """
    
    def write_tick_json(self, tick_result: TickResult) -> None:
        """Write a tick result immediately to JSON.
        
        Args:
            tick_result: Tick result to write
        """
        if not self.config.json_ticks:
            return
        
        # Convert to dict
        tick_dict = tick_result.to_dict()
        
        # For streaming, we write each tick as a JSON line
        ticks_jsonl_path = self.output_dir / "ticks.jsonl"
        
        with open(ticks_jsonl_path, 'a', encoding='utf-8') as f:
            json.dump(tick_dict, f)
            f.write('\n')
    
    def flush_ticks(self) -> None:
        """No-op for streaming writer."""
        pass


def create_output_writer(output_dir: Path | str, config: OutputConfig,
                        metadata: Optional[Dict[str, Any]] = None,
                        streaming: bool = False) -> OutputWriter:
    """Factory function to create an output writer.
    
    Args:
        output_dir: Directory to write output files
        config: Output configuration
        metadata: Optional metadata to include in outputs
        streaming: If True, create a streaming writer
        
    Returns:
        OutputWriter instance
    """
    if streaming:
        return StreamingOutputWriter(output_dir, config, metadata)
    else:
        return OutputWriter(output_dir, config, metadata)


def generate_metadata(version: str, seed: int, config_hash: str,
                     additional: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate metadata dictionary for outputs.
    
    Args:
        version: M|inc version
        seed: Random seed used
        config_hash: Hash of configuration
        additional: Additional metadata fields
        
    Returns:
        Metadata dictionary
    """
    metadata = {
        "version": version,
        "seed": seed,
        "config_hash": config_hash,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "generator": "m_inc"
    }
    
    if additional:
        metadata.update(additional)
    
    return metadata
