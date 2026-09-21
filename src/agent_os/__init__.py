"""Personal Agent OS core package."""

__version__ = "0.1.0"


def run(*args, **kwargs):
    """Execute a controlled worker through the Agent OS lifecycle."""
    from .gateway import run as gateway_run
    return gateway_run(*args, **kwargs)
