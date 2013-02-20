#!/usr/bin/env python

"""
Compute surface and volume label overlaps.

Compute the Dice and Jaccard overlap measures for each labeled region
of two labeled surfaces or image volumes, for example one that has been
manually labeled and one that has been automatically labeled.

For surface overlap, this program simply calls Joachim Giard's code.


Authors:
    - Arno Klein  (arno@mindboggle.info)  http://binarybottle.com

Copyright 2012,  Mindboggle team (http://mindboggle.info), Apache v2.0 License

"""

def measure_surface_overlap(command, labels_file1, labels_file2):
    """
    Measure surface overlap using Joachim Giard's code.

    Parameters
    ----------
    command : surface overlap C++ executable command
    labels_file1 : ``vtk file`` with index labels for scalar values
    labels_file2 : ``vtk file`` with index labels for scalar values

    Returns
    -------
    overlap_file : string
        name of output text file with overlap results

    Examples
    --------
    >>> import os
    >>> from mindboggle.evaluate.evaluate_labels import measure_surface_overlap
    >>> ccode_path = os.environ['MINDBOGGLE_TOOLS']
    >>> command = os.path.join(ccode_path, 'surface_overlap', 'SurfaceOverlapMain')
    >>> path = os.path.join(os.environ['MINDBOGGLE_DATA'])
    >>> file1 = os.path.join(path, 'arno', 'labels', 'lh.labels.DKT25.manual.vtk')
    >>> file2 = os.path.join(path, 'arno', 'labels', 'lh.labels.DKT31.manual.vtk')
    >>> measure_surface_overlap(command, file1, file2)

    """
    import os
    from nipype.interfaces.base import CommandLine

    overlap_filename = os.path.basename(labels_file1) + '_and_' + \
                       os.path.basename(labels_file2) + '.txt'
    overlap_file = os.path.join(os.getcwd(), overlap_filename)
    cli = CommandLine(command = command)
    cli.inputs.args = ' '.join([labels_file1, labels_file2, overlap_file])
    cli.cmdline
    cli.run()

    return overlap_file


def measure_volume_overlap(labels, file1, file2):
    """
    Measure overlap between individual label regions
    in source and target nifti (nii.gz) images.

    Parameters
    ----------
    labels : list of label indices
    file1 : source image, consisting of index-labeled pixels/voxels
    file2 : target image, consisting of index-labeled pixels/voxels

    Returns
    -------
    overlaps : numpy array
        overlap values
    out_file : string
        output text file name with overlap values

    Examples
    --------
    >>> import os
    >>> from mindboggle.evaluate.evaluate_labels import measure_volume_overlap
    >>> from mindboggle.utils.io_file import read_columns
    >>> path = os.path.join(os.environ['MINDBOGGLE_DATA'])
    >>> file1 = os.path.join(path, 'arno', 'labels', 'labels.DKT25.manual.nii.gz')
    >>> file2 = os.path.join(path, 'arno', 'labels', 'labels.DKT31.manual.nii.gz')
    >>> labels_file = os.path.join(path, 'info', 'labels.volume.DKT25.txt')
    >>> labels = read_columns(labels_file, 1)[0]
    >>> measure_volume_overlap(labels, file1, file2)

    """
    import os
    import numpy as np
    import nibabel as nb

    save_output = True

    # Load labeled image volumes
    file1_data = nb.load(file1).get_data().ravel()
    file2_data = nb.load(file2).get_data().ravel()
    #print(file1 + ' ' + file2)
    #print(np.unique(file1_data))
    #print(np.unique(file2_data))

    # Initialize output
    overlaps = np.zeros((len(labels), 3))

    # Loop through labels
    for ilabel, label in enumerate(labels):
        label = int(label)
        overlaps[ilabel, 0] = label

        # Find which voxels contain the label in each volume
        file1_indices = np.where(file1_data==label)[0]
        file2_indices = np.where(file2_data==label)[0]
        file1_label_sum = len(file1_indices)
        file2_label_sum = len(file2_indices)

        # Determine their intersection and union
        intersect_label_sum = len(np.intersect1d(file2_indices, file1_indices))
        union_label_sum = len(np.union1d(file2_indices, file1_indices))
        #print('{0} {1} {2} {3} {4}'.format(label, file2_label_sum, file1_label_sum,
        #                              intersect_label_sum, union_label_sum))

        # There must be at least one voxel with the label in each volume
        if file2_label_sum * file1_label_sum > 0:

            # Compute Dice and Jaccard coefficients
            dice = np.float(2.0 * intersect_label_sum) / +\
                   (file2_label_sum + file1_label_sum)
            jacc = np.float(intersect_label_sum) / union_label_sum
            overlaps[ilabel, 1:3] = [dice, jacc]
            print('label: {0}, dice: {1:.2f}, jacc: {2:.2f}'.format(
                  label, dice, jacc))

        # NOTE:  untested:
        if save_output:
            file1_name = os.path.splitext(os.path.basename(file1))[0]
            file2_name = os.path.splitext(os.path.basename(file2))[0]
            out_file = os.path.join(os.getcwd(), 'labelvolume_dice_jacc_' +
                                    file2_name + '_vs_' + file1_name + '.txt')
            np.savetxt(out_file, overlaps, fmt='%d %.4f %.4f',
                       delimiter='\t', newline='\n')

    return overlaps, out_file

