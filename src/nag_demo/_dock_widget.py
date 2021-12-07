"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
from typing import List
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel
from napari_plugin_engine import napari_hook_implementation
from napari.utils import progress
import numpy as np
from qtpy.QtWidgets import QWidget, QVBoxLayout, QPushButton
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
import dask.array as da

class Threshold(Enum):
    isodata = partial(threshold_isodata)
    li = partial(threshold_li)
    otsu = partial(threshold_otsu)
    triangle = partial(threshold_triangle)
    yen = partial(threshold_yen)

@magic_factory
def segment_by_threshold(img_layer: "napari.layers.Image", threshold: Threshold) -> "napari.types.LayerDataTuple":
    with progress(total=0):
        threshold_val = threshold.value(img_layer.data.compute())
        binarised_im = img_layer.data > threshold_val
        seg_labels = da.from_array(label(binarised_im))

    seg_layer = (
        seg_labels,
        {'name': f'{img_layer.name}_seg'},
        'labels'
    )

    return seg_layer

class SegmentationDiffHighlight(QWidget):

    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.setLayout(QVBoxLayout())

        highlight_btn = QPushButton("Highlight Differences")
        highlight_btn.clicked.connect(self._compute_differences)

        self.layer_combos = []
        self.gt_layer_combo = self.get_layer_combo_box('Ground Truth Layer')
        self.seg_layer_combo = self.get_layer_combo_box('Segmentation Layer')
        self.viewer.layers.events.inserted.connect(self._reset_layer_options)
        self.viewer.layers.events.removed.connect(self._reset_layer_options)

        self.layout().addWidget(highlight_btn)
        self.layout().addStretch()

    def get_layer_combo_box(self, label_text):
        combo_row = QWidget()
        combo_row.setLayout(QHBoxLayout())
        combo_row.layout().setContentsMargins(0, 0, 0, 0)

        new_combo_label = QLabel(label_text)
        combo_row.layout().addWidget(new_combo_label)

        new_layer_combo = QComboBox(self)
        new_layer_combo.addItems([layer.name for layer in self.viewer.layers])
        combo_row.layout().addWidget(new_layer_combo)

        self.layer_combos.append(new_layer_combo)
        self.layout().addWidget(combo_row)

        return new_layer_combo

    def _compute_differences(self):
        gt_layer = self.viewer.layers[self.gt_layer_combo.currentText()]
        seg_layer = self.viewer.layers[self.seg_layer_combo.currentText()]

        truth_foreground = da.where(gt_layer.data != 0, 1, 0)
        seg_foreground = da.where(seg_layer.data != 0, 1, 0)

        for i in range(len(truth_foreground)):
            if np.count_nonzero(truth_foreground[i]) == 0:
                # we want to zero out any slices with no ground truth
                seg_foreground[i] = da.zeros(truth_foreground[i].shape)

        diff = da.where(truth_foreground != seg_foreground, 1, 0)  

        gt_layer.visible = False
        seg_layer.visible = False
        self.viewer.add_labels(diff, name='seg_gt_diff', color={1: 'red'})

    def _reset_layer_options(self, event):
        for combo in self.layer_combos:
            combo.clear()
            combo.addItems([layer.name for layer in self.viewer.layers])
    # make npe2 dock widget 
    # document
    # test

# @napari_hook_implementation(specname='napari_experimental_provide_dock_widget')
def get_segment_widget():
    return segment_by_threshold 
    
def get_highlight_widget():
    return SegmentationDiffHighlight
