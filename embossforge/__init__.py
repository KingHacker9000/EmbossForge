"""EmbossForge: parametric embossing tools."""

from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version("embossforge")
except PackageNotFoundError:  # pragma: no cover - direct source import before installation
    __version__ = "0.1.0"
