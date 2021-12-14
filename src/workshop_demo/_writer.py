"""
This module is an example of a barebones writer plugin for napari
"""

from typing import List
import os
from tifffile import imsave
from shutil import make_archive, rmtree
from napari.qt import thread_worker

@thread_worker(
    # give us an indeterminate progress bar
    progress=True
)
def write_tiffs(data, dir_pth):
    """Given 2D+T data array, write each slice to individual tif.

    This operation is threaded.

    Parameters
    ----------
    data : ArrayLike
        2D+T data to write to files 
    dir_pth : str
        path to existing folder to hold tiffs
    """
    for i, t_slice in enumerate(data):
        tiff_nme = f'seg{str(i).zfill(3)}.tif'
        tiff_pth = os.path.join(dir_pth, tiff_nme)
        imsave(tiff_pth, t_slice)


def labels_to_zip(path: str, layer_data_tuples: List["napari.types.LayerDataTuple"]) -> List[str]:
    """Save all 2D+T labels layers folder of individual 2D tiffs and zip. 

    Parameters
    ----------
    path : str
        path to save layers to
    layer_data_tuples : List[napari.types.LayerDataTuple]
        list of (data, meta, layer_type) layer tuples to save

    Returns
    -------
    List[str] | None
        path to save to or None if layers can't be saved
    """

    # strip file extension so we can make directory
    if path.endswith('.zip'):
        path = path[:-4]

    layers_to_write = list(filter(lambda lyr: lyr[2] == 'labels', layer_data_tuples))

    # we need each layer's data to be 3D
    if not all([layer_tuple[0].ndim == 3 for layer_tuple in layers_to_write]):
        return None
    
    # we will use this function to zip up the folder once all tiffs are written
    def zip_dir():
        """Make zip file from directory at path"""
        make_archive(path, 'zip', path)
        # clean up directory after ourselves
        rmtree(path)    

    os.mkdir(path)
    for (data, meta, layer_type) in layers_to_write:
        # use correct folder structure so that our reader can read it
        layer_dir_pth = os.path.join(path, f'01_AUTO/SEG')
        os.makedirs(layer_dir_pth)
        if len(data.shape) == 2:
            data = [data]
        worker = write_tiffs(data, layer_dir_pth)
        worker.start()
        # once this worker is done we zip up the folder
        worker.finished.connect(zip_dir)

    # returning path even though worker may not be finished - cheeky...
    return path + '.zip'
