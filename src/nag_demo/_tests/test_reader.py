import numpy as np
from nag_demo import napari_get_reader


# # tmp_path is a pytest fixture
# def test_reader(tmp_path):
#     """An example of how you might test your plugin."""

#     # write some fake data using your supported file format
#     my_test_file = str(tmp_path / "myfile.npy")
#     original_data = np.random.rand(20, 20)
#     np.save(my_test_file, original_data)

#     # try to read it back in
#     reader = napari_get_reader(my_test_file)
#     assert callable(reader)

#     # make sure we're delivering the right format
#     layer_data_list = reader(my_test_file)
#     assert isinstance(layer_data_list, list) and len(layer_data_list) > 0
#     layer_data_tuple = layer_data_list[0]
#     assert isinstance(layer_data_tuple, tuple) and len(layer_data_tuple) > 0

#     # make sure it's the same as it started
#     np.testing.assert_allclose(original_data, layer_data_tuple[0])

def test_get_reader_seq_pass(tmpdir):
    """Valid dir of sequence tiffs"""
    seq = tmpdir.mkdir('01')
    seq.join('000.tif')

    reader = napari_get_reader(seq)
    assert callable(reader)

def test_get_reader_gt_pass(tmpdir):
    """Valid dir of GT tiffs"""
    seq = tmpdir.mkdir('01_GT').mkdir('SEG')
    seq.join('man_seg000.tif')
    
    reader = napari_get_reader(seq)
    assert callable(reader)

def test_get_reader_not_dir_fail(tmpdir):
    """Not receiving a directory"""
    seq = tmpdir.mkdir('01').join('000.tif')
    reader = napari_get_reader(seq)

    assert reader is None

def test_get_reader_wrong_dir_name_fail(tmpdir):
    """Directory incorrectly named"""
    seq = tmpdir.mkdir('foobar').join('000.tif')
    reader = napari_get_reader(seq)

    assert reader is None
    
def test_get_reader_mix_tif_fail(tmpdir):
    seq = tmpdir.mkdir('01')
    seq.join('000.tif').write('test')
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
    seq.join('000.tif').write('test')
    reader = napari_get_reader(seq)
    assert reader is None

def test_get_reader_no_tif_fail(tmpdir):
    pass
