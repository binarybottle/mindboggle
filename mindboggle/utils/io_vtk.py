#!/usr/bin/python
"""
Functions related to reading and writing VTK format files.

1. Functions for writing basic VTK elements
2. Functions for loading and writing VTK files
3. Functions for converting FreeSurfer files to VTK format


Authors:
    - Forrest Sheng Bao  (forrest.bao@gmail.com)  http://fsbao.net
    - Arno Klein  (arno@mindboggle.info)  http://binarybottle.com

Copyright 2012,  Mindboggle team (http://mindboggle.info), Apache v2.0 License

"""
#import os
#import numpy as np
#import nibabel as nb
#import vtk
#from mindboggle.utils.mesh_operations import inside_faces
#from mindboggle.utils.io_file import write_table
#from mindboggle.measure.measure_functions import mean_value_per_label
#from mindboggle.utils.io_free import read_surface


#=============================================================================
# Functions for writing basic VTK elements
#=============================================================================

def write_vtk_header(Fp, Header='# vtk DataFile Version 2.0',
                     Title='Generated by Mindboggle (www.mindboggle.info)',
                     fileType='ASCII', dataType='POLYDATA'):
    """
    Write header information for a VTK-format file::

        # vtk DataFile Version 2.0
        Generated by Mindboggle (www.mindboggle.info)
        ASCII
        DATASET POLYDATA

    This part matches three things in the VTK 4.2 File Formats doc:
      - Part 1: Header
      - Part 2: Title (256 characters maximum, terminated with newline character)
      - Part 3: Data type, either ASCII or BINARY
      - Part 4: Geometry/topology. dataType is one of:
          - STRUCTURED_POINTS
          - STRUCTURED_GRID
          - UNSTRUCTURED_GRID
          - POLYDATA
          - RECTILINEAR_GRID
          - FIELD

    """

    Fp.write('{0}\n{1}\n{2}\nDATASET {3}\n'.format(Header, Title, fileType, dataType))

def write_vtk_points(Fp, points, dataType="float"):
    """
    Write coordinates of points, the POINTS section in DATASET POLYDATA section::

        POINTS 150991 float
        -7.62268877029 -81.2403945923 -1.44539153576
        ...

    Indices are 0-offset. Thus the first point is point id 0::

        POINTS n dataType
        p0x p0y p0z
        ...
        p(n-1)x p(n-1)y p(n-1)z

    """
    import numpy as np

    Fp.write('POINTS {0} {1}\n'.format(len(points), dataType))

    n = np.shape(points)[1]
    for point in points:
        if n == 3:
            [R, A, S] = point
            Fp.write('{0} {1} {2}\n'.format(R, A, S))
        elif n == 2:
            [R, A] = point
            Fp.write('{0} {1}\n'.format(R, A))
        else:
            print('ERROR: Unrecognized number of coordinates per point')

def write_vtk_faces(Fp, faces):
    """
    Write indices to vertices forming triangular meshes,
    the POLYGONS section in DATASET POLYDATA section::

        POLYGONS 301978 1207912
        3 0 1 4
        ...

    """
    import numpy as np

    n = np.shape(faces)[1]
    if n == 3:
        face_name = 'POLYGONS '
        Fp.write('{0} {1} {2}\n'.format(face_name, len(faces),
                 len(faces) * (n + 1)))
    elif n == 2:
        face_name = 'LINES '
        Fp.write('{0} {1} {2}\n'.format(face_name, len(faces),
                 len(faces) * (n + 1)))
    else:
        print('ERROR: Unrecognized number of vertices per face')

    for face in faces:
        if n == 3:
            [V0, V1, V2] = face
            Fp.write('{0} {1} {2} {3}\n'.format(n, V0, V1, V2))
        elif n == 2:
            [V0, V1] = face
            Fp.write('{0} {1} {2}\n'.format(n, V0, V1))

