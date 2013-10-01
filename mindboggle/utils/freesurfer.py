#!/usr/bin/env python
"""
Functions that call FreeSurfer commands.

These functions are for converting from FreeSurfer formats,
and for surface registration-based labeling.


Authors:
    - Forrest Sheng Bao, 2012  (forrest.bao@gmail.com)  http://fsbao.net
    - Arno Klein, 2012-2013  (arno@mindboggle.info)  http://binarybottle.com
    - Oliver Hinds, 2013  (ohinds@gmail.com)

Copyright 2013,  Mindboggle team (http://mindboggle.info), Apache v2.0 License

"""


def surface_to_vtk(surface_file, output_vtk):
    """
    Convert FreeSurfer surface file to VTK format.

    If a file named orig.mgz exists in '../mri', the surface coordinates
    are transformed into scanner RAS space during format conversion
    according to the vox2ras transform in that file.

    Parameters
    ----------
    surface_file : string
        name of FreeSurfer surface file
    output_vtk : string
        name of output VTK file

    Returns
    -------
    output_vtk : string
        name of output VTK file

    Examples
    --------
    >>> import os
    >>> from mindboggle.utils.freesurfer import surface_to_vtk
    >>> path = os.environ['MINDBOGGLE_DATA']
    >>> surface_file = os.path.join(path, 'arno', 'freesurfer', 'lh.pial')
    >>> output_vtk = ''
    >>> #
    >>> surface_to_vtk(surface_file, output_vtk)
    >>> #
    >>> # View:
    >>> from mindboggle.utils.plots import plot_surfaces
    >>> plot_surfaces('lh.pial.vtk')

    """
    import os
    import nibabel as nb

    from mindboggle.utils.io_vtk import write_header, write_points, write_faces

    surf = nb.freesurfer.read_geometry(surface_file)
    points = surf[0]
    faces = surf[1]

    # Transform surface coordinates into normal scanner RAS.
    # See example 3 in "Transforms within a subject's anatomical space":
    # https://surfer.nmr.mgh.harvard.edu/fswiki/CoordinateSystems
    orig_file = os.path.join(os.path.dirname(surface_file),
                             "..", "mri", "orig.mgz")

    if os.path.exists(orig_file):
        import numpy as np
        Norig = nb.load(orig_file).get_affine()
        Torig = np.array([[-1, 0, 0, 128],
                          [0, 0, 1, -128],
                          [0, -1, 0, 128],
                          [0, 0, 0, 1]], dtype=float)
        xfm = np.dot(Norig, np.linalg.inv(Torig))
        points = np.transpose(np.dot(xfm, np.transpose(
            np.concatenate((points, np.ones((np.shape(points)[0],1))),
                           axis=1))))[:,0:3]

    if not output_vtk:
        output_vtk = os.path.join(os.getcwd(),
                                  os.path.basename(surface_file + '.vtk'))
    Fp = open(output_vtk, 'w')
    write_header(Fp, Title='vtk output from ' + surface_file)
    write_points(Fp, points)
    write_faces(Fp, faces)
    Fp.close()

    if not os.path.exists(output_vtk):
        raise(IOError(output_vtk + " not found"))

    return output_vtk


def curvature_to_vtk(surface_file, vtk_file, output_vtk):
    """
    Convert FreeSurfer curvature, thickness, or convexity file to VTK format.

    Parameters
    ----------
    surface_file : string
        name of FreeSurfer surface file
    vtk_file : string
        name of VTK surface file
    output_vtk : string
        name of output VTK file

    Returns
    -------
    output_vtk : string
        name of output VTK file, where each vertex is assigned
        the corresponding shape value

    Examples
    --------
    >>> import os
    >>> from mindboggle.utils.io_vtk import curvature_to_vtk
    >>> path = os.environ['MINDBOGGLE_DATA']
    >>> surface_file = os.path.join(path, 'arno', 'freesurfer', 'lh.thickness')
    >>> vtk_file = os.path.join(path, 'arno', 'freesurfer', 'lh.pial.vtk')
    >>> output_vtk = ''
    >>> #
    >>> curvature_to_vtk(surface_file, vtk_file, output_vtk)
    >>> #
    >>> # View:
    >>> from mindboggle.utils.plots import plot_surfaces
    >>> plot_surfaces('lh.thickness.vtk')

    """
    import os
    import nibabel as nb

    from mindboggle.utils.io_vtk import rewrite_scalars

    curvature_values = nb.freesurfer.read_morph_data(surface_file)
    scalar_names = os.path.basename(surface_file)

    if not output_vtk:
        output_vtk = os.path.join(os.getcwd(),
                                  os.path.basename(surface_file)+'.vtk')
    rewrite_scalars(vtk_file, output_vtk, curvature_values, scalar_names)
    if not os.path.exists(output_vtk):
        raise(IOError(output_vtk + " not found"))

    return output_vtk


