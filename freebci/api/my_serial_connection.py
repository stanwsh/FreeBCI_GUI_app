"""Compatibility alias for the asynchronous serial connection dialog.

The original synchronous implementation prepared a BrainFlow board in the GUI
thread and is intentionally gone.  Import the worker-backed dialog instead.
"""
from freebci.api.my_serial_connection_pure import MySerialConnection

__all__ = ["MySerialConnection"]
