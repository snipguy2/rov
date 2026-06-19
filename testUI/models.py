# models.py
from dataclasses import dataclass, fields

@dataclass(frozen=True)
class SensorReadings:
    """Immutable structural container for hardware metric snapshots.
    
    Add or remove fields here, and the UI adapts automatically.
    """
    timestamp: str
    temperature: float
    humidity: float
    pressure: float
    voltage: float       # Added to demonstrate dynamic view expansion
    air_quality: float   # Added to demonstrate dynamic view expansion

    @property
    def csv_header(self) -> list[str]:
        """Dynamically generates header titles based on dataclass field names."""
        return [f.name.capitalize() for f in fields(self)]

    @property
    def csv_row(self) -> list[str]:
        """Dynamically builds a text-ready row string list for any schema length."""
        row_data = []
        for f in fields(self):
            val = getattr(self, f.name)
            # Format floating-point values cleanly to two decimal places
            row_data.append(f"{val:.2f}" if isinstance(val, float) else str(val))
        return row_data