def write_vtk_vertices(Fp, indices):
    """
    Write indices to vertices, the VERTICES section
    in the DATASET POLYDATA section::

        VERTICES 140200 420600
        3 130239 2779 10523
        ...

    Indices are 0-offset. Thus the first point is point id 0::

        VERTICES n size
        numPoints0 i0 j0 k0
        ...
        numPoints_[n-1] i_[n-1] j_[n-1] k_[n-1]

    """

    Fp.write('VERTICES {0} {1}\n{2} '.format(
             len(indices), len(indices) + 1, len(indices)))
    [Fp.write('{0} '.format(i)) for i in indices]
    Fp.write('\n')

def write_vtk_LUT(Fp, LUT, LUTName, at_LUT_begin=True):
    """
    Write per-VERTEX values as a scalar LUT into a VTK file::

        POINT_DATA 150991
        SCALARS Max_(majority_labels) int 1
        LOOKUP_TABLE default
        11 11 11 11 11 11 11 11 11 11 ...

    Parameters
    ----------
    LUT :  list of floats
    at_LUT_begin : [Boolean] True if the first vertex LUT in a VTK file

    """

    if at_LUT_begin:
        Fp.write('POINT_DATA {0}\n'.format(len(LUT)))
    Fp.write('SCALARS {0} float\n'.format(LUTName))
    Fp.write('LOOKUP_TABLE {0}\n'.format(LUTName))
    for Value in LUT:
        Fp.write('{0}\n'.format(Value))
    Fp.write('\n')


#=============================================================================
# Functions for loading and writing VTK files
#=============================================================================

def load_scalar(filename, return_arrays=True):
    """
    Load a VTK-format scalar map that contains only one SCALAR segment.

    Parameters
    ----------
    filename : string
        The path/filename of a VTK format file.
    return_arrays : Boolean
        return numpy arrays instead of lists of lists below?

    Returns
    -------
    points : list of lists of floats (see return_arrays)
        Each element is a list of 3-D coordinates of a vertex on a surface mesh
    faces : list of lists of integers (see return_arrays)
        Each element is list of 3 indices of vertices that form a face
        on a surface mesh
    scalars : list of floats (see return_arrays)
        Each element is a scalar value corresponding to a vertex
    n_vertices : int
        number of vertices in the mesh

    Example
    -------
    >>> points, faces, scalars, n_vertices = load_scalar('lh.pial.depth.vtk')

    """
    import numpy as np
    import vtk

    Reader = vtk.vtkDataSetReader()
    Reader.SetFileName(filename)
    Reader.ReadAllScalarsOn()  # Activate the reading of all scalars
    Reader.Update()

    Data = Reader.GetOutput()
    points = [list(Data.GetPoint(point_id))
              for point_id in xrange(0, Data.GetNumberOfPoints())]
    n_vertices = len(points)

    #Vrts = Data.GetVerts()
    #indices = [Vrts.GetData().GetValue(i) for i in xrange(1, Vrts.GetSize())]

    CellArray = Data.GetPolys()
    Polygons = CellArray.GetData()
    faces = [[Polygons.GetValue(j) for j in xrange(i*4 + 1, i*4 + 4)]
             for i in xrange(0, CellArray.GetNumberOfCells())]

    PointData = Data.GetPointData()
    print("Loading 1 (named \'{1}\') out of {0} scalars in file {2}...".
          format(Reader.GetNumberOfScalarsInFile(),
                 Reader.GetScalarsNameInFile(0), filename))
    ScalarsArray = PointData.GetArray(Reader.GetScalarsNameInFile(0))
    if ScalarsArray:
        scalars = [ScalarsArray.GetValue(i)
                   for i in xrange(0, ScalarsArray.GetSize())]
    else:
        scalars = []

    if return_arrays:
        return np.array(points), np.array(faces), np.array(scalars), n_vertices
    else:
        return points, faces, scalars, n_vertices

