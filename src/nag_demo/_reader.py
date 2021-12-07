"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the ``napari_get_reader`` hook specification, (to create
a reader plugin) but your plugin may choose to implement any of the hook
specifications offered by napari.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below accordingly.  For complete documentation see:
https://napari.org/docs/dev/plugins/for_plugin_developers.html
"""
import warnings
from napari.utils import progress
import os
import glob
import re
import dask
import dask.array as da
from napari_plugin_engine import napari_hook_implementation
from pathlib import Path
import numpy as np
import tifffile

from ._constants import SEQ_REGEX, SEQ_TIF_REGEX, GT_REGEX, GT_TIF_REGEX

# @napari_hook_implementation
def napari_get_reader(path):
    """Returns reader if path contains valid tracking challenge tifs else None.

    Validates contents of path (which needs to be a directory) to either be
    test 2D+time sequences or segmentation Gold Standard Truth as per tracking
    challenge specifications:
    https://public.celltrackingchallenge.net/documents/Naming%20and%20file%20content%20conventions.pdf

    :param path: path to be opened by reader
    :type path: str
    :return: reader function or None
    """
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
    if not all_tifs:
        return None
        
    if not is_gt:
        is_seq_tifs = all([re.match(SEQ_TIF_REGEX, pth) for pth in all_tifs])
        if is_seq_tifs:
            return reader_function
        else:
            return None

    is_gt_tifs = all([re.match(GT_TIF_REGEX, pth) for pth in all_tifs])
    if not is_gt_tifs:
        return None

    return reader_function

@dask.delayed
def read_im(tif_pth):
    """Delayed func to read each individual tif into a numpy array"""
    with tifffile.TiffFile(tif_pth) as im_tif:
        im = im_tif.pages[0].asarray()
    return im

def read_tifs(path, tif_regex, n_frames):
    """Read all tifs at path matching tif_regex into delayed dask stack.

    If n_frames is given, places GT labels at the appropriate indices
    in the larger time sequence. Otherwise, reads labels into one
    contiguous sequence.

    :param path: path containing tifs
    :type path: str
    :param tif_regex: regex matching GT or sequence tracking chalenge tiffs
    :type tif_regex: regex str
    :param n_frames: number of total frames in the sequence
    :type n_frames: int
    :return: nd dask array
    """
    # TODO: if we take more than one sequence
    # read tifs using tifffile.open etc. in a dask delayed function
    all_tifs = sorted([pth for pth in glob.glob(path + '/*.tif') if re.match(tif_regex, pth)])
    tif_shape = None
    tif_dtype = None
    with tifffile.TiffFile(all_tifs[0]) as im_tif:
        tif_shape = im_tif.pages[0].shape
        tif_dtype = im_tif.pages[0].dtype

    # each tiff needs to be stacked into a big dask array
    if not n_frames:
        n_frames = len(all_tifs)
    im_stack = [np.zeros(shape=tif_shape, dtype=tif_dtype) for _ in range(n_frames)]

    for tif_pth in progress(all_tifs):
        frame_index = int(re.match(tif_regex, tif_pth).groups()[-1])
        im = da.from_delayed(read_im(tif_pth), shape=tif_shape, dtype=tif_dtype)
        im_stack[frame_index] = im
    layer_data = da.stack(im_stack)

    return layer_data

def reader_function(path):
    """Reads valid tracking challenge tifs at path into napari as layers.

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

    gt_match = re.match(GT_REGEX, path)
    is_gt = bool(gt_match)

    max_frames = None
    layer_type = "image"
    pth_regex = SEQ_TIF_REGEX
    layer_name = "tracking_data"
    if is_gt:
        # we need to know the number of frames to spread this over, so we look for the sister sequence
        parent_dir_pth = Path(path).parent.parent.absolute()
        sister_sequence_pth = os.path.join(parent_dir_pth, gt_match.groups()[1])
        if not os.path.exists(sister_sequence_pth):
            warnings.warn(f"Can't find image for ground truth at {path}. Reading without knowing number of frames...")
        else:
            latest_tif_pth = sorted(glob.glob(sister_sequence_pth + '/*.tif'))[-1]
            max_frames = int(re.match(SEQ_TIF_REGEX, latest_tif_pth).groups()[-1]) + 1
        layer_type = "labels"
        pth_regex = GT_TIF_REGEX
        layer_name = 'ground_truth'

    layer_data = read_tifs(path, pth_regex, max_frames)

    # optional kwargs for the corresponding viewer.add_* method
    add_kwargs = {'name': layer_name}

    return [(layer_data, add_kwargs, layer_type)]
