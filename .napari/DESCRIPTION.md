## What is this?

This plugin was created to serve as a semi-meaningful example of a plugin using
the new napari [npe2](https://pypi.org/project/npe2/) architecture.

It provides a reader, a writer and two dock widgets to support opening, processing
and writing out [cell tracking challenge](https://celltrackingchallenge.net/) data.

We've provided comments and example tests that can be used as a reference
when building your own plugin.

## Using this plugin

### Sample Data
You can download sample data for this plugin from the tracking challenge website. Any 2D+T
sequence should work, but this plugin has been tested only with the 
[Human hepatocarcinoma-derived cells expressing the fusion protein YFP-TIA-1](http://data.celltrackingchallenge.net/training-datasets/Fluo-C2DL-Huh7.zip) 
dataset.
### Reading Data
This plugin's reader is designed for tracking challenge segmentation gold standard ground truth
data conforming to the file format described in the [data specification](https://public.celltrackingchallenge.net/documents/Naming%20and%20file%20content%20conventions.pdf).

Ground truth data is only provided for a subset of the frames of the entire sequence. This
reader will attempt to find the number of frames of the associated sequence in a sister
directory of the ground truth data directory and open a labels layer with the same number
of frames, thus ensuring the labelled data is correctly overlaid onto the original sequence.

<!-- Movie here -->

### Segmenting Data
One of the dock widgets provided by this plugin is "Segment by Threshold". The widget
allows you to select a 2D+T image layer in the viewer (e.g. any of the sequences in the Human 
hepatocarcinoma dataset above) and segment it using a selection of scikit-image thresholding functions.

The segmentation is then returned as a `Labels` layer into the viewer.

<!-- Movie here -->

### Highlighting Segmentation Differences
The second dock widget provided by this plugin allows you to visually compare your segmentation
against the ground truth data by computing the difference between the two and adding this as a
layer in the napari viewer.

To use this widget, open it from the Plugins menu and select the two layers you wish to compare.

<!-- Movie here -->

### Writing to Zip
Finally, you can save your segmentation to a zip file whose internal directory structure
will closely mimic that of the tracking challenge datasets, so that it may be opened 
again in the viewer.

To save your layer, choose File -> Save selected layer(s) with *one* labels layer selected,
then select label zipper from the dropdown choices.

<!-- Movie here -->