def write_scalars(vtk_file, points, indices, faces, LUTs=[], LUT_names=[]):
    """
    Save scalars into a VTK-format file.

    Scalar definition includes specification of a lookup table.
    The definition of a lookup table is optional. If not specified,
    the default VTK table will be used (and tableName should be "default").

    SCALARS dataName dataType numComp
    LOOKUP_TABLE tableName

    Parameters
    ----------
    vtk_file : string
        path of the output VTK file
    points :  list of 3-tuples of floats
        each element has 3 numbers representing the coordinates of the points
    indices : list of integers
        indices of vertices
    faces : list of 3-tuples of integers
        indices to the three vertices of a face on the mesh
    LUTs : list of lists of floats
        each list contains values assigned to the vertices
    LUT_names : list of strings
        each element is the name of a LUT

    Example
    -------
    >>> import random
    >>> from mindboggle.utils.io_vtk import write_scalars
    >>> points = [[random.random() for i in [1,2,3]] for j in xrange(0,4)]
    >>> indices = [1,2,3,0]
    >>> faces = [[1,2,3],[0,1,3]]
    >>> LUT_names = ['curv','depth']
    >>> LUTs=[[random.random() for i in xrange(1,5)] for j in [1,2]]
    >>> write_scalars('test_write_scalars.vtk', points, indices, faces,
    >>>               LUTs=LUTs, LUT_names=LUT_names)

    """
    import os
    from mindboggle.utils.io_vtk import write_vtk_header, write_vtk_points, \
         write_vtk_vertices, write_vtk_faces, write_vtk_LUT

    vtk_file = os.path.join(os.getcwd(), vtk_file)

    Fp = open(vtk_file,'w')
    write_vtk_header(Fp)
    write_vtk_points(Fp, points)
    write_vtk_vertices(Fp, indices)
    write_vtk_faces(Fp, faces)
    if len(LUTs) > 0:
        # Make sure that LUTs is a list of lists
        if type(LUTs[0]) != list:
            LUTs = [LUTs]
        for i, LUT in enumerate(LUTs):
            if i == 0:
                if len(LUT_names) == 0:
                    LUT_name = 'scalars'
                else:
                    LUT_name = LUT_names[i]
                write_vtk_LUT(Fp, LUT, LUT_name)
            else:
                if len(LUT_names) < i + 1:
                    LUT_name = 'scalars'
                else:
                    LUT_name  = LUT_names[i]
                write_vtk_LUT(Fp, LUT, LUT_name, at_LUT_begin=False)
    Fp.close()

    return vtk_file

def rewrite_scalars(input_vtk, output_vtk, new_scalars, filter_scalars=[]):
    """
    Load VTK format file and save a subset of scalars into a new file.

    Parameters
    ----------
    input_vtk : input VTK file [string]
    output_vtk : output VTK file [string]
    new_scalars : new scalar values for VTK file
    filter_scalars : (optional)
        scalar values used to filter faces (positive values retained)

    """
    import os
    from mindboggle.utils.mesh_operations import inside_faces
    from mindboggle.utils.io_vtk import write_vtk_header, write_vtk_points, \
         write_vtk_vertices, write_vtk_faces, write_vtk_LUT, \
         load_scalar

    # Output VTK file to current working directory
    output_vtk = os.path.join(os.getcwd(), output_vtk)

    # Load VTK file
    points, faces, scalars, n_vertices = load_scalar(input_vtk, return_arrays=1)

    # Find indices to nonzero values
    indices = range(n_vertices)
    if len(filter_scalars) > 0:
        indices_nonzero = [i for i,x in enumerate(filter_scalars) if int(x) > 0]
        # Remove surface mesh faces whose three vertices are not all in indices
        faces = inside_faces(faces, indices_nonzero)

    # Lookup lists for saving to VTK format files
    LUTs = [new_scalars]
    LUT_names = ['scalars']

    # Write VTK file
    Fp = open(output_vtk,'w')
    write_vtk_header(Fp)
    write_vtk_points(Fp, points)
    write_vtk_vertices(Fp, indices)
    write_vtk_faces(Fp, faces)
    if len(LUTs) > 0:
        for i, LUT in enumerate(LUTs):
            if i == 0:
                if len(LUT_names) == 0:
                    LUT_name = 'scalars'
                else:
                    LUT_name = LUT_names[i]
                write_vtk_LUT(Fp, LUT, LUT_name)
            else:
                if len(LUT_names) < i + 1:
                    LUT_name = 'scalars'
                else:
                    LUT_name  = LUT_names[i]
                write_vtk_LUT(Fp, LUT, LUT_name, at_LUT_begin=False)
    Fp.close()

    return output_vtk

