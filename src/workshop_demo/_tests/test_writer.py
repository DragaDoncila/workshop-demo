import os
import numpy as np
from zipfile import ZipFile

from workshop_demo import labels_to_zip

def test_writing_single_layer(tmpdir, qtbot):
    layer_tuple = (
        np.random.randint(0, 255, (5, 100, 100)),
        {},
        'labels'
    )
    pth = os.path.join(str(tmpdir), 'test_labels.zip')
    labels_to_zip(pth, [layer_tuple])

    def check_zip():
        assert os.path.exists(pth)
        zip_file = ZipFile(pth)
        tiff_filenames = [info.filename for info in zip_file.infolist() if '.tif' in info.filename]
        assert len(tiff_filenames) == 5
        assert all(['01_AUTO/SEG/seg00' in fname for fname in tiff_filenames])

    # we use waitUntil to wait for the thread to finish without needing
    # its finished signal
    qtbot.waitUntil(check_zip)

def test_writing_returns_none(tmpdir):
    layer_tuple = (
        np.random.randint(0, 255, (100, 100)),
        {},
        'labels'
    )
    pth = os.path.join(str(tmpdir), 'test_labels.zip')
    assert labels_to_zip(pth, [layer_tuple]) is None

    layer_tuple2 = (
        np.random.randint(0, 255, (5, 100, 100)),
        {},
        'labels'
    )
    assert labels_to_zip(pth, [layer_tuple2, layer_tuple2]) is None   