def annot_to_vtk(annot_file, vtk_file, output_vtk=''):
    """
    Load a FreeSurfer .annot file and save as a VTK format file.

    Note regarding current pip install nibabel (fixed in github master repo)::

        The 'True' flag in nibabel.freesurfer.read_annot(annot_file, True)
        gives the original FreeSurfer label values, not the FreeSurferColorLUT
        labels, and when set to 'False' assigns all otherwise unlabeled
        left cortical vertices to 3, which is also assigned to the caudal
        middle frontal gyrus.  To correct this ambiguity, this program assigns
        -1 to all vertices with label 0 in the original ('True') labels.

    Parameters
    ----------
    annot_file : string
        name of FreeSurfer .annot file
    vtk_file : string
        name of VTK surface file
    output_vtk : string
        name of output VTK file, where each vertex is assigned
        the corresponding shape value

    Returns
    -------
    labels : list
        integers (one label per vertex)
    output_vtk : string
        name of output VTK file, where each vertex is assigned
        the corresponding shape value

    Examples
    --------
    >>> import os
    >>> from mindboggle.utils.freesurfer import annot_to_vtk
    >>> path = os.environ['MINDBOGGLE_DATA']
    >>> annot_file = os.path.join(path, 'arno', 'freesurfer', 'lh.aparc.annot')
    >>> vtk_file = os.path.join(path, 'arno', 'freesurfer', 'lh.pial.vtk')
    >>> output_vtk = ''
    >>> #
    >>> labels, output_vtk = annot_to_vtk(annot_file, vtk_file, output_vtk)
    >>> #
    >>> # View:
    >>> from mindboggle.utils.plots import plot_surfaces
    >>> plot_surfaces(output_vtk)

    """
    import os
    import nibabel as nb
    import numpy as np

    from mindboggle.utils.io_vtk import rewrite_scalars

    labels, ctab, names = nb.freesurfer.read_annot(annot_file)

    # CAN REMOVE THE FOLLOWING FEW LINES WHEN
    # https://github.com/nipy/nibabel/issues/205#issuecomment-25294009
    # RESOLUTION IN THE PIP INSTALL VERSION OF NIBABEL:
    labels_orig, ctab, names = nb.freesurfer.read_annot(annot_file, True)
    labels[np.where(labels_orig == 0)[0]] = -1
    # Test removal of unlabeled cortex from label 3:
    #labels[np.where(labels==3)[0]]=1000

    if not output_vtk:
        output_vtk = os.path.join(os.getcwd(),
            os.path.basename(annot_file).strip('.annot') + '.vtk')

    rewrite_scalars(vtk_file, output_vtk, labels, 'Labels')

    if not os.path.exists(output_vtk):
        raise(IOError(output_vtk + " not found"))

    return labels, output_vtk


