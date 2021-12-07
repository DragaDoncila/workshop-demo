"""
This module is an example of a barebones writer plugin for napari

It implements the ``napari_get_writer`` and ``napari_write_image`` hook specifications.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs
"""

from typing import List
from napari_plugin_engine import napari_hook_implementation
import os
from ._constants import SEQ_REGEX, GT_REGEX
import re
from tifffile import imsave
from shutil import make_archive
from napari.utils import progress
from napari.qt import thread_worker

# @napari_hook_implementation
def napari_get_writer(path: str, layer_types: List[str]):
    # we can only write labels or images to tiffs
    filtered_types = filter(lambda l_type: l_type == 'labels' or l_type == 'image', layer_types)
    if not filtered_types:
        return None

    # only writing to zip
    if not path.endswith('.zip'):
        return None

    return writer_function

@thread_worker(
    progress=True
)
def write_tiffs(data, dir_pth):
    for i, t_slice in enumerate(data):
        # write sequence of tiffs to folder
        tiff_nme = f't{str(i).zfill(3)}.tif'
        tiff_pth = os.path.join(dir_pth, tiff_nme)
        imsave(tiff_pth, t_slice)

def writer_function(path: str, layer_data_tuples: List["napari.types.LayerDataTuple"]) -> List[str]:
    if path.endswith('.zip'):
        path = path[:-4]

    layers_to_write = list(filter(lambda lyr: lyr[2] == 'labels' or lyr[2] == 'image', layer_data_tuples))
    
    os.mkdir(path)
    # for each layer
    for (data, meta, layer_type) in layers_to_write:
        # make folder with layer name name
        layer_dir_pth = os.path.join(path, meta['name'])
        os.mkdir(layer_dir_pth)
        if len(data.shape) == 2:
            data = [data]
        worker = write_tiffs(data, layer_dir_pth)
        worker.start()

    # zip folder (?)
    pth = make_archive(path, 'zip', path)
    return pth 
