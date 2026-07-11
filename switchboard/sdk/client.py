from typing import Any
from switchboard.kernel.kernel import Kernel
from switchboard.logging.config import get_logger

logger = get_logger("sdk_client")

class SwitchBoardClient:
    """
    High-level SDK Client for external applications to interface with the 
    SwitchBoard platform.
    """

    def __init__(self, kernel: Kernel | None = None) -> None:
        self._kernel = kernel

    async def get_status(self) -> dict[str, Any]:
        """
        Retrieve operational status of the platform.
        """
        if self._kernel:
            return {
                "status": "connected",
                "kernel_state": self._kernel.state.value,
                "version": self._kernel.settings.version
            }
        return {
            "status": "detached",
            "message": "Detached SDK client. No local kernel context available."
        }

    async def execute_task(self, task_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Request task execution from the platform kernel.
        """
        logger.info("SDK client request to execute task", task_id=task_id)
        if self._kernel:
            return {
                "task_id": task_id,
                "status": "queued",
                "kernel_state": self._kernel.state.value
            }
        return {
            "task_id": task_id,
            "status": "failed",
            "reason": "No active kernel connection"
        }