def annot_labels_to_volume(subject, annot_name, original_space, reference):
    """
    Propagate surface labels through hemisphere's gray matter volume
    and convert label volume from FreeSurfer 'unconformed' to original space
    using FreeSurfer's mri_aparc2aseg and mri_vol2vol.

    Note ::
        From the mri_aparc2aseg documentation:
        The volumes of the cortical labels will be different than
        reported by mris_anatomical_stats because partial volume information
        is lost when mapping the surface to the volume. The values reported by
        mris_anatomical_stats will be more accurate than the volumes from the
        aparc+aseg volume.

    Parameters
    ----------
    subject : string
        subject name
    annot_name: string
        FreeSurfer annot filename without the hemisphere prepend or .annot append
    original_space: Boolean
        convert from FreeSurfer unconformed to original space?
    reference : string
        file in original space

    Returns
    -------
    output_file : string
        name of output file

    """
    import os

    from mindboggle.utils.utils import execute

    # Fill hemisphere gray matter volume with surface labels using FreeSurfer:
    print("Fill gray matter volume with surface labels using FreeSurfer...")

    output_file1 = os.path.join(os.getcwd(), annot_name + '.nii.gz')

    cmd = ['mri_aparc2aseg', '--s', subject, '--annot', annot_name,
            '--o', output_file1]
    execute(cmd)
    if not os.path.exists(output_file1):
        raise(IOError(output_file1 + " not found"))

    # Convert label volume from FreeSurfer to original space:
    if original_space:
        print("Convert label volume from FreeSurfer 'unconformed' to original space...")

        output_file2 = os.path.join(os.getcwd(), annot_name + '.native.nii.gz')

        interp = 'nearest'
        cmd = ['mri_vol2vol',
               '--mov', output_file1,
               '--targ', reference,
               '--interp', interp,
               '--regheader --o', output_file2]
        execute(cmd)
        if not os.path.exists(output_file2):
            raise(IOError(output_file2 + " not found"))
        output_file = output_file2
    else:
        output_file = output_file1

    if not os.path.exists(output_file):
        raise(IOError(output_file + " not found"))

    return output_file


def label_with_classifier(subject, hemi, left_classifier='',
                          right_classifier='', annot_file=''):
    """
    Label a brain with the DKT atlas using FreeSurfer's mris_ca_label

    FreeSurfer documentation ::

        SYNOPSIS
        mris_ca_label [options] <subject> <hemi> <surf> <classifier> <output>

        DESCRIPTION
        For a single subject, produces an annotation file, in which each
        cortical surface vertex is assigned a neuroanatomical label.
        This automatic procedure employs data from a previously-prepared atlas
        file. An atlas file is created from a training set, capturing region
        data manually drawn by neuroanatomists combined with statistics on
        variability correlated to geometric information derived from the
        cortical model (sulcus and curvature). Besides the atlases provided
        with FreeSurfer, new ones can be prepared using mris_ca_train).

    Notes regarding creation and use of FreeSurfer Gaussian classifier atlas:

    Create the DKT classifier atlas (?h.DKTatlas40.gcs) --NEED TO VERIFY THIS:
    $ mris_ca_train -t $FREESURFERHOME/average/colortable_desikan_killiany.txt \
                    $hemi sphere.reg aparcNMMjt.annot $SCANS ./$hemi.DKTatlas40.gcs

    Label a brain with the DKT atlas (surface annotation file ?h.DKTatlas40.annot):
    $ mris_ca_label -l ./$x/label/$hemi.cortex.label $x/ $hemi sphere.reg \
                    ./$hemi.DKTatlas40.gcs ./$x/label/$hemi.DKTatlas40.annot

    Label the cortex of a subject's segmented volume according
    to the edited surface labels (?h.aparcNMMjt.annot):
    $ mri_aparc2aseg --s ./x --volmask --annot aparcNMMjt

    Label a brain with the DKT atlas using FreeSurfer's mris_ca_label:
    $ mris_ca_label MMRR-21-1 lh lh.sphere.reg ../lh.DKTatlas40.gcs ../out.annot

    Parameters
    ----------
    subject : string
        subject corresponding to FreeSurfer subject directory
    hemi : string
        hemisphere ['lh' or 'rh']
    left_classifier : string
        name of left hemisphere FreeSurfer classifier atlas (full path)
    right_classifier : string
        name of right hemisphere FreeSurfer classifier atlas (full path)
    annot_file : string
        name of output .annot file

    Returns
    -------
    annot_file : string
        name of output .annot file

    Examples
    --------
    >>> # This example requires a FreeSurfer subjects/<subject> subdirectory
    >>> import os
    >>> from mindboggle.utils.freesurfer import label_with_classifier
    >>> subject = 'Twins-2-1'
    >>> hemi = 'lh'
    >>> left_classifier = '/homedir/mindboggle_cache/b28a600a713c269f4c561f66f64337b2/lh.DKTatlas40.gcs'
    >>> right_classifier = ''
    >>> annot_file = './lh.classifier.annot'
    >>> label_with_classifier(subject, hemi, left_classifier, right_classifier, annot_file)
    >>> #
    >>> # View:
    >>> from mindboggle.utils.freesurfer import annot_to_vtk
    >>> from mindboggle.utils.plots import plot_surfaces
    >>> path = os.environ['MINDBOGGLE_DATA']
    >>> vtk_file = os.path.join(path, 'arno', 'freesurfer', 'lh.pial.vtk')
    >>> output_vtk = './lh.classifier.vtk'
    >>> #
    >>> labels, output_vtk = annot_to_vtk(annot_file, vtk_file, output_vtk)
    >>> plot_surfaces(output_vtk)

    """
    import os
    from mindboggle.utils.utils import execute

    if not annot_file:
        annot_file = os.path.join(os.getcwd(), hemi + '.classifier.annot')

    if hemi == 'lh':
        classifier = left_classifier
    elif hemi == 'rh':
        classifier = right_classifier
    else:
        print("label_with_classifier()'s hemi should be 'lh' or 'rh'")

    cmd = ['mris_ca_label', subject, hemi, hemi+'.sphere.reg', classifier,
            annot_file]
    execute(cmd)
    if not os.path.exists(annot_file):
        raise(IOError(annot_file + " not found"))

    return annot_file


