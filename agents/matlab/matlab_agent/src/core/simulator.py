from __future__ import annotations

"""Unified MATLAB simulation interface and implementations."""

from abc import ABC, abstractmethod
import threading
from typing import Any, Dict, Optional

from ..comm.interfaces import IMessageBroker
from .batch import handle_batch_simulation
from .streaming import handle_streaming_simulation
from .interactive import handle_interactive_simulation


class MatlabSimulator(ABC):
    """Abstract base class for MATLAB simulations."""

    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()

    def start(self) -> None:
        """Start the simulation in a separate thread."""
        if self._running.is_set():
            return
        self._running.set()
        self._thread = threading.Thread(target=self._execute, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the simulation to stop."""
        self._running.clear()

    def is_running(self) -> bool:
        """Check if the simulation thread is active."""
        return self._running.is_set()

    @abstractmethod
    def _execute(self) -> None:
        """Execute the simulation logic."""


class BatchSimulator(MatlabSimulator):
    """Run MATLAB batch simulations."""

    def __init__(
        self,
        msg_dict: Dict[str, Any],
        source: str,
        broker: IMessageBroker,
        path_simulation: str,
        response_templates: Dict[str, Any],
    ) -> None:
        super().__init__()
        self.msg_dict = msg_dict
        self.source = source
        self.broker = broker
        self.path = path_simulation
        self.templates = response_templates

    def _execute(self) -> None:  # pragma: no cover - thin wrapper
        handle_batch_simulation(
            self.msg_dict, self.source, self.broker, self.path, self.templates
        )
        self.stop()


class StreamingSimulator(MatlabSimulator):
    """Run MATLAB streaming simulations."""

    def __init__(
        self,
        msg_dict: Dict[str, Any],
        source: str,
        broker: IMessageBroker,
        path_simulation: str,
        response_templates: Dict[str, Any],
        tcp_settings: Dict[str, Any],
    ) -> None:
        super().__init__()
        self.msg_dict = msg_dict
        self.source = source
        self.broker = broker
        self.path = path_simulation
        self.templates = response_templates
        self.tcp = tcp_settings

    def _execute(self) -> None:  # pragma: no cover - thin wrapper
        handle_streaming_simulation(
            self.msg_dict,
            self.source,
            self.broker,
            self.path,
            self.templates,
            self.tcp,
        )
        self.stop()


class InteractiveSimulator(MatlabSimulator):
    """Run MATLAB interactive simulations."""

    def __init__(
        self,
        msg_dict: Dict[str, Any],
        source: str,
        broker: IMessageBroker,
        path_simulation: str,
        response_templates: Dict[str, Any],
        tcp_settings: Dict[str, Any],
    ) -> None:
        super().__init__()
        self.msg_dict = msg_dict
        self.source = source
        self.broker = broker
        self.path = path_simulation
        self.templates = response_templates
        self.tcp = tcp_settings

    def _execute(self) -> None:  # pragma: no cover - thin wrapper
        handle_interactive_simulation(
            self.msg_dict,
            self.source,
            self.broker,
            self.path,
            self.templates,
            self.tcp,
        )
        self.stop()
