from switchboard.types.common import BaseEvent
from switchboard.kernel.state import KernelState

class LifecycleEvent(BaseEvent):
    """
    Event emitted when the SwitchBoard platform transitions between lifecycle states.
    """
    def __init__(self, from_state: KernelState, to_state: KernelState, details: str = "") -> None:
        super().__init__(
            payload={
                "from_state": from_state.value,
                "to_state": to_state.value,
                "details": details
            }
        )

    @property
    def from_state(self) -> KernelState:
        return KernelState(self.payload["from_state"])

    @property
    def to_state(self) -> KernelState:
        return KernelState(self.payload["to_state"])

    @property
    def details(self) -> str:
        return self.payload["details"]


class ServiceLifecycleEvent(BaseEvent):
    """
    Event emitted when a managed service transitions its lifecycle state.
    """
    def __init__(self, service_name: str, action: str, success: bool = True, error_msg: str | None = None) -> None:
        super().__init__(
            payload={
                "service_name": service_name,
                "action": action,  # "initialize", "start", "shutdown"
                "success": success,
                "error_msg": error_msg
            }
        )

    @property
    def service_name(self) -> str:
        return self.payload["service_name"]

    @property
    def action(self) -> str:
        return self.payload["action"]

    @property
    def success(self) -> bool:
        return self.payload["success"]

    @property
    def error_msg(self) -> str | None:
        return self.payload["error_msg"]
