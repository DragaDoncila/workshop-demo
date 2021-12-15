try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._dock_widget import SegmentationDiffHighlight, Threshold, segment_by_threshold
from ._reader import napari_get_reader
from ._writer import labels_to_zip

__all__ = [
    "napari_get_reader",
    "labels_to_zip",
    "segment_by_threshold",
    "SegmentationDiffHighlight",
    "Threshold",
]