def write_mean_shapes_table(filename, column_names, labels, nonlabels,
                            area_file, depth_file, mean_curvature_file,
                            gauss_curvature_file,
                            max_curvature_file, min_curvature_file,
                            thickness_file='', convexity_file=''):
    """
    Make a table of mean values per label per measure.

    Parameters
    ----------
    filename :  output filename (without path)
    column_names :  names of columns [list of strings]
    labels :  list (same length as values)
    nonlabels : list of integer labels to be excluded
    area_file :  name of file containing per-vertex surface areas
    *shape_files :  arbitrary number of vtk files with scalar values

    Returns
    -------
    means_file : table file name for mean shape values
    norm_means_file : table file name for mean shape values normalized by area

    Example
    -------
    >>> import os
    >>> from mindboggle.utils.io_vtk import load_scalar, write_mean_shapes_table
    >>> filename = 'test_write_mean_shapes_table.txt'
    >>> column_names = ['labels', 'area', 'depth', 'mean_curvature',
    >>>                 'gauss_curvature', 'max_curvature', 'min_curvature']
    >>> data_path = os.environ['MINDBOGGLE_DATA']
    >>> label_file = os.path.join(data_path, 'subjects', 'MMRR-21-1',
    >>>              'label', 'lh.labels.DKT25.manual.vtk')
    >>> points, faces, labels, n_vertices = load_scalar(label_file, True)
    >>> nonlabels = [-1]
    >>> area_file = os.path.join(data_path, 'measures',
    >>>             '_hemi_lh_subject_MMRR-21-1', 'lh.pial.area.vtk')
    >>> depth_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.depth.vtk')
    >>> mean_curvature_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.curv.avg.vtk')
    >>> gauss_curvature_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.curv.gauss.vtk')
    >>> max_curvature_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.curv.max.vtk')
    >>> min_curvature_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.curv.min.vtk')
    >>> write_mean_shapes_table(filename, column_names, labels, nonlabels,
    >>>                         area_file, depth_file, mean_curvature_file,
    >>>                         gauss_curvature_file,
    >>>                         max_curvature_file, min_curvature_file,
    >>>                         thickness_file='', convexity_file='')

    """
    import os
    from mindboggle.utils.io_file import write_table
    from mindboggle.measure.measure_functions import mean_value_per_label
    from mindboggle.utils.io_vtk import load_scalar

    shape_files = [depth_file, mean_curvature_file, gauss_curvature_file,
                   max_curvature_file, min_curvature_file]
    if len(thickness_file) > 0:
        shape_files.append(thickness_file)
    if len(convexity_file) > 0:
        shape_files.append(convexity_file)

    # Load per-vertex surface area file
    points, faces, areas, n_vertices = load_scalar(area_file, return_arrays=1)
    mean_values, norm_mean_values, surface_areas, \
        label_list = mean_value_per_label(areas, areas, labels, nonlabels)

    columns = []
    norm_columns = []
    columns.append(surface_areas)
    norm_columns.append(surface_areas)

    for shape_file in shape_files:

        points, faces, values, n_vertices = load_scalar(shape_file, return_arrays=1)

        mean_values, norm_mean_values, surface_areas, \
            label_list = mean_value_per_label(values, areas, labels, nonlabels)

        columns.append(mean_values)
        norm_columns.append(norm_mean_values)

    means_file = os.path.join(os.getcwd(), filename)
    write_table(label_list, columns, column_names, means_file)

    norm_means_file = os.path.join(os.getcwd(), 'norm_' + filename)
    write_table(label_list, norm_columns, column_names, norm_means_file)

    return means_file, norm_means_file

