from dataclasses import dataclass

@dataclass
class StartMessage:
    name:str = "START"
    
@dataclass
class Bar30DataStruct:
    name: str = "BAR_30_DATA"
    temperature : float = -99.99 #celsius float
    pressure: float = -99.99 #mbar float

@dataclass
class SetFluidDensityStruct:
    name: str = "SET_FLUID_DENSITY"
    density : float = 997.0 # Provide the density of the working fluid in kg/m^3. Default is for seawater. Should be 997 for freshwater.

@dataclass
class InitBarSensorStruct:
    name : str = "INIT_BAR_30"
    
@dataclass
class CheckInitBarSensorStruct:
    name : str = "CHECK_BAR_30"
    
@dataclass
class PingArduinoStruct:
    name : str = "PING_ARDUINO"
    
@dataclass
class LeakSensorDataStruct:
    name : str = "LEAK_SENSOR_DATA"
    leak : bool = 0.0
    
@dataclass
class LeftJoystickForwardY:
    name : str = "FORWARD_Y"
    scale : float = 0.0
    
@dataclass
class LeftJoystickBackwardY:
    name : str "BACKWARD_Y"
    scale : float = 0.0
    
@dataclass
class LeftJoystickLeftX:
    name : str "LEFT_X"
    scale : float = 0.0
    
@dataclass 
class LeftJoystickRightX:
    name :str "RIGHT_X"
    scale : float = 0.0
    
@dataclass
class 