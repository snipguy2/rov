# models.py
from dataclasses import dataclass, fields
from typing import Optional

@dataclass(frozen=True)
class SensorReadings:
    """Immutable structural container for hardware metric snapshots.
    
    Using Optional allows individual sensors to report 'None' if they fail,
    without bringing down the entire data packet.
    """
    timestamp: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    voltage: Optional[float] = None       
    air_quality: Optional[float] = None   

    @property
    def csv_header(self) -> list[str]:
        return [f.name.capitalize() for f in fields(self)]

    @property
    def csv_row(self) -> list[str]:
        row_data = []
        for f in fields(self):
            val = getattr(self, f.name)
            # Handle missing data cleanly in the CSV output
            if val is None:
                row_data.append("N/A")
            else:
                row_data.append(f"{val:.2f}" if isinstance(val, float) else str(val))
        return row_data
    
@dataclass(frozen=True)
class ROVCommand:
    """Structure for thruster signals sent to the ROV."""
    timestamp: str
    thruster_values: list[float]  # [T1, T2, T3, T4, T5, T6, T7, T8]
    
    @property
    def csv_header(self) -> list[str]:
        return [f.name.capitalize() for f in fields(self)]

    @property
    def csv_row(self) -> list[str]:
        row_data = []
        for f in fields(self):
            val = getattr(self, f.name)
            # Handle missing data cleanly in the CSV output
            if val is None:
                row_data.append("N/A")
            else:
                row_data.append(f"{val:.2f}" if isinstance(val, float) else str(val))
        return row_data