def register_template(hemi, sphere_file, transform,
                      templates_path, template):
    """
    Register surface to template with FreeSurfer's mris_register.

    Transform the labels from multiple atlases via a template
    (using FreeSurfer's mris_register).

    """
    import os

    from mindboggle.utils.utils import execute

    template_file = os.path.join(templates_path, hemi + '.' + template)
    output_file = hemi + '.' + transform

    cmd = ['mris_register', '-curv', sphere_file, template_file, output_file]
    execute(cmd)
    if not os.path.exists(output_file):
        raise(IOError(output_file + " not found"))

    return transform


def transform_atlas_labels(hemi, subject, transform,
                           subjects_path, atlas, atlas_string):
    """
    Transform atlas labels.

    Read in the FreeSurfer *.annot file for a subject's brain hemisphere,
    .

    Transform the labels from a surface atlas via a template
    using FreeSurfer's mri_surf2surf (wrapped in Nipype).

    nipype.workflows.smri.freesurfer.utils.fs.SurfaceTransform
    wraps command ``mri_surf2surf`` ::

        "Transform a surface file from one subject to another via a spherical
        registration. Both the source and target subject must reside in your
        Subjects Directory, and they must have been processed with recon-all,
        unless you are transforming to one of the icosahedron meshes."

    Parameters
    ----------
    hemi : string
        hemisphere ['lh' or 'rh']
    subject : string
        subject corresponding to FreeSurfer subject directory
    transform : string
        name of FreeSurfer spherical surface registration transform file
    subjects_path : string
        name of FreeSurfer subjects directory
    atlas : string
        name of atlas
    atlas_string : string
        name of atlas labeling protocol

    Returns
    -------
    output_file : string
        name of the output file

    """
    import os
    from nipype.interfaces.freesurfer import SurfaceTransform

    sxfm = SurfaceTransform()
    sxfm.inputs.hemi = hemi
    sxfm.inputs.target_subject = subject
    sxfm.inputs.source_subject = atlas

    # Source file
    sxfm.inputs.source_annot_file = os.path.join(subjects_path,
                                    atlas, 'label',
                                    hemi + '.' + atlas_string + '.annot')
    # Output annotation file
    output_file = os.path.join(os.getcwd(), hemi + '.' + atlas + '.' +
                               atlas_string + '_to_' + subject + '.annot')
    sxfm.inputs.out_file = output_file

    # Arguments: strings within registered files
    args = ['--srcsurfreg', transform,
            '--trgsurfreg', transform]
    sxfm.inputs.args = ' '.join(args)

    sxfm.run()

    if not os.path.exists(output_file):
        raise(IOError(output_file + " not found"))

    return output_file