def write_vertex_shape_table(filename, column_names, indices, area_file,
                             depth_file, mean_curvature_file, gauss_curvature_file,
                             max_curvature_file, min_curvature_file,
                             thickness_file='', convexity_file='',
                             segment_IDs=[], nonsegment_IDs=[]):
    """
    Make a table of shape values per vertex per label per measure.

    Parameters
    ----------
    filename : output filename (without path)
    column_names : names of columns [list of strings]
    indices : list of integers
        indices to vertices to compute shapes
    area_file : name of file containing per-vertex surface areas
    *shape_files : arbitrary number of vtk files with scalar values
    segment_IDs : numpy array of integers (optional)
        IDs assigning all vertices to segments
        (depth is normalized by the maximum depth value in a segment)
    nonsegment_IDs : list of integers
        segment IDs to be excluded

    Returns
    -------
    shape_table : table file name for vertex shape values

    Example
    -------
    >>> import os
    >>> from mindboggle.utils.io_vtk import load_scalar, write_vertex_shape_table
    >>> from mindboggle.utils.mesh_operations import find_neighbors, detect_boundaries
    >>> from mindboggle.info.sulcus_boundaries import sulcus_boundaries
    >>> data_path = os.environ['MINDBOGGLE_DATA']
    >>> filename = 'test_write_vertex_shape_table.txt'
    >>> column_names = ['labels', 'area', 'depth', 'mean_curvature',
    >>>                 'gauss_curvature', 'max_curvature', 'min_curvature']
    >>> label_file = os.path.join(data_path, 'subjects', 'MMRR-21-1',
    >>>              'label', 'lh.labels.DKT25.manual.vtk')
    >>> points, faces, labels, n_vertices = load_scalar(label_file, True)
    >>> mesh_indices = find_neighbors(faces, n_vertices)
    >>> neighbor_lists = find_neighbors(faces, n_vertices)
    >>> sulci_file = os.path.join(data_path, 'results', 'features',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'sulci.vtk')
    >>> points, faces, sulcus_IDs, n_vertices = load_scalar(sulci_file, True)
    >>> sulcus_indices = [i for i,x in enumerate(sulcus_IDs) if x > -1]
    >>> indices, label_pairs, foo = detect_boundaries(sulcus_indices, labels,
    >>>     neighbor_lists)
    >>> nonsegments = [-1]
    >>> area_file = os.path.join(data_path, 'measures',
    >>>             '_hemi_lh_subject_MMRR-21-1', 'lh.pial.area.vtk')
    >>> depth_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.depth.vtk')
    >>> mean_curvature_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.curv.avg.vtk')
    >>> gauss_curvature_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.curv.gauss.vtk')
    >>> max_curvature_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.curv.max.vtk')
    >>> min_curvature_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.curv.min.vtk')
    >>> write_vertex_shape_table(filename, column_names, indices,
    >>>     area_file, depth_file, mean_curvature_file, gauss_curvature_file,
    >>>     max_curvature_file, min_curvature_file, thickness_file='',
    >>>     convexity_file='', segment_IDs=sulcus_IDs, nonsegment_IDs=nonsegments)

    """
    import os
    import numpy as np
    from mindboggle.utils.io_file import write_table
    from mindboggle.utils.io_vtk import load_scalar

    shape_files = [area_file, depth_file, mean_curvature_file,
                   gauss_curvature_file, max_curvature_file, min_curvature_file]
    if len(thickness_file):
        shape_files.append(thickness_file)
    if len(convexity_file):
        shape_files.append(convexity_file)

    columns = []
    for i, shape_file in enumerate(shape_files):

        points, faces, values, n_vertices = load_scalar(shape_file, return_arrays=1)
        columns.append(values[indices])

        # Store depths to normalize
        if shape_files[i] == depth_file:
            depths = values

    # Normalize depth values by maximum depth per segment
    unique_segment_IDs = np.unique(segment_IDs)
    unique_segment_IDs = [x for x in unique_segment_IDs if x not in nonsegment_IDs]
    if len(unique_segment_IDs):
        for segment_ID in unique_segment_IDs:
            indices_segment = [i for i,x in enumerate(segment_IDs)
                               if x == segment_ID]
            if len(indices_segment):
                max_depth_segment = max(depths[indices_segment])
                depths[indices_segment] = depths[indices_segment] / max_depth_segment
        column_names.append('norm_depth')
        columns.append(depths[indices])
    print(len(column_names), len(columns))
    shape_table = os.path.join(os.getcwd(), filename)
    write_table(segment_IDs[indices], columns, column_names, shape_table)

    return shape_table

