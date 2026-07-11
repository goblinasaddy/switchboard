from enum import Enum

class KernelState(str, Enum):
    """
    Enum representing the operational phases of the SwitchBoard Kernel lifecycle.
    """
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