def combine_whites_over_grays(subject, second_segmentation_file='',
                              out_dir='', use_c3d=False):
    """
    Combine FreeSurfer segmentation volumes (no surface-based outputs)
    and a segmentation file from another source (such as ANTs Atropos)
    to obtain a single gray=2 and white=3 matter segmentation file.

    If the second file is not provided, the function returns a gray and
    white matter segmentation file from FreeSurfer volume files.

    Steps ::

        1. Convert FreeSurfer aseg.mgz (gray) and filled.mgz (white) volumes
           to nifti format in their original space (using rawavg.mgz).
        2. Load second segmentation file where gray=2 and white=3,
           such as from ANTs (Atropos).
        3. Combine the union of the gray matter from #1 and #2
           and the union of the white matter from #1 and #2,
           replacing white and gray matter overlap with white matter.

    Note ::

        Requires FreeSurfer's mri_vol2vol function and either ANTs ImageMath
        or the convert3d (c3d) tool.

    Parameters
    ----------
    subject : string
        name of FreeSurfer subject (for filled.mgz and aseg.mgz files)
    second_segmentation_file : str (optional)
        second segmentation file (gray=2, white=3; other labels are fine)
    out_dir : str (optional)
        output directory
    use_c3d : Boolean
        use convert3d? (otherwise ANTs ImageMath)

    Returns
    -------
    gray_and_white_file : string
        name of gray and white matter segmented file (gray=2, white=3)

    Examples
    --------
    >>> from mindboggle.utils.freesurfer import combine_whites_over_grays
    >>> subject = 'OASIS-TRT-20-1'
    >>> second_segmentation_file = '/homedir/Data/Atropos/OASIS-TRT-20-1/tmp123/tmpBrainSegmentation.nii.gz'
    >>> out_dir = ''
    >>> use_c3d = False
    >>> combine_whites_over_grays(subject, second_segmentation_file, out_dir, use_c3d)

    """
    import os
    import nibabel as nb

    from mindboggle.utils.utils import execute

    subjects_dir = os.environ['SUBJECTS_DIR']

    #-------------------------------------------------------------------------
    # Outputs:
    #-------------------------------------------------------------------------
    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
    else:
        out_dir = os.getcwd()
    gray_and_white_file = os.path.join(out_dir, 'gray_and_white.nii.gz')
    white_file = os.path.join(out_dir, 'white.nii.gz')
    temp_file = os.path.join(out_dir, 'temp.nii.gz')

    #-------------------------------------------------------------------------
    # Convert FreeSurfer gray and white matter volumes to nifti format:
    #-------------------------------------------------------------------------
    rawavg = os.path.join(subjects_dir, subject, 'mri', 'rawavg.mgz')
    aseg = os.path.join(subjects_dir, subject, 'mri', 'aseg.mgz')
    cmd = ['mri_vol2vol --mov', aseg, '--targ', rawavg, '--interp nearest',
           '--regheader --o', gray_and_white_file]
    execute(cmd)
    if not os.path.exists(gray_and_white_file):
        raise(IOError(gray_and_white_file + " not found"))

    filled = os.path.join(subjects_dir, subject, 'mri', 'filled.mgz')
    cmd = ['mri_vol2vol --mov', filled, '--targ', rawavg, '--interp nearest',
           '--regheader --o', white_file]
    execute(cmd)
    if not os.path.exists(white_file):
        raise(IOError(white_file + " not found"))

    if use_c3d:
        #---------------------------------------------------------------------
        # Retain only gray or white matter values:
        #---------------------------------------------------------------------
        cmd = ['c3d', gray_and_white_file, '-replace 1 0 3 1 42 1',
               '-threshold 1 1 2 0', '-o', gray_and_white_file]
        execute(cmd)

        cmd = ['c3d', white_file, '-binarize -scale 3', '-o', white_file]
        execute(cmd)

        #---------------------------------------------------------------------
        # Include second segmentation:
        #---------------------------------------------------------------------
        if second_segmentation_file:
            cmd = ['c3d', second_segmentation_file, '-threshold 2 2 1 0',
                   gray_and_white_file, '-add -binarize',
                   '-threshold 1 1 2 0', '-o', gray_and_white_file]
            execute(cmd)
            cmd = ['c3d', second_segmentation_file, '-threshold 3 3 1 0',
                   white_file, '-add -binarize', '-threshold 1 1 3 0',
                   '-o', white_file]
            execute(cmd)

        #---------------------------------------------------------------------
        # Replace white/gray matter overlap with white matter:
        #---------------------------------------------------------------------
        cmd = ['c3d', white_file, '-threshold 3 3 0 1', gray_and_white_file,
               '-multiply', white_file, '-add', '-o', gray_and_white_file]
        execute(cmd)

    else:
        #---------------------------------------------------------------------
        # Retain only gray or white matter values:
        #---------------------------------------------------------------------
        cmd = ['ImageMath 3', gray_and_white_file,
               'ReplaceVoxelValue', gray_and_white_file, '1 1 0']
        execute(cmd)
        cmd = ['ImageMath 3', gray_and_white_file,
               'ReplaceVoxelValue', gray_and_white_file, '3 3 1']
        execute(cmd)
        cmd = ['ImageMath 3', gray_and_white_file,
               'ReplaceVoxelValue', gray_and_white_file, '42 42 1']
        execute(cmd)
        cmd = ['ThresholdImage 3', gray_and_white_file,
               gray_and_white_file, '1 1 2 0']
        execute(cmd)

        cmd = ['ThresholdImage 3', white_file, white_file, '1 10000 3 0']
        execute(cmd)

        #---------------------------------------------------------------------
        # Include second segmentation:
        #---------------------------------------------------------------------
        if second_segmentation_file:
            cmd = ['ThresholdImage 3', second_segmentation_file,
                   temp_file, '2 2 1 0']
            execute(cmd)
            cmd = ['ImageMath 3', temp_file, '+', temp_file,
                   gray_and_white_file]
            execute(cmd)
            cmd = ['ThresholdImage 3', temp_file,
                   gray_and_white_file, '1 10000 2 0']
            execute(cmd)

            cmd = ['ThresholdImage 3', second_segmentation_file,
                   temp_file, '3 3 1 0']
            execute(cmd)
            cmd = ['ImageMath 3', temp_file, '+', temp_file, white_file]
            execute(cmd)
            cmd = ['ThresholdImage 3', temp_file, white_file, '1 10000 3 0']
            execute(cmd)

        #---------------------------------------------------------------------
        # Replace white/gray matter overlap with white matter:
        #---------------------------------------------------------------------
        cmd = ['ThresholdImage 3', white_file, temp_file, '3 3 0 1']
        execute(cmd)
        cmd = ['ImageMath 3', temp_file, 'm', temp_file, gray_and_white_file]
        execute(cmd)
        cmd = ['ImageMath 3', gray_and_white_file, '+', temp_file, white_file]
        execute(cmd)

    return gray_and_white_file


