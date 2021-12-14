
try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"


from ._reader import napari_get_reader
from ._writer import labels_to_zip
from ._dock_widget import segment_by_threshold, SegmentationDiffHighlight, Threshold

