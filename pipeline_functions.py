#!/usr/bin/python

"""
This is Mindboggle's NiPype pipeline!

Example usage:

from pipeline import create_mindboggle_flow
wf = create_mindboggle_flow()
wf.inputs.feature_extractor.curvature_file = '/projects/mindboggle/data/ManualSurfandVolLabels/subjects/KKI2009-14/surf/lh.curv'
wf.inputs.feature_extractor.surface_file = '/projects/mindboggle/data/ManualSurfandVolLabels/subjects/KKI2009-14/surf/lh.pial'
wf.run() # doctest: +SKIP


Authors:  Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

##############################################################################
#   Multi-atlas registration
##############################################################################

def register_template(subject_id, subjects_path, 
                      template_name, templates_path, reg_name):
    """Register surface to template with FreeSurfer's mris_register

    Example: bert
             /Applications/freesurfer/subjects
             ./templates_freesurfer
             KKI_2.tif
             sphere_to_template.reg
    """
    import os

    for hemi in ['lh','rh']:
        input_file = os.path.join(subjects_path, subject_id, 'surf', hemi + '.sphere')
        output_file = os.path.join(subjects_path, subject_id, 'surf', hemi + '.' + reg_name)
        template_file = os.path.join(templates_path, hemi + '.' + template_name)
        args = ['mris_register -curv', input_file, template_file, output_file]
        print(' '.join(args)); os.system(' '.join(args))
    return reg_name

def register_atlases(subject_id, atlas_list_file, annot_file_name,
                     reg_name, output_path):
    """Transform the labels from multiple atlases via a template
    using FreeSurfer's mri_surf2surf (wrapped in NiPype)

    nipype.workflows.smri.freesurfer.utils.fs.SurfaceTransform
    wraps command **mri_surf2surf**:
    "Transform a surface file from one subject to another via a spherical registration.
    Both the source and target subject must reside in your Subjects Directory,
    and they must have been processed with recon-all, unless you are transforming
    to one of the icosahedron meshes."
    """
    import os
    from nipype.interfaces.freesurfer import SurfaceTransform

    sxfm = SurfaceTransform()
    sxfm.inputs.target_subject = subject_id

    # Get list of atlas subjects from a file
    f = open(atlas_list_file)
    atlas_list = f.readlines()
    for atlas_line in atlas_list:
        # For each atlas
        atlas_name = atlas_line.strip("\n")
        sxfm.inputs.source_subject = atlas_name
        # For each hemisphere
        for hemi in ['lh','rh']:        
            sxfm.inputs.hemi = hemi
            # Specify annotation file
            output_annot = os.path.join(output_path, subject_id, 'label',
                                        hemi + '.' + atlas_name + '_to_' + \
                                        subject_id + '_' + annot_file_name)
            args = ['--sval-annot', annot_file_name,
                    '--tval', output_annot,
                    '--srcsurfreg', reg_name,
                    '--trgsurfreg', reg_name]
            sxfm.inputs.args = ' '.join(args)
            sxfm.run()
    return atlas_list

##############################################################################
#   Surface map calculation
##############################################################################

def convert_to_vtk(fs_surface_files):
    """Measure

    measure_()
    """
    #import subprocess as sp
    import os
    surface_files = []
    for fs_surface_file in fs_surface_files:
        surface_file = fs_surface_file + '.vtk'
        surface_files.append(surface_file)
        args = ['mris_convert', fs_surface_file, surface_file]
        print(' '.join(args)); os.system(' '.join(args))
    #proc = sp.Popen(' '.join(args))
    #o, e = proc.communicate()
    #if proc.returncode > 0 :
    #    raise Exception('\n'.join([args + ' failed', o, e]))
    return surface_files

def measure_surface_maps(travel_depth_command, surface_files):
    """Measure

    measure_()
    """
    import os
    depth_curv_map_files = []
    for surface_file in surface_files:
        depth_curv_map_file = surface_file.strip('.vtk') + '.depth.vtk'
        depth_curv_map_files.append(depth_curv_map_file)
        args = [travel_depth_command, surface_file, depth_curv_map_file]
        print(' '.join(args)); os.system(' '.join(args))
    return surface_files, depth_curv_map_files

##############################################################################
#   Feature extraction
##############################################################################

def extract_fundi(extract_fundi_command, surface_files, depth_curv_map_files):
    """Extract fundi

    extract_fundi
    """
    import os
    fundi = []
    for i, surface_file in enumerate(surface_files):
        depth_curv_map_file = depth_curv_map_files[i]
        args = ['python', extract_fundi_command, 
               '%s'%surface_file, '%s'%depth_curv_map_file]
        print(' '.join(args)); os.system(' '.join(args))
    return fundi

"""
def extract_sulci(surface_file, depth_map, mean_curvature_map, gauss_curvature_map):
    ""Extract sulci

    extract_sulci
    ""
    import subprocess as sp
    args = 'feature = extract/sulci/extract.py'
    args = ['python', args, '%s'%surface_file, '%s'%depth_map]
    print(' '.join(args)); os.system(' '.join(args))
    #output_file = glob('file1.vtk').pop()
    #feature_files = glob('*.vtk')
    #return feature_files
    return sulci

def extract_midaxis(surface_file, depth_map, mean_curvature_map, gauss_curvature_map):
    ""Extract midaxis

    extract_midaxis
    ""
    from glob import glob
    import subprocess as sp
    args = 'feature = extract/midaxis/extract.py'
    args = ['python', args, '%s'%surface_file, '%s'%depth_map]
    print(' '.join(args)); os.system(' '.join(args))
    return midaxis