#def relabel_annot_file(hemi, subject, annot_name, new_annot_name, relabel_file):
#    """
#    Combine surface labels in a .annot file.
#
#    https://mail.nmr.mgh.harvard.edu/pipermail//freesurfer/2010-June/014620.html
#
#     `mris_translate_annotation <subject> <hemi> <in annot> <translation file> <out annot>`
#
#      ``translation file``: text file that lists the labels (one per line)
#      you want to group, and the new label you want to create.  You have to use
#      the RGB codes; each line will provide the input and output RGB values::
#
#            221     220     60      223     220     60
#            221     220     160     223     220     60
#            221     220     100     223     220     60
#
#    Parameters
#    ----------
#    hemi : string
#        hemisphere ['lh' or 'rh']
#    subject : string
#        subject name
#    annot_name : string
#        name of .annot file (without pre- or post-pends)
#    relabel_file : string
#        text file with old and new RGB values
#    new_annot_name : string
#        new .annot name
#
#    Returns
#    -------
#    new_annot_name : string
#        new .annot name
#
#    """
#    from nipype.interfaces.base import CommandLine
#
#    cli = CommandLine(command='mris_translate_annotation')
#    cli.inputs.args = ' '.join([subject, hemi, annot_name, relabel_file,
#                                new_annot_name])
#    cli.cmdline
#    cli.run()
#
#    return new_annot_name


