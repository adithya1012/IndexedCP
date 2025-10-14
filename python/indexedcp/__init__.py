"""
IndexedCP Python Client

A Python implementation of the IndexedCP client for secure, efficient, and resumable file transfer.
Compatible with the Node.js IndexedCP server.
"""

from .client import IndexCPClient

__version__ = "1.0.0"
__all__ = ["IndexCPClient"]