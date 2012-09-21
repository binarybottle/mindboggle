#!/usr/bin/python
"""
Functions related to reading and writing VTK format files.

1. Functions for writing basic VTK elements
2. Functions for loading and writing VTK files
3. Functions specific to Mindboggle features


Authors:
    - Forrest Sheng Bao  (forrest.bao@gmail.com)  http://fsbao.net
    - Arno Klein  (arno@mindboggle.info)  http://binarybottle.com

Copyright 2012,  Mindboggle team (http://mindboggle.info), Apache v2.0 License

"""

#=========================================
# Functions for writing basic VTK elements
#=========================================

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

def write_vtk_points(Fp, Points, dataType="float"):
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

    Fp.write('POINTS {0} {1}\n'.format(len(Points), dataType))

    n = np.shape(Points)[1]
    for point in Points:
        if n == 3:
            [R, A, S] = point
            Fp.write('{0} {1} {2}\n'.format(R, A, S))
        elif n == 2:
            [R, A] = point
            Fp.write('{0} {1}\n'.format(R, A))
        else:
            print('ERROR: Unrecognized number of coordinates per point')

def write_vtk_faces(Fp, Faces):
    """
    Write vertices forming triangular meshes,
    the POLYGONS section in DATASET POLYDATA section::

        POLYGONS 301978 1207912
        3 0 1 4
        ...

    """
    import numpy as np

    n = np.shape(Faces)[1]
    if n == 3:
        face_name = 'POLYGONS '
        Fp.write('{0} {1} {2}\n'.format(face_name, len(Faces),
                 len(Faces) * (n + 1)))
    elif n == 2:
        face_name = 'LINES '
        Fp.write('{0} {1}\n'.format(face_name, len(Faces),
                 len(Faces) * (n + 1)))
    else:
        print('ERROR: Unrecognized number of vertices per face')

    for face in Faces:
        if n == 3:
            [V0, V1, V2] = face
            Fp.write('{0} {1} {2} {3}\n'.format(n, V0, V1, V2))
        elif n == 2:
            [V0, V1] = face
            Fp.write('{0} {1} {2}\n'.format(n, V0, V1))

def write_vtk_vertices(Fp, Vertices):
    """
    Write vertices, the VERTICES section in DATASET POLYDATA section::

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
             len(Vertices), len(Vertices) + 1, len(Vertices)))
    [Fp.write('{0} '.format(i)) for i in Vertices]
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

#============================================
# Functions for loading and writing VTK files
#============================================

def load_scalar(filename, return_arrays=1):
    """
    Load a VTK-format scalar map that contains only one SCALAR segment.

    Parameters
    ----------
    filename : string
        The path/filename of a VTK format file.
    return_arrays : return numpy arrays instead of lists of lists below (1=yes, 0=no)

    Returns
    -------
    Points : list of lists of floats (see return_arrays)
        Each element is a list of 3-D coordinates of a vertex on a surface mesh
    Faces : list of lists of integers (see return_arrays)
        Each element is list of 3 IDs of vertices that form a face
        on a surface mesh
    Scalars : list of floats (see return_arrays)
        Each element is a scalar value corresponding to a vertex

    Example
    -------
    >>> Points, Faces, Scalars = load_scalar('lh.pial.depth.vtk')

    """
    import vtk
    if return_arrays:
        import numpy as np

    Reader = vtk.vtkDataSetReader()
    Reader.SetFileName(filename)
    Reader.ReadAllScalarsOn()  # Activate the reading of all scalars
    Reader.Update()

    Data = Reader.GetOutput()
    Points = [list(Data.GetPoint(point_id))
              for point_id in xrange(0, Data.GetNumberOfPoints())]

    #Vrts = Data.GetVerts()
    #Vertices = [Vrts.GetData().GetValue(i) for i in xrange(1, Vrts.GetSize())]

    CellArray = Data.GetPolys()
    Polygons = CellArray.GetData()
    Faces = [[Polygons.GetValue(j) for j in xrange(i*4 + 1, i*4 + 4)]
             for i in xrange(0, CellArray.GetNumberOfCells())]

    PointData = Data.GetPointData()
    print("Loading {0} {1} scalars in file {2}...".
          format(Reader.GetNumberOfScalarsInFile,
                 Reader.GetScalarsNameInFile(0), filename))
    ScalarsArray = PointData.GetArray(Reader.GetScalarsNameInFile(0))
    if ScalarsArray:
        Scalars = [ScalarsArray.GetValue(i)
                   for i in xrange(0, ScalarsArray.GetSize())]
    else:
        Scalars = []

    if return_arrays:
        return np.array(Points), np.array(Faces), np.array(Scalars)
    else:
        return Points, Faces, Scalars

def write_scalars(vtk_file, Points, Vertices, Faces, LUTs=[], LUT_names=[]):
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
        The path of the VTK file to save sulci
    Points :  list of 3-tuples of floats
        Each element has 3 numbers representing the coordinates of the points
    Vertices : list of integers
        IDs of vertices that are part of a sulcus
    Faces : list of 3-tuples of integers
        Each element is a face on the mesh, consisting of 3 integers
        representing the 3 vertices of the face
    LUTs : list of lists of floats
        Each element is a list of floats representing a scalar map for the mesh
    LUT_names : list of strings
        Each element is the name of a scalar map, e.g., curv, depth.

    Example
    -------
    >>> import random
    >>> from utils.io_vtk import write_scalars
    >>> Points = [[random.random() for i in [1,2,3]] for j in xrange(0,4)]
    >>> Vertices = [1,2,3,0]
    >>> Faces = [[1,2,3],[0,1,3]]
    >>> LUT_names = ['curv','depth']
    >>> LUTs=[[random.random() for i in xrange(1,5)] for j in [1,2]]
    >>> write_scalars('test.vtk',Points, Vertices, Faces, LUTs=LUTs, \
                      LUT_names=LUT_names)

    """
    import os
    from utils import io_vtk

    vtk_file = os.path.join(os.getcwd(), vtk_file)

    Fp = open(vtk_file,'w')
    io_vtk.write_vtk_header(Fp)
    io_vtk.write_vtk_points(Fp, Points)
    io_vtk.write_vtk_vertices(Fp, Vertices)
    io_vtk.write_vtk_faces(Fp, Faces)
    if len(LUTs) > 0:
        # Make sure that LUTs is a list of lists
        if type(LUTs[0]) != list:
            LUTs = [LUTs]
        for i, LUT in enumerate(LUTs):
            if i == 0:
                if len(LUT_names) == 0:
                    LUT_name = 'Scalars'
                else:
                    LUT_name = LUT_names[i]
                io_vtk.write_vtk_LUT(Fp, LUT, LUT_name)
            else:
                if len(LUT_names) < i + 1:
                    LUT_name = 'Scalars'
                else:
                    LUT_name  = LUT_names[i]
                io_vtk.write_vtk_LUT(Fp, LUT, LUT_name, at_LUT_begin=False)
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
                     scalar values used to filter faces (non-zero are retained)

    """
    import os
    from utils import io_vtk
    from utils.mesh_operations import inside_faces

    # Output VTK file to current working directory
    output_vtk = os.path.join(os.getcwd(), output_vtk)

    # Load VTK file
    Points, Faces, Scalars = io_vtk.load_scalar(input_vtk, return_arrays=1)

    # Find indices to nonzero values
    indices = range(len(Scalars))
    if len(filter_scalars) > 0:
        indices_nonzero = [i for i,x in enumerate(filter_scalars) if int(x) > 0]
    else:
        indices_nonzero = indices

    # Remove surface mesh faces whose three vertices are not all in indices
    faces_indices = inside_faces(Faces, indices_nonzero)

    # Lookup lists for saving to VTK format files
    LUTs = [new_scalars]
    LUT_names = ['Scalars']

    # Write VTK file
    Fp = open(output_vtk,'w')
    io_vtk.write_vtk_header(Fp)
    io_vtk.write_vtk_points(Fp, Points)
    io_vtk.write_vtk_vertices(Fp, indices)
    io_vtk.write_vtk_faces(Fp, faces_indices)
    if len(LUTs) > 0:
        for i, LUT in enumerate(LUTs):
            if i == 0:
                if len(LUT_names) == 0:
                    LUT_name = 'Scalars'
                else:
                    LUT_name = LUT_names[i]
                io_vtk.write_vtk_LUT(Fp, LUT, LUT_name)
            else:
                if len(LUT_names) < i + 1:
                    LUT_name = 'Scalars'
                else:
                    LUT_name  = LUT_names[i]
                io_vtk.write_vtk_LUT(Fp, LUT, LUT_name, at_LUT_begin=False)
    Fp.close()

    return output_vtk

def write_mean_shapes_table(filename, column_names, labels, area_file,
                            depth_file, mean_curvature_file,
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
    area_file :  name of file containing per-vertex surface areas
    *shape_files :  arbitrary number of vtk files with scalar values

    Returns
    -------
    means_file : table file name for mean values
    norm_means_file : table file name for mean values normalized by area

    """
    import os
    from utils.io_vtk import load_scalar
    from utils.io_file import write_table
    from measure.measure_functions import mean_value_per_label

    shape_files = [depth_file, mean_curvature_file, gauss_curvature_file,
                   max_curvature_file, min_curvature_file]
    if len(thickness_file) > 0:
        shape_files.append(thickness_file)
    if len(convexity_file) > 0:
        shape_files.append(convexity_file)

    columns = []
    norm_columns = []
    for i, shape_file in enumerate(shape_files):

        Points, Faces, areas = load_scalar(area_file, return_arrays=1)
        Points, Faces, values = load_scalar(shape_file, return_arrays=1)

        mean_values, norm_mean_values, surface_areas, \
            label_list = mean_value_per_label(values, areas, labels)

        if i == 0:
            columns.append(surface_areas)
            norm_columns.append(surface_areas)
        else:
            columns.append(mean_values)
            norm_columns.append(norm_mean_values)

    means_file = os.path.join(os.getcwd(), filename)
    write_table(label_list, columns, column_names, means_file)

    norm_means_file = os.path.join(os.getcwd(), 'norm_' + filename)
    write_table(label_list, norm_columns, column_names, norm_means_file)

    return means_file, norm_means_file

