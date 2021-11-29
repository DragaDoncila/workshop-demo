"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the ``napari_get_reader`` hook specification, (to create
a reader plugin) but your plugin may choose to implement any of the hook
specifications offered by napari.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below accordingly.  For complete documentation see:
https://napari.org/docs/dev/plugins/for_plugin_developers.html
"""
import numpy as np
from napari_plugin_engine import napari_hook_implementation
from napari.utils import progress
import os
import glob
import re
SEQ_REGEX = r'(.*)/([0-9]{2,})'
GT_REGEX = r'(.*)/([0-9]{2,})_GT/SEG'

SEQ_TIF_REGEX = rf'{SEQ_REGEX}/(t[0-9]{{3}}\.tif)'
GT_TIF_REGEX = rf'{GT_REGEX}/(man_seg[0-9]{{3}}\.tif)'

# @napari_hook_implementation
def napari_get_reader(path):    
    print("GETTING READER")
    # TODO: if we return None when opening with specific plugin, error is "no plugin registered named foobar?"
    # return None

    path = os.path.abspath(path)
    # we want a folder not an individual tiff
    if not os.path.isdir(path):
        return None

    # dirname either a sequence or a GT/SEG
    is_gt = re.match(GT_REGEX, path)
    if not is_gt:
        is_seq = re.match(SEQ_REGEX, path)
        if not is_seq:
            return None

    # need to be able to find either sequence tifs or seg GT tifs
    all_tifs = glob.glob(path + '/*.tif')
    if not is_gt:
        is_seq_tifs = all([re.match(SEQ_TIF_REGEX, pth) for pth in all_tifs])
        if not is_seq_tifs:
            return None

    is_gt_tifs = all([re.match(GT_TIF_REGEX, pth) for pth in all_tifs])
    if not is_gt_tifs:
        return None

    return reader_function


def reader_function(path):
    """Take a path or list of paths and return a list of LayerData tuples.

    Readers are expected to return data as a list of tuples, where each tuple
    is (data, [add_kwargs, [layer_type]]), "add_kwargs" and "layer_type" are
    both optional.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of layer.
        Both "meta", and "layer_type" are optional. napari will default to
        layer_type=="image" if not provided
    """
    print("READING")

    # optional kwargs for the corresponding viewer.add_* method
    add_kwargs = {}

    layer_type = "image"  # optional, default is "image"
    data = np.random.random((100, 100))
    return [(data, add_kwargs, layer_type)]