def load_vtk_vertices(Filename):
    """Load VERTICES segment from a VTK file

    Parameters
    ----------
    Filename : string
        The path/filename of a VTK format file.

    Returns
    -------
    Vertices : a list of integers
        Each element is an integer defined in VERTICES segment of the VTK file.
        The integer is an index referring to a point defined in POINTS segment of the VTK file.

    Notes
    ------
        We assume that VERTICES segment is organized as one line,
        the first column of which is the number of vertices.
        Vertices here are as vertices in VTK terminology. It may not be the vertices in your 3-D surface.

    """
    import vtk

    Reader = vtk.vtkDataSetReader()
    Reader.SetFileName(Filename)
    Reader.Update()

    Data = Reader.GetOutput()

    Vrts = Data.GetVerts()
    Vertices = [Vrts.GetData().GetValue(i) for i in xrange(1, Vrts.GetSize())]

    return Vertices

def load_lines(Filename):
    """
    Load LINES from a VTK file, along with the scalar values.

    The line that extracts vertices from a VTK
    iterates from 1 to Vrts.GetSize(), rather than from 0.

    Parameters
    ----------
    Filename : string
        The path/filename of a VTK format file.

    Returns
    -------
    lines : list of 2-tuple of integers
        Each element is a 2-tuple of IDs (i.e., indexes) of two points defined in POINTS segment of the VTK file
    scalars : list of floats
        Each element is a scalar value corresponding to a vertex

    """
    import vtk

    Reader = vtk.vtkDataSetReader()
    Reader.SetFileName(Filename)
    Reader.Update()

    Data = Reader.GetOutput()
    Lns = Data.GetLines()

    lines  = [[Lns.GetData().GetValue(j) for j in xrange(i*3+1, i*3+3) ]
              for i in xrange(Data.GetNumberOfLines())]

    PointData = Data.GetPointData()
    print "There are", Reader.GetNumberOfscalarsInFile(), "scalars in file", Filename
    print "Loading the scalar", Reader.GetScalarsNameInFile(0)
    ScalarsArray = PointData.GetArray(Reader.GetScalarsNameInFile(0))
    scalars = [ScalarsArray.GetValue(i) for i in xrange(0, ScalarsArray.GetSize())]

    return lines, scalars

def write_lines(vtk_file, points, indices, lines, LUTs=[], LUT_names=[]):
    """
    Save connected line segments to a VTK file.

    Parameters
    ----------
    vtk_file : string
        path of the output VTK file
    points :  list of 3-tuples of floats
        each element has 3 numbers representing the coordinates of the points
    indices : list of integers
        indices of vertices
    lines : list of 2-tuples of integers
        Each element is an edge on the mesh, consisting of 2 integers
        representing the 2 vertices of the edge
    LUTs : list of lists of floats
        each list contains values assigned to the vertices
    LUT_names : list of strings
        each element is the name of a LUT

    Example
    -------
    >>> import random
    >>> points = [[random.random() for i in range(3)] for j in xrange(5)]
    >>> indices = [0,1,2,3,4]
    >>> lines = [[1,2],[3,4]]  # ?
    >>> LUT_names = ['curv','depth']
    >>> LUTs=[[random.random() for i in range(6)] for j in range(2)]
    >>> write_lines('test_write_lines.vtk', points, indices, lines,
    >>>             LUTs=LUTs, LUT_names=LUT_names)

    """
    import os
    from mindboggle.utils.io_vtk import write_vtk_header, write_vtk_points, \
         write_vtk_vertices, write_vtk_faces, write_vtk_LUT

    vtk_file = os.path.join(os.getcwd(), vtk_file)

    Fp = open(vtk_file,'w')
    write_vtk_header(Fp)
    write_vtk_points(Fp, points)
    write_vtk_vertices(Fp, indices)
    for i in xrange(0,len(lines)):
        lines[i] = str(lines[i][0]) + " " + str(lines[i][1]) + "\n"
    write_vtk_faces(Fp, lines)
    if len(LUTs) > 0:
        for i, LUT in enumerate(LUTs):
            if i == 0:
                write_vtk_LUT(Fp, LUT, LUT_names[i])
            else:
                write_vtk_LUT(Fp, LUT, LUT_names[i], at_LUT_begin=False)
    Fp.close()