#def thickness_to_ascii(hemi, subject, subjects_path):
#    """
#    Convert a FreeSurfer thickness (per-vertex) file
#    to an ascii file.
#
#    Note:  Untested function
#
#    Parameters
#    ----------
#    hemi : string indicating left or right hemisphere
#    subject_path: string
#        path to subject directory where the binary FreeSurfer
#        thickness file is found ("lh.thickness")
#
#    Returns
#    -------
#    thickness_file : string
#        name of output file, where each element is the thickness
#        value of a FreeSurfer mesh vertex. Elements are ordered
#        by orders of vertices in FreeSurfer surface file.
#
#    """
#    import os
#    from nipype.interfaces.base import CommandLine
#
#    filename = hemi + 'thickness'
#    filename_full = os.path.join(subjects_path, subject, filename)
#    thickness_file = os.path.join(os.getcwd(), filename + '.dat')
#
#    cli = CommandLine(command='mri_convert')
#    cli.inputs.args = ' '.join([filename_full, '--ascii+crsf', thickness_file])
#    cli.cmdline
#    cli.run()
#
#    return thickness_file


#def vtk_to_labels(hemi, surface_file, label_numbers, label_names,
#                   RGBs, scalar_name):
#     """
#     Write FreeSurfer .label files from a labeled VTK surface mesh.
#
#     From https://surfer.nmr.mgh.harvard.edu/fswiki/LabelsClutsAnnotationFiles:
#
#         "A label file is a text file capturing a list of vertices belonging to a region,
#         including their spatial positions(using R,A,S coordinates). A label file
#         corresponds only to a single label, thus contains only a single list of vertices"::
#
#             1806
#             7  -22.796  -66.405  -29.582 0.000000
#             89  -22.273  -43.118  -24.069 0.000000
#             138  -14.142  -81.495  -30.903 0.000000
#             [...]
#
#     Parameters
#     ----------
#     hemi :  string
#         hemisphere
#     surface_file :  string
#         vtk surface mesh file with labels
#     label_numbers :  list of integers
#         label numbers
#     label_names :  list of strings
#         label names
#     RGBs :  list of lists of 3-tuples
#         label RGB values for later conversion to a .annot file
#     scalar_name :  string
#         name of scalar values in vtk file
#
#     Returns
#     -------
#     label_files :  list of strings
#         label file names (order must match label list)
#     colortable :  string
#         file with list of labels and RGB values
#         NOTE: labels are identified by the colortable's RGB values
#
#     """
#     import os
#     import numpy as np
#     import vtk
#
#     def string_vs_list_check(var):
#         """
#         Check type to make sure it is a string.
#
#         (if a list, return the first element)
#         """
#
#         # Check type:
#         if type(var) == str:
#             return var
#         elif type(var) == list:
#             return var[0]
#         else:
#             os.error("Check format of " + var)
#
#     # Check type to make sure the filename is a string
#     # (if a list, return the first element)
#     surface_file = string_vs_list_check(surface_file)
#
#     # Initialize list of label files and output colortable file
#     label_files = []
#     #relabel_file = os.path.join(os.getcwd(), 'relabel_annot.txt')
#     #f_relabel = open(relabel_file, 'w')
#     colortable = os.path.join(os.getcwd(), 'colortable.ctab')
#     f_rgb = open(colortable, 'w')
#
#     # Loop through labels
#     irgb = 0
#     for ilabel, label_number in enumerate(label_numbers):
#
#         # Check type to make sure the number is an int
#         label_number = int(label_number)
#         label_name = label_names[ilabel]
#
#         # Load surface
#         reader = vtk.vtkDataSetReader()
#         reader.SetFileName(surface_file)
#         reader.ReadAllScalarsOn()
#         reader.Update()
#         data = reader.GetOutput()
#         d = data.GetPointData()
#         labels = d.GetArray(scalar_name)
#
#         # Write vertex index, coordinates, and 0
#         count = 0
#         npoints = data.GetNumberOfPoints()
#         L = np.zeros((npoints,5))
#         for i in range(npoints):
#             label = labels.GetValue(i)
#             if label == label_number:
#                 L[count,0] = i
#                 L[count,1:4] = data.GetPoint(i)
#                 count += 1
#
#         # Save the label file
#         if count > 0:
#             irgb += 1
#
#             # Write to relabel_file
#             #if irgb != label_number:
#             #    f_relabel.writelines('{0} {1}\n'.format(irgb, label_number))
#
#             # Write to colortable
#             f_rgb.writelines('{0} {1} {2}\n'.format(
#                 irgb, label_name, "0 0 0 0")) # ".join(RGBs[ilabel])))
#
#             # Store in list of .label files
#             label_file = hemi + '.' + label_name + '.label'
#             label_file = os.path.join(os.getcwd(), label_file)
#             label_files.append(label_file)
#
#             # Write to .label file
#             f = open(label_file, 'w')
#             f.writelines('#!ascii label\n' + str(count) + '\n')
#             for i in range(npoints):
#                 if any(L[i,:]):
#                     pr = '{0} {1} {2} {3} 0\n'.format(
#                         np.int(L[i,0]), L[i,1], L[i,2], L[i,3])
#                     f.writelines(pr)
#                 else:
#                     break
#             f.close()
#     f_rgb.close()
#     #f_relabel.close()
#
#     return label_files, colortable