def load_lines(Filename):
    """
    Load VERTICES from a VTK file, along with the scalar values.

    The line that extracts vertices from a VTK
    iterates from 1 to Vrts.GetSize(), rather than from 0.

    Parameters
    ----------
    Filename : string
        The path/filename of a VTK format file.

    Returns
    -------
    Vertexes : list of integers
        Each element is an ID (i.e., index) of a point defined in POINTS segment of the VTK file
    Scalars : list of floats
        Each element is a scalar value corresponding to a vertex
    """

    import vtk
    Reader = vtk.vtkDataSetReader()
    Reader.SetFileName(Filename)
    Reader.Update()

    Data = Reader.GetOutput()
    Lns = Data.GetLines()

    Lines  = [[Lns.GetData().GetValue(j) for j in xrange(i*3+1, i*3+3) ]
              for i in xrange(Data.GetNumberOfLines())]

    PointData = Data.GetPointData()
    print "There are", Reader.GetNumberOfScalarsInFile(), "scalars in file", Filename
    print "Loading the scalar", Reader.GetScalarsNameInFile(0)
    ScalarsArray = PointData.GetArray(Reader.GetScalarsNameInFile(0))
    Scalars = [ScalarsArray.GetValue(i) for i in xrange(0, ScalarsArray.GetSize())]

    return Lines, Scalars

def write_lines(vtk_file, Points, Vertices, Lines, LUTs=[], LUT_names=[]):
    """
    Save connected line segments to a VTK file.

    Parameters
    ----------
    vtk_file : string
        The path of the VTK file to save fundi
    Points :  list of 3-tuples of floats
        Each element has 3 numbers representing the coordinates of the points
    Vertices : list of integers
        IDs of vertices that are part of a fundus
    Lines : list of 2-tuples of integers
        Each element is an edge on the mesh, consisting of 2 integers
        representing the 2 vertices of the edge
    LUTs : list of lists of integers
        Each element is a list of integers representing a map for the mesh
    LUT_names : list of strings
        Each element is the name of a map, e.g., curv, depth.

    Example
    -------
    >>> import random
    >>> from utils import io_vtk
    >>> Points = [[random.random() for i in range(3)] for j in xrange(5)]
    >>> Vertices = [0,1,2,3,4]
    >>> Faces = [[1,2,3],[0,3,4]]
    >>> LUT_names = ['curv','depth']
    >>> LUTs=[[random.random() for i in range(6)] for j in range(2)]
    >>> io_vtk.write_scalars('test.vtk',Points, Vertices, Faces, LUTs=LUTs, \
                      LUT_names=LUT_names)

    """

    import os
    from utils import io_vtk

    vtk_file = os.path.join(os.getcwd(), vtk_file)

    Fp = open(vtk_file,'w')
    io_vtk.write_vtk_header(Fp)
    io_vtk.write_vtk_points(Fp, Points)
    io_vtk.write_vtk_vertices(Fp, Vertices)
    for i in xrange(0,len(Lines)):
        Lines[i] = str(Lines[i][0]) + " " + str(Lines[i][1]) + "\n"
    io_vtk.write_vtk_faces(Fp, Lines)
    if len(LUTs) > 0:
        for i, LUT in enumerate(LUTs):
            if i == 0:
                io_vtk.write_vtk_LUT(Fp, LUT, LUT_names[i])
            else:
                io_vtk.write_vtk_LUT(Fp, LUT, LUT_names[i],
                                        at_LUT_begin=False)
    Fp.close()
