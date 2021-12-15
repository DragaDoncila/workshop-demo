"""
This module contains two barebones widgets for use as napari dock widgets.

One is built using magic_factory, abstracting away a lot of the complexity of
managing the layout and basic functionality of your widget.

The second is built by subclassing QWidget directly. It provides a lot of
flexibility for complex functionality, but requires more careful management
and, of course, more code.
"""
import numpy as np
import dask.array as da
from qtpy.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget, QVBoxLayout, QPushButton
from magicgui import magic_factory
from enum import Enum
from skimage.filters import (
    threshold_isodata,
    threshold_li,
    threshold_otsu,
    threshold_triangle,
    threshold_yen,
)
from skimage.measure import label
from functools import partial
from napari.utils import progress
from napari.layers import Labels

class Threshold(Enum):
    # plain functions can't be Enum members, so we wrap these in partial
    # this doesn't change their behaviour
    isodata = partial(threshold_isodata)
    li = partial(threshold_li)
    otsu = partial(threshold_otsu)
    triangle = partial(threshold_triangle)
    yen = partial(threshold_yen)

# our manifest widget command points to this function
@magic_factory
def segment_by_threshold(img_layer: "napari.layers.Image", threshold: Threshold) -> "napari.types.LayerDataTuple":
    """Returns segmented labels layer given an image layer and threshold function.

    Magicgui widget providing access to five scikit-image threshold functions
    and layer selection using a combo box. Layer is segmented based on threshold choice.

    Returns
    -------
    napari.types.LayerDataTuple
        tuple of (data, meta, 'labels') for consumption by napari
    """
    with progress(total=0):
        # need to use threshold.value to get the function from the enum member
        threshold_val = threshold.value(img_layer.data.compute())
        binarised_im = img_layer.data > threshold_val
        seg_labels = da.from_array(label(binarised_im))

    seg_layer = (
        seg_labels,
        {'name': f'{img_layer.name}_seg'},
        'labels'
    )

    return seg_layer

# our manifest widget command points to this class
class SegmentationDiffHighlight(QWidget):
    """Widget allows selection of two labels layers and returns a new layer
    highlighing pixels whose values differ between the two layers."""

    def __init__(self, napari_viewer):
        """Initialize widget with two layer combo boxes and a run button

        Parameters
        ----------
        napari_viewer : napari.utils._proxies.PublicOnlyProxy   
            public proxy for the napari viewer object
        """
        super().__init__()
        self.viewer = napari_viewer
        self.setLayout(QVBoxLayout())

        # make button for differences
        self.highlight_btn = QPushButton("Highlight Differences")
        self.highlight_btn.clicked.connect(self._compute_differences)

        # make two combo boxes for selecting labels layers
        self.layer_combos = []
        self.gt_layer_combo = self.add_labels_combo_box('Ground Truth Layer')
        self.seg_layer_combo = self.add_labels_combo_box('Segmentation Layer')

        # if the user adds or removes layers we want to update the combo box
        self.viewer.layers.events.inserted.connect(self._reset_layer_options)
        self.viewer.layers.events.removed.connect(self._reset_layer_options)

        self.layout().addWidget(self.highlight_btn)
        self.layout().addStretch()

    def add_labels_combo_box(self, label_text):
        """Add combo box with the given label_text and labels layers as items  

        Parameters
        ----------
        label_text : str
            Text to add next to combo box

        Returns
        -------
        QComboBox
            Combo box with labels layers as items
        """

        # make a new row to put label and combo box in
        combo_row = QWidget()
        combo_row.setLayout(QHBoxLayout())
        # we don't want margins so it looks all tidy
        combo_row.layout().setContentsMargins(0, 0, 0, 0)

        new_combo_label = QLabel(label_text)
        combo_row.layout().addWidget(new_combo_label)

        new_layer_combo = QComboBox(self)
        # only adding labels layers
        new_layer_combo.addItems([layer.name for layer in self.viewer.layers if isinstance(layer, Labels)])
        combo_row.layout().addWidget(new_layer_combo)

        # saving to a list so we can iterate through all combo boxes to reset choices
        self.layer_combos.append(new_layer_combo)
        self.layout().addWidget(combo_row)

        # returning the combo box so we know which is which when we click run
        return new_layer_combo

    def _compute_differences(self):
        """Get layers selected by user and compute pixel by pixel difference
        """

        # grab the layer using the combo box item text as the layer name
        gt_layer = self.viewer.layers[self.gt_layer_combo.currentText()]
        seg_layer = self.viewer.layers[self.seg_layer_combo.currentText()]
        
        # find the non-zero labels in each layer
        truth_foreground = da.where(gt_layer.data != 0, 1, 0)
        seg_foreground = da.where(seg_layer.data != 0, 1, 0)

        for i in range(len(truth_foreground)):
            if np.count_nonzero(truth_foreground[i]) == 0:
                # we want to zero out any slices with no ground truth
                seg_foreground[i] = da.zeros(truth_foreground[i].shape)

        # where they're not equal, we need to highlight
        diff = da.where(truth_foreground != seg_foreground, 1, 0)  

        gt_layer.visible = False
        seg_layer.visible = False
        self.viewer.add_labels(diff, name='seg_gt_diff', color={1: '#fca503'})

    def _reset_layer_options(self, event):
        """Clear existing combo boxes and repopulate

        Parameters
        ----------
        event : event
            Clear existing combo box items and query viewer for all labels layers
        """
        for combo in self.layer_combos:
            combo.clear()
            combo.addItems([layer.name for layer in self.viewer.layers if isinstance(layer, Labels)])