"""

# Labeled surface patch and volume extraction nodes
def extract_patches(labels):
    """Extract labeled surface patches
    
    extract_patches
    """
    from glob import glob
    import subprocess as sp
    args = ['python', 'patch = extract/labels/extract.py']
    print(' '.join(args)); os.system(' '.join(args))
    return patches

def extract_regions(labels):
    """Extract labeled region volumes
    
    extract_regions
    """
    from glob import glob
    import subprocess as sp
    args = ['python', 'region = extract/labels/extract.py']
    print(' '.join(args)); os.system(' '.join(args))
    return regions

##############################################################################
#   Label propagation
##############################################################################

def propagate_labels(labels, fundi):
    """Propagate labels
    """
    return labels

# Volume label propagation node
def propagate_volume_labels(labels):
    """Propagate labels through volume
    """
    return labels


##############################################################################
#   Feature segmentation / identification
##############################################################################

def segment_sulci(sulci):
    """Segment and identify sulci
    """
    import os

    for hemi in ['lh','rh']:
        input_file = os.path.join(subject_surf_path, hemi + '.sphere')
        output_file = os.path.join(subject_surf_path, hemi + '.' + reg_name)
        template_file = os.path.join(templates_path, hemi + '.' + template_name)
        args = ['mris_register -curv', input_file, template_file, output_file]
        print(' '.join(args)); os.system(' '.join(args))
        return feature_type, segmented_sulci

def segment_fundi(fundi):
    """Segment and identify fundi
    """
    import os

    for hemi in ['lh','rh']:
        input_file = os.path.join(subject_surf_path, hemi + '.sphere')
        output_file = os.path.join(subject_surf_path, hemi + '.' + reg_name)
        template_file = os.path.join(templates_path, hemi + '.' + template_name)
        args = ['mris_register -curv', input_file, template_file, output_file]
        print(' '.join(args)); os.system(' '.join(args))
        return feature_type, segmented_fundi

def segment_midaxis(midaxis):
    """Segment and identify medial axis surfaces
    """
    import os

    for hemi in ['lh','rh']:
        input_file = os.path.join(subject_surf_path, hemi + '.sphere')
        output_file = os.path.join(subject_surf_path, hemi + '.' + reg_name)
        template_file = os.path.join(templates_path, hemi + '.' + template_name)
        args = ['mris_register -curv', input_file, template_file, output_file]
        print(' '.join(args)); os.system(' '.join(args))
        return feature_type, segmented_midaxis

##############################################################################
#   High-level shape measurement functions
##############################################################################

def measure_positions(features):
    """Measure

    measure_()
    """
    for feature in features:
        from measure.py import measure_position
        if type(feature) is np.ndarray:
            measurement = measure_position(feature)

def measure_extents(features):
    """Measure

    measure_()
    """
    for feature in features:
        from measure.py import measure_extent
        if type(feature) is np.ndarray:
            measurement = measure_extent(feature)

def measure_curvatures(features):
    """Measure

    measure_()
    """
    for feature in features:
        from measure.py import measure_curvature
        if type(feature) is np.ndarray:
            measurement = measure_curvature(feature)

def measure_depths(features):
    """Measure

    measure_()
    """
    for feature in features:
        from measure.py import measure_depth
        if type(feature) is np.ndarray:
            measurement = measure_depth(feature)

def measure_spectra(features):
    """Measure

    measure_()
    """
    for feature in features:
        from measure.py import measure_spectrum
        if type(feature) is np.ndarray:
            measurement = measure_spectrum(feature)

##############################################################################
#   Individual shape measurement functions
##############################################################################

def measure_position(feature):
    """Measure

    measure_()
    """
    from measure.py import measure_position
    if type(feature) is np.ndarray:
        measurement = measure_position(feature)
    return measurement

def measure_extent(feature):
    """Measure

    measure_()
    """
    from measure.py import measure_extent
    if type(feature) is np.ndarray:
        measurement = measure_extent(feature)
    return measurement

def measure_depth(feature):
    """Measure

    measure_()
    """
    from measure.py import measure_depth
    if type(feature) is np.ndarray:
        measurement = measure_(feature)
    return measurement

def measure_curvature(feature):
    """Measure

    measure_()
    """
    from measure.py import measure_curvature
    if type(feature) is np.ndarray:
        measurement = measure_curvature(feature)
    return measurement

def measure_spectrum(feature):
    """Measure

    measure_()
    """
    from measure.py import measure_spectrum
    if type(feature) is np.ndarray:
        measurement = measure_spectrum(feature)
    return measurement

##############################################################################
#    Store features in database
##############################################################################

def write_maps_to_database(surface_map):
    """Write to database

    write_to_database()
    """
    from write_to_database.py import maps_to_database
    if type(feature) is np.ndarray:
        maps_to_database(surface_map)
    success = 'True'
    return success

def write_features_to_database(feature):
    """Write to database

    write_to_database()
    """
    from write_to_database.py import features_to_database
    if type(feature) is np.ndarray:
        features_to_database(feature)
    success = 'True'
    return success

def write_measures_to_database(measurements):
    """Write to database

    write_to_database()
    """
    from write_to_database.py import measure_to_database
    for measurement in measurements:
        if type(measurement) is np.ndarray:
            measure_to_database(measurement)
    success = 'True'
    return success
    
def write_measures_to_table(measurement):
    """Write to database

    write_to_database()
    """
    from write_to_table.py import measure_to_table
    for measurement in measurements:
        if type(measurement) is np.ndarray:
            measure_to_table(measurement)
    success = 'True'
    return success