#=============================================================================
# Functions for converting FreeSurfer files to VTK format
#=============================================================================

def freesurface_to_vtk(surface_file):
    """
    Convert FreeSurfer surface file to VTK format.
    """
    import os
    from mindboggle.utils.io_free import read_surface
    from mindboggle.utils.io_vtk import write_vtk_header, write_vtk_points, write_vtk_faces

    points, faces = read_surface(surface_file)

    vtk_file = os.path.join(os.getcwd(),
                            os.path.basename(surface_file + '.vtk'))
    Fp = open(vtk_file, 'w')
    write_vtk_header(Fp, Title='vtk output from ' + surface_file)
    write_vtk_points(Fp, points)
    write_vtk_faces(Fp, faces)
    Fp.close()

    return vtk_file

def freecurvature_to_vtk(file_string, surface_file, hemi, subject, subjects_path):
    """
    Convert FreeSurfer curvature, thickness, or convexity file to VTK format.

    Parameters
    ----------
    file_string : string
        string for FreeSurfer file: 'curv', 'thickness', 'sulc.pial'
    surface_file : string  (name of VTK surface file)
    hemi : string indicating left or right hemisphere
    subject : string
        name of subject directory
    subjects_path: string
        path to subject directory

    Returns
    -------
    vtk_file : string
        name of output VTK file, where each vertex is assigned
        the corresponding shape value.

    """
    import os
    from mindboggle.utils.io_free import read_curvature
    from mindboggle.utils.io_vtk import load_scalar, write_scalars

    filename = os.path.join(subjects_path, subject, 'surf',
                            hemi + '.' + file_string)
    vtk_file = os.path.join(os.getcwd(), file_string + '.vtk')

    curvature_values = read_curvature(filename)

    # Load VTK surface
    points, faces, scalars, n_vertices = load_scalar(surface_file, return_arrays=0)

    LUTs = [curvature_values]
    LUT_names = [file_string]
    write_scalars(vtk_file, points, range(n_vertices), faces, LUTs, LUT_names)

    return vtk_file

def freeannot_to_vtk(surface_file, hemi, subject, subjects_path, annot_name):
    """
    Load a FreeSurfer .annot file and save as a VTK format file.

    Parameters
    ----------
    surface_file : string  (name of VTK surface file)
    annot_file : strings  (name of FreeSurfer .annot file)

    Returns
    -------
    labels : list of integers (one label per vertex)
    vtk_file : output VTK file

    """
    import os
    import nibabel as nb
    from mindboggle.utils.io_vtk import load_scalar, write_scalars

    annot_file = os.path.join(subjects_path, subject, 'label',
                              hemi + '.' + annot_name + '.annot')

    labels, colortable, names = nb.freesurfer.read_annot(annot_file)

    # Load FreeSurfer surface
    #from utils.io_file import read_surface
    #points, faces = read_surface(surface_file)

    # Load VTK surface
    points, faces, scalars, n_vertices = load_scalar(surface_file, return_arrays=0)

    output_stem = os.path.join(os.getcwd(),
                  os.path.basename(surface_file.strip('.vtk')))
    vtk_file = output_stem + '.' + annot_name.strip('.annot') + '.vtk'

    LUTs = [labels.tolist()]
    LUT_names = ['Labels']
    write_scalars(vtk_file, points, range(n_vertices), faces, LUTs, LUT_names)

    return labels, vtk_file