#def labels_to_annot(hemi, subjects_path, subject, label_files,
#                     colortable, annot_name):
#     """
#     Convert FreeSurfer .label files to a FreeSurfer .annot file
#     using FreeSurfer's mris_label2annot:
#     https://surfer.nmr.mgh.harvard.edu/fswiki/mris_label2annot
#
#     The order of the .label files must equal the order
#     of the labels in the colortable:
#     https://surfer.nmr.mgh.harvard.edu/fswiki/LabelsClutsAnnotationFiles
#
#     NOTE:  The resulting .annot file will have incorrect labels
#            if the numbering of the labels is not sequential from 1,2,3...
#            For programs like tksurfer, the labels are identified
#            by the colortable's RGB values, so to some programs that display
#            the label names, the labels could appear correct when not.
#     NOTE:  You cannot overwrite a .annot file of the same name,
#            so in this script I delete it before running.
#
#     Parameters
#     ----------
#     hemi :  hemisphere [string]
#     subjects_path :  path to file
#     subject :  subject name
#     label_files :  .label file names [list of strings]
#     colortable :  file of label numbers & names (same order as label_files)
#     annot_name :  name of the output .annot file (without prepending hemi)
#
#     Returns
#     -------
#     annot_name :  name of .annot file (without prepend)
#     annot_file :  name of .annot file (with prepend)
#
#     """
#     import os
#     from nipype.interfaces.base import CommandLine
#
#     label_files = [f for f in label_files if f!=None]
#     if label_files:
#         annot_file = hemi + '.' + annot_name + '.annot'
#         if os.path.exists(os.path.join(subjects_path, subject, 'label', annot_file)):
#             cli = CommandLine(command='rm')
#             cli.inputs.args = os.path.join(subjects_path, subject, \
#                                            'label', annot_file)
#             cli.cmdline
#             cli.run()
#         cli = CommandLine(command='mris_label2annot')
#         cli.inputs.args = ' '.join(['--h', hemi, '--s', subject, \
#                                     '--l', ' --l '.join(label_files), \
#                                     '--ctab', colortable, \
#                                     '--a', annot_name])
#         cli.cmdline
#         cli.run()
#
#         return annot_name, annot_file
