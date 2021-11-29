import numpy as np
from nag_demo import napari_get_reader
from tifffile import imsave

# tmp_path is a pytest fixture
def test_reader(tmpdir):
    """An example of how you might test your plugin."""

    # write some fake data using your supported file format
    seq_pth = tmpdir.mkdir('01')
    gt_pth = tmpdir.mkdir('01_GT').mkdir('SEG')

    original_data = np.random.randint(0, 2**12, size=(100, 100), dtype=np.uint16)
    seq_tif = seq_pth.join('t000.tif')
    seq2_tif = seq_pth.join('t001.tif')
    imsave(str(seq_tif), original_data)
    imsave(str(seq2_tif), original_data)

    # try to read it back in
    reader = napari_get_reader(seq_pth)
    assert callable(reader)

    # make sure we're delivering the right format
    layer_data_list = reader(str(seq_pth))
    assert isinstance(layer_data_list, list) and len(layer_data_list) == 1
    layer_data_tuple = layer_data_list[0]
    assert isinstance(layer_data_tuple, tuple) and layer_data_tuple[2] == 'image'

    # make sure it's the same as it started
    layer_data = layer_data_tuple[0]
    assert layer_data.shape == (2, 100, 100)
    assert all([np.allclose(original_data, im_slice) for im_slice in layer_data])

def test_get_reader_seq_pass(tmpdir):
    """Valid dir of sequence tiffs"""
    seq = tmpdir.mkdir('01')
    seq.join('t000.tif').write('test')

    reader = napari_get_reader(seq)
    assert callable(reader)

def test_get_reader_gt_pass(tmpdir):
    """Valid dir of GT tiffs"""
    seq = tmpdir.mkdir('01_GT').mkdir('SEG')
    seq.join('man_seg000.tif').write('test')
    
    reader = napari_get_reader(seq)
    assert callable(reader)

def test_get_reader_not_dir_fail(tmpdir):
    """Not receiving a directory"""
    seq = tmpdir.mkdir('01').join('t000.tif')
    reader = napari_get_reader(seq)

    assert reader is None

def test_get_reader_wrong_dir_name_fail(tmpdir):
    """Directory incorrectly named"""
    seq = tmpdir.mkdir('foobar').join('t000.tif')
    reader = napari_get_reader(seq)

    assert reader is None
    
def test_get_reader_mix_tif_fail(tmpdir):
    """Directory ok but tifs are not named by expected sequence"""
    seq = tmpdir.mkdir('01')
    seq.join('t000.tif').write('test')
    seq.join('foobar.tif').write('test')

    reader = napari_get_reader(seq)
    assert reader is None

def test_get_reader_mix_dir_fail(tmpdir):
    """Directory is sequence but files are GT or vice versa"""
    seq = tmpdir.mkdir('01')
    seq.join('man_seg000.tif').write('test')
    reader = napari_get_reader(seq)
    assert reader is None

    seq = tmpdir.mkdir('01_GT')
    seq.join('t000.tif').write('test')
    reader = napari_get_reader(seq)
    assert reader is None

def test_get_reader_no_tif_fail(tmpdir):
    """Directory is ok but no tifs are present"""
    seq = tmpdir.mkdir('01')
    seq.join('not_a_tif.jpg').write('test')

    reader = napari_get_reader(seq)
    assert reader is None