def vtk_to_freelabels(hemi, surface_file, label_numbers, label_names,
                      RGBs, scalar_name):
    """
    Write FreeSurfer .label files from a labeled VTK surface mesh.

    From https://surfer.nmr.mgh.harvard.edu/fswiki/LabelsClutsAnnotationFiles:

        "A label file is a text file capturing a list of vertices belonging to a region,
        including their spatial positions(using R,A,S coordinates). A label file
        corresponds only to a single label, thus contains only a single list of vertices"::

            1806
            7  -22.796  -66.405  -29.582 0.000000
            89  -22.273  -43.118  -24.069 0.000000
            138  -14.142  -81.495  -30.903 0.000000
            [...]

    Parameters
    ----------
    hemi :  hemisphere [string]
    surface_file :  vtk surface mesh file with labels [string]
    label_numbers :  label numbers [list of strings]
    label_names :  label names [list of strings]
    RGBs :  list of label RGB values for later conversion to a .annot file
    scalar_name :  name of scalar values in vtk file [string]

    Returns
    -------
    label_files :  list of .label file names (order must match label list)
    colortable :  file with list of labels and RGB values
                 NOTE: labels are identified by the colortable's RGB values

    """
    import os
    import numpy as np
    import vtk

    def string_vs_list_check(var):
        """
        Check type to make sure it is a string.

        (if a list, return the first element)
        """

        # Check type:
        if type(var) == str:
            return var
        elif type(var) == list:
            return var[0]
        else:
            os.error("Check format of " + var)

    # Check type to make sure the filename is a string
    # (if a list, return the first element)
    surface_file = string_vs_list_check(surface_file)

    # Initialize list of label files and output colortable file
    label_files = []
    #relabel_file = os.path.join(os.getcwd(), 'relabel_annot.txt')
    #f_relabel = open(relabel_file, 'w')
    colortable = os.path.join(os.getcwd(), 'colortable.ctab')
    f_rgb = open(colortable, 'w')

    # Loop through labels
    irgb = 0
    for ilabel, label_number in enumerate(label_numbers):

        # Check type to make sure the number is an int
        label_number = int(label_number)
        label_name = label_names[ilabel]

        # Load surface
        reader = vtk.vtkDataSetReader()
        reader.SetFileName(surface_file)
        reader.ReadAllScalarsOn()
        reader.Update()
        data = reader.GetOutput()
        d = data.GetPointData()
        labels = d.GetArray(scalar_name)

        # Write vertex index, coordinates, and 0
        count = 0
        npoints = data.GetNumberOfPoints()
        L = np.zeros((npoints,5))
        for i in range(npoints):
            label = labels.GetValue(i)
            if label == label_number:
                L[count,0] = i
                L[count,1:4] = data.GetPoint(i)
                count += 1

        # Save the label file
        if count > 0:
            irgb += 1

            # Write to relabel_file
            #if irgb != label_number:
            #    f_relabel.writelines('{0} {1}\n'.format(irgb, label_number))

            # Write to colortable
            f_rgb.writelines('{0} {1} {2}\n'.format(
                             irgb, label_name, RGBs[ilabel]))

            # Store in list of .label files
            label_file = hemi + '.' + label_name + '.label'
            label_file = os.path.join(os.getcwd(), label_file)
            label_files.append(label_file)

            # Write to .label file
            f = open(label_file, 'w')
            f.writelines('#!ascii label\n' + str(count) + '\n')
            for i in range(npoints):
                if any(L[i,:]):
                    pr = '{0} {1} {2} {3} 0\n'.format(
                         np.int(L[i,0]), L[i,1], L[i,2], L[i,3])
                    f.writelines(pr)
                else:
                    break
            f.close()
    f_rgb.close()
    #f_relabel.close()

    return label_files, colortable  #relabel_file
