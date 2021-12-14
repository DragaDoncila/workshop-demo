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
from pathlib import Path
import numpy as np
import tifffile

from ._constants import SEQ_TIF_REGEX, GT_REGEX, GT_TIF_REGEX

def napari_get_reader(path):
    """Returns reader if path contains valid tracking challenge ground truth tifs, otherwise None.

    Validates contents of path (which needs to be a directory) to be
    test 2D+time segmentation Gold Standard Truth tiffs as per tracking
    challenge specifications:
    https://public.celltrackingchallenge.net/documents/Naming%20and%20file%20content%20conventions.pdf

    :param path: path to be opened by reader
    :type path: str
    :return: reader function or None
    """
    # TODO: if we return None when opening with specific plugin, error is "no plugin registered named foobar?"
    # return None

    path = os.path.abspath(path)
    # we want a folder not an individual tiff
    if not os.path.isdir(path):
        return None

    # directory name needs to match the ground truth regex
    is_gt = re.match(GT_REGEX, path)
    if not is_gt:
        return None

    # need to be able to find some tifs
    all_tifs = glob.glob(path + '/*.tif')
    if not all_tifs:
        return None
    
    # the tifs we've found need to match the regex for a ground truth tif
    is_gt_tifs = all([re.match(GT_TIF_REGEX, pth) for pth in all_tifs])
    if not is_gt_tifs:
        return None

    return reader_function

def read_tifs(path, n_frames):
    """Read all tifs at path matching tif_regex into delayed dask stack.

    If n_frames is given, places GT labels at the appropriate indices
    in the larger time sequence. Otherwise, reads labels into one
    contiguous sequence.

    :param path: path containing tifs
    :type path: str
    :param n_frames: number of total frames in the sequence
    :type n_frames: int
    :return: nd dask array
    """

    # sort all the tifs found at path that match the regex
    all_tifs = sorted([pth for pth in glob.glob(path + '/*.tif') if re.match(GT_TIF_REGEX, pth)])

    # open and inspect the first file so we can give a shape and dtype to the dask array
    tif_shape = None
    tif_dtype = None
    with tifffile.TiffFile(all_tifs[0]) as im_tif:
        tif_shape = im_tif.pages[0].shape
        tif_dtype = im_tif.pages[0].dtype

    # if we haven't been given a number of frames we just read the whole folder
    if not n_frames:
        n_frames = len(all_tifs)
    im_stack = [da.zeros(shape=tif_shape, dtype=tif_dtype) for _ in range(n_frames)]

    @dask.delayed
    def read_im(tif_pth):
        """Delayed func to read each individual tif into a numpy array"""
        with tifffile.TiffFile(tif_pth) as im_tif:
            im = im_tif.pages[0].asarray()
        return im

    for tif_pth in progress(all_tifs):
        # get the slice index from the name of the file
        frame_index = int(re.match(GT_TIF_REGEX, tif_pth).groups()[-1])
        im = da.from_delayed(read_im(tif_pth), shape=tif_shape, dtype=tif_dtype)
        # assign what we read into the stack at the right spot
        im_stack[frame_index] = im
    layer_data = da.stack(im_stack)

    return layer_data

def reader_function(path):
    """Reads valid tracking challenge ground truth tifs at path and returns as napari layers.

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
        tuples of (layer_data, meta, layer_type) where layer_data is a dask array,
        meta contains metadata for the layer and layer_type is labels
    """
    path = os.path.normpath(path)
    gt_match = re.match(GT_REGEX, path)

    # we need to know the number of frames to spread this over, so we look for the sister sequence
    parent_dir_pth = Path(path).parent.parent.absolute()
    # get the sequence number for this ground truth data
    seq_number = gt_match.groups()[1]
    sister_sequence_pth = os.path.join(parent_dir_pth, seq_number)

    n_frames = None
    if not os.path.exists(sister_sequence_pth):
        warnings.warn(f"Can't find image for ground truth at {path}. Reading without knowing number of frames...")
    else:
        # find the last tif in the sequence so we can work out the number of frames
        latest_tif_pth = sorted(glob.glob(sister_sequence_pth + '/*.tif'))[-1]
        # split the number out of the filename and add 1 because we start at 0
        n_frames = int(re.match(SEQ_TIF_REGEX, latest_tif_pth).groups()[-1]) + 1

    layer_data = read_tifs(path, n_frames)
    layer_type = "labels"
    layer_name = f"{gt_match.group(2)}{gt_match.group(3)}"

    # optional kwargs for the corresponding viewer.add_* method 
    #    e.g. name, colormap, scale, etc.
    add_kwargs = {'name': layer_name}

    return [(layer_data, add_kwargs, layer_type)]
