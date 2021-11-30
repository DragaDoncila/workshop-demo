"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
from napari_plugin_engine import napari_hook_implementation
from napari.utils import progress
from qtpy.QtWidgets import QWidget, QHBoxLayout, QPushButton
from magicgui import magic_factory
from enum import Enum
from skimage.filters import (
    threshold_isodata,
    threshold_li,
    threshold_otsu,
    threshold_triangle,
    threshold_yen,
)
from functools import partial

class Threshold(Enum):
    isodata = partial(threshold_isodata)
    li = partial(threshold_li)
    otsu = partial(threshold_otsu)
    triangle = partial(threshold_triangle)
    yen = partial(threshold_yen)

@magic_factory
def thresholding(img_layer: "napari.layers.Image", threshold: Threshold) -> "napari.types.LayerDataTuple":
    with progress(total=0):
        threshold_val = threshold.value(img_layer.data.compute())
        binarised_im = img_layer.data > threshold_val

    return (binarised_im, {'name': f'{img_layer.name}_binarised', 'opacity': 0.25}, 'image')


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return [thresholding]
