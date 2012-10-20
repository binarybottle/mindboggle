#!/usr/bin/python
"""
Functions to extract folds, sulci, or identify sulci from folds.

Authors:
    - Arno Klein  (arno@mindboggle.info)  http://binarybottle.com
    - Yrjo Hame  (yrjo.hame@gmail.com)
    - Forrest Sheng Bao  (forrest.bao@gmail.com)  http://fsbao.net

Copyright 2012,  Mindboggle team (http://mindboggle.info), Apache v2.0 License

"""
#import sys
#import numpy as np
#from time import time
#from mindboggle.utils.io_vtk import load_scalars, write_scalar_lists, rewrite_scalar_lists
#from mindboggle.utils.mesh_operations import find_neighbors, detect_boundaries,\
#    segment, fill_holes, compute_distance
#from mindboggle.info.sulcus_boundaries import sulcus_boundaries

#===============================================================================
# Extract folds
#===============================================================================
def find_deep_vertices(depth_file, area_file, fraction_folds):
    """
    Find the deepest vertices in a surface mesh whose collective area
    is a given fraction of the total surface area of the mesh.

    Note: Resulting folds may have holes.

    Parameters
    ----------
    depth_file : str
        surface mesh file in VTK format with faces and depth scalar values
    area_file : str
        surface mesh file in VTK format with faces and surface area scalar values
    fraction_folds : float
        fraction of surface mesh considered folds

    Returns
    -------
    folds : array of integers
        an integer for every mesh vertex: 1 for fold, -1 for non-fold

    Examples
    --------
    >>> import os
    >>> from mindboggle.utils.io_vtk import load_scalars, write_scalar_lists
    >>> from mindboggle.extract.extract_folds import find_deep_vertices
    >>> from mindboggle.utils.mesh_operations import find_neighbors
    >>> data_path = os.environ['MINDBOGGLE_DATA']
    >>> depth_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.depth.vtk')
    >>> area_file = os.path.join(data_path, 'measures',
    >>>             '_hemi_lh_subject_MMRR-21-1', 'lh.pial.area.vtk')
    >>> folds = find_deep_vertices(depth_file, area_file, 0.5)
    >>> # Write results to vtk file and view with mayavi2:
    >>> from mindboggle.utils.io_vtk import rewrite_scalar_lists
    >>> rewrite_scalar_lists(depth_file, 'test_find_deep_vertices.vtk',
    >>>                      [folds], ['folds'], folds)
    >>> os.system('mayavi2 -m Surface -d test_find_deep_vertices.vtk &')

    """
    import numpy as np
    from time import time
    from mindboggle.utils.io_vtk import load_scalars

    print("Extract the deepest surface mesh vertices ({0} of surface area)...".
          format(fraction_folds))
    t0 = time()

    # Load depth and surface area values from VTK files
    points, faces, depths, n_vertices = load_scalars(depth_file, return_arrays=True)
    points, faces, areas, n_vertices = load_scalars(area_file, return_arrays=True)

    indices_asc = np.argsort(depths)
    indices_des = indices_asc[::-1]

    total_area = np.sum(areas)
    fraction_area = fraction_folds * total_area
    sum_area = 0
    folds = -1 * np.ones(len(areas))

    # Start by making fraction_area of the vertices folds
    start = np.round(fraction_folds * len(depths))
    folds[indices_des[0:start]] = 1
    sum_area = np.sum(areas[indices_des[0:start]])

    # If these initial vertices cover less than fraction_area,
    # add vertices until the remaining vertices' area exceeds fraction_area
    if sum_area <= fraction_area:
        for index in indices_des[start::]:
            folds[index] = 1
            sum_area += areas[index]
            if sum_area >= fraction_area:
                break
    # Otherwise, if these initial vertices cover more than fraction_area,
    # remove vertices until the remaining vertices' area is less than fraction_area
    else:
        start = np.round((1-fraction_folds) * len(depths))
        for index in indices_asc[start::]:
            folds[index] = -1
            sum_area += areas[index]
            if sum_area <= fraction_area:
                break

    print('  ...Extracted deep vertices ({1:.2f} seconds)'.format(time() - t0))

    return folds

#===============================================================================
# Extract individual folds
#===============================================================================
def extract_folds(depth_file, area_file, neighbor_lists, fraction_folds,
                  min_fold_size, do_fill_holes=True):
    """
    Use depth to extract folds from a triangular surface mesh.

    The resulting separately numbered folds may have holes
    resulting from shallower areas within a fold,
    so the largest connected set of background vertices are removed
    (presumed to be the background) and smaller sets of connected
    background vertices (presumed to be holes) are filled by fold number.

    Parameters
    ----------
    depth_file : str
        surface mesh file in VTK format with faces and depth scalar values
    area_file : str
        surface mesh file in VTK format with faces and surface area scalar values
    neighbor_lists : list of lists of integers
        each list contains indices to neighboring vertices
    fraction_folds : float
        fraction of surface mesh considered folds
    min_fold_size : int
        minimum fold size (number of vertices)
    do_fill_holes : Boolean
        segment and fill holes?

    Returns
    -------
    folds : array of integers
        fold numbers for all vertices (default -1 for non-fold vertices)
    n_folds :  int
        number of folds

    Examples
    --------
    >>> import os
    >>> from mindboggle.utils.io_vtk import load_scalars, write_scalar_lists
    >>> from mindboggle.utils.mesh_operations import find_neighbors, inside_faces
    >>> from mindboggle.extract.extract_folds import extract_folds
    >>> data_path = os.environ['MINDBOGGLE_DATA']
    >>> depth_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.depth.vtk')
    >>> area_file = os.path.join(data_path, 'measures',
    >>>             '_hemi_lh_subject_MMRR-21-1', 'lh.pial.area.vtk')
    >>> points, faces, depths, n_vertices = load_scalars(depth_file, return_arrays=0)
    >>> neighbor_lists = find_neighbors(faces, len(points))
    >>> folds, n_folds = extract_folds(depth_file, area_file, neighbor_lists,
    >>>     0.5, 50, False)
    >>> # Write results to vtk file and view with mayavi2:
    >>> #rewrite_scalar_lists(depth_file, 'test_extract_folds.vtk', folds, 'folds', folds)
    >>> indices = [i for i,x in enumerate(folds) if x > -1]
    >>> write_scalar_lists('test_extract_folds.vtk', points, indices,
    >>>     inside_faces(faces, indices), [folds], ['folds'])
    >>> os.system('mayavi2 -m Surface -d test_extract_folds.vtk &')

    """
    import numpy as np
    from time import time
    from mindboggle.utils.mesh_operations import segment, fill_holes
    from mindboggle.extract.extract_folds import find_deep_vertices

    fill_boundaries = True

    print("Extract folds from surface mesh...")
    t0 = time()

    # Extract folds (fraction of surface area covered by deeper vertices)
    folds = find_deep_vertices(depth_file, area_file, fraction_folds)

    # Segment folds of a surface mesh
    print("  Segment surface mesh into separate folds")
    t1 = time()
    folds = segment(np.where(folds == 1)[0], neighbor_lists,
                    seed_lists=[], min_region_size=min_fold_size)
    print('    ...Folds segmented ({0:.2f} seconds)'.format(time() - t1))
    n_folds = len([x for x in list(set(folds)) if x != -1])

    # If there are any folds, find and fill holes
    if n_folds > 0 and do_fill_holes:

        if fill_boundaries:
            folds = fill_hole_boundaries(folds, neighbor_lists)

        else:
            # Find nonfold vertices
            t2 = time()
            nonfold_indices = [i for i,x in enumerate(folds) if x==-1]

            # Segment holes in the folds
            print('  Segment holes in the folds...')
            holes = segment(nonfold_indices, neighbor_lists)
            n_holes = len([x for x in list(set(holes))])

            # If there are any holes
            if n_holes > 0:

                # Ignore the largest hole (the background) and renumber holes
                max_hole_size = 0
                max_hole_index = 0
                for ihole in range(n_holes):
                    I = np.where(holes == ihole)
                    if len(I) > max_hole_size:
                        max_hole_size = len(I)
                        max_hole_index = ihole
                holes[holes == max_hole_index] = -1
                if max_hole_index < n_holes:
                    holes[holes > max_hole_index] -= 1
                n_holes -= 1
                print('    ...{0} holes segmented ({1:.2f} seconds)'.
                      format(n_holes, time() - t2))

                # Fill holes
                t3 = time()
                folds = fill_holes(folds, holes, neighbor_lists)
                print('  Filled holes ({0:.2f} seconds)'.format(time() - t3))

    print('  ...Extracted folds in {1:.2f} seconds'.format(time() - t0))

    # Return folds, number of folds
    return folds, n_folds

#===============================================================================
# Identify sulci from folds
#===============================================================================
def identify_sulci_from_folds(folds, labels, neighbor_lists, label_pair_lists
                              sulcus_names=[]):
    """
    Identify sulcus folds in a brain surface according to a labeling protocol
    that includes a list of label pairs defining each sulcus.

    Definitions ::

    A fold is a group of connected, deep vertices.

    A ''label list'' is the list of labels used to define a single sulcus.

    A ''label pair list'' contains pairs of labels, where each pair
    defines a boundary between two labeled regions.
    No two label pair lists share a label pair.

    A ''sulcus ID'' uniquely identifies a sulcus.
    It is the index to a sulcus label list (or sulcus label pair list).

    Algorithm ::

      For each fold (vertices with the same fold label):

        Case 0: NO MATCH -- fold has no label

        Case 1: NO MATCH -- fold has only one label

          If the fold has only one label, remove the fold by assigning
          -1 to all vertices in this fold.

        Case 2: matching label set in sulcus

          If the set of labels in the fold is the same as in one of the
          protocol's sulci, assign the index to the corresponding
          label list to all vertices in the fold.

        Case 3: NO MATCH -- fold has no sulcus label pair

        Case 4: fold labels in one sulcus

          If the set of labels in the fold is a subset of labels in
          only one of the protocol's sulcus label lists, assign the index
          for that list to all vertices in the fold.
          (Ex: the labels in the fold are [1,2,3] and there is only one
           sulcus label list containing 1, 2, and 3: [1,2,3,4])

        Case 5: ambiguous -- fold labels in more than one sulcus
                          -- fold labels not contained by a sulcus

          Find label boundary pairs in the fold whose labels
          are not shared by any other label pairs in the fold,
          and store the sulcus IDs for these pairs.

          Assign a sulcus ID to fold vertices that have unique
          label pair labels (unique to ensure a label is not shared
          with another label pair); store unassigned vertices.

          If there are remaining vertices with duplicate label pair labels,
          construct seed lists of remaining label boundary vertices,
          segment into sets of vertices connected to label boundary seeds,
          and assign a sulcus ID to each segment.

    Parameters
    ----------
    labels : list of integers
        labels for all vertices
    folds : list of lists of integers
        each list contains indices to vertices of a fold
    neighbor_lists : list of lists of integers
        each list contains indices to neighboring vertices for each vertex
    label_pair_lists : list of sublists of subsublists of integers
        each subsublist contains a pair of labels, and the sublist of these
        label pairs represents the label boundaries defining a sulcus
    sulcus_names : list of strings (optional)
        names of sulci

    Returns
    -------
    sulci : array of integers
        sulcus numbers for all vertices, with -1s for non-sulcus vertices

    Examples
    --------
    >>> # Arguments
    >>> labels_file = sys.argv[1]
    >>> folds_file = sys.argv[2]
    >>> sulcus_names_file = sys.argv[3]
    >>> vtk_file = sys.argv[4]
    >>> # Load labels and folds (the second surface has to be inflated).
    >>> points, faces, labels, n_vertices = load_scalars(labels_file, return_arrays=0)
    >>> points, faces, folds, n_vertices = load_scalars(folds_file, return_arrays=0)
    >>> fid = open(sulcus_names_file, 'r')
    >>> sulcus_names = fid.readlines()
    >>> sulcus_names = [x.strip('\n') for x in sulcus_names]
    >>> # Calculate neighbor lists for all vertices
    >>> neighbor_lists = find_neighbors(faces, len(points))
    >>> # Prepare list of all unique sorted label pairs in the labeling protocol
    >>> label_pair_lists = sulcus_boundaries()
    >>> # Create a list of lists of folds
    >>> unique_folds = set(folds)
    >>> folds = []
    >>> for id in unique_folds:
    >>>     if id > 0:
    >>>         fold = [i for i,x in enumerate(folds) if x == id]
    >>>         folds.append(fold)
    >>> # Identify sulci from folds
    >>> sulci = identify_sulci_from_folds(labels, folds, neighbor_lists,
    >>>                                   label_pair_lists, sulcus_names)
    >>> # Finally, write points, faces and sulci to a new vtk file
    >>> rewrite_scalar_lists(labels_file, vtk_file, [sulci], ['sulci'], sulci)

    """
    import numpy as np
    from mindboggle.utils.mesh_operations import segment, detect_boundaries

    verbose = 0

    #---------------------------------------------------------------------------
    # Nested function
    #---------------------------------------------------------------------------
    def find_superset_subset_lists(labels, label_lists):
        """
        Find *label_lists* that are supersets or subsets of *labels*.

        Parameters
        ----------
        labels : list of integers
            label numbers
        label_lists : list of lists of integers
            each list contains label numbers

        Returns
        -------
        superset_indices : list of integers
            indices to label_lists that are a superset of labels
        subset_indices : list of integers
            indices to label_lists that are a subset of labels

        Example
        -------
        >>> find_superset_subset_lists([1,2],[[1,2],[3,4]])
        >>> [0]
        >>> find_superset_subset_lists([1,2],[[1,2,3],[1,2,5]])
        >>> [0, 1]
        >>> find_superset_subset_lists([1,2],[[2,3],[1,2,5]])
        >>> [1]

        """

        labels = set(labels)
        superset_indices = []
        subset_indices = []
        for Id, label_list in enumerate(label_lists):
            if labels.issubset(set(label_list)):
                superset_indices.append(Id)
            if set(label_list).issubset(labels):
                subset_indices.append(Id)

        return superset_indices, subset_indices

    #---------------------------------------------------------------------------
    # Prepare data structures
    #---------------------------------------------------------------------------
    # Array of sulcus IDs for fold vertices, initialized as -1.
    # Since we do not touch gyral vertices and vertices whose labels
    # are not in the label list, or vertices having only one label,
    # their sulcus IDs will remain -1.
    sulci = -1 * np.ones(len(neighbor_lists))

    # Prepare list of sulcus label lists (labels within a sulcus)
    label_lists = []
    for row in label_pair_lists:
        label_lists.append(list(np.unique(np.asarray(row))))

    # Prepare list of all unique sorted label pairs in the labeling protocol
    protocol_pairs = []
    [protocol_pairs.append(list(set(x)))
     for lst in label_pair_lists
     for x in lst
     if list(set(x)) not in protocol_pairs]

    #---------------------------------------------------------------------------
    # Loop through folds
    #---------------------------------------------------------------------------
    fold_numbers = [x for x in np.unique(folds) if x > -1]
    for n_fold in fold_numbers:
        fold = np.where(folds == n_fold)[0]
        special_case = False

        # List the labels in this fold
        fold_labels = [labels[vertex] for vertex in fold]
        unique_fold_labels = [int(x) for x in np.unique(fold_labels)]

        # Case 0: NO MATCH -- fold has no label
        if not len(unique_fold_labels):
            print("  Fold {0}: NO MATCH -- fold has no label")
            # Ignore: sulci already initialized with -1 values
            continue

        # Case 1: NO MATCH -- fold has only one label
        elif len(unique_fold_labels) == 1:
            print("  Fold {0}: NO MATCH -- fold has only one label ({1})".
                  format(n_fold, unique_fold_labels[0]))
            # Ignore: sulci already initialized with -1 values
            continue

        # Case 2: matching label set in sulcus
        elif unique_fold_labels in label_lists:
            if len(sulcus_names):
                print("  Fold {0}: matching label set in sulcus: {1} ({2})".
                    format(n_fold,
                    sulcus_names[label_lists.index(unique_fold_labels)],
                      ', '.join([str(x) for x in unique_fold_labels])))
            else:
                print("  Fold {0}: matching label set in sulcus ({1})".
                    format(n_fold,', '.join([str(x) for x in unique_fold_labels])))
            index = label_lists.index(unique_fold_labels)
            # Assign ID of the matching sulcus to all fold vertices
            sulci[fold] = index

        # Cases 3-5: at least one fold label but no perfect match
        else:
            # Find all label boundary pairs within the fold
            indices_fold_pairs, fold_pairs, unique_fold_pairs = detect_boundaries(
                fold, labels, neighbor_lists)

            # Find fold label pairs in the protocol (pairs are already sorted)
            fold_pairs_in_protocol = [x for x in unique_fold_pairs
                                      if x in protocol_pairs]
            if verbose:
                print("  Fold labels: {0}".
                      format(', '.join([str(x) for x in unique_fold_labels])))
                print("  Fold label pairs in protocol: {0}".
                      format(', '.join([str(x) for x in fold_pairs_in_protocol])))

            # Case 3: NO MATCH -- fold has no sulcus label pair
            if not len(fold_pairs_in_protocol):
                print("  Fold {0}: NO MATCH -- fold has no sulcus label pair".
                      format(n_fold))

            # Cases 4-5: labels in common between fold and sulcus/sulci
            else:

                # Find overlap of sulcus labels and fold labels
                superset_indices, subset_indices = find_superset_subset_lists(
                    unique_fold_labels, label_lists)

                # Cases 4: fold labels contained by one sulcus
                if len(superset_indices) == 1:
                    if len(sulcus_names):
                        print("  Fold {0}: fold labels in one sulcus: {1} ({2})".
                            format(n_fold, sulcus_names[superset_indices[0]],
                            ', '.join([str(x)
                            for x in label_lists[superset_indices[0]]])))
                    else:
                        print("  Fold {0}: fold labels in one sulcus: ({1})".
                            format(n_fold, ', '.join([str(x)
                            for x in label_lists[superset_indices[0]]])))
                    # Assign ID of matching sulcus to all fold vertices
                    sulci[fold] = superset_indices[0]

                # Case 5: ambiguous  -- fold labels in more than one sulcus
                #                    -- fold labels not contained by a sulcus
                else:
                    print("  Fold {0}: ambiguous -- "
                          "fold labels in more than one sulcus or "
                          "not contained by a sulcus".format(n_fold))
                    special_case = True

        # Special cases
        if special_case:

            # Find label boundary pairs in the fold whose labels
            # are and are not shared by any other label pairs
            # in the fold, and store the sulcus IDs for these pairs
            unique_pairs = []
            IDs_unique_pairs = []
            remainder_pairs = []
            IDs_remainder_pairs = []
            for pair in fold_pairs_in_protocol:
                labels_in_pairs = [x for sublst in fold_pairs_in_protocol
                                   for x in sublst]
                if len([x for x in labels_in_pairs if x in pair]) == 2:
                    unique_pairs.append(pair)
                    IDs_unique_pairs.extend(
                        [i for i,x in enumerate(label_pair_lists)
                         if np.sort(pair).tolist() in x])
                else:
                    remainder_pairs.append(pair)
                    IDs_remainder_pairs.extend([i
                        for i,x in enumerate(label_pair_lists)
                        if np.sort(pair).tolist() in x])

            # Assign a sulcus ID to fold vertices that have unique
            # label pair labels (unique to ensure a label is not shared
            # with another label pair in the fold); store unassigned vertices
            if len(unique_pairs):
                print("           Assign sulcus IDs to vertices "
                      "with labels in only one fold pair")
                if verbose:
                    for index, ID_unique_pair in enumerate(IDs_unique_pairs):
                        if len(sulcus_names):
                            print("           {0} ({1})".format(
                                unique_pairs[index], sulcus_names[ID_unique_pair]))
                        else:
                            print("           {0}".format(unique_pairs[index]))
                unassigned = []
                for vertex in fold:
                    index = [i for i,x in enumerate(unique_pairs)
                             if labels[vertex] in x]
                    if len(index):
                        sulci[vertex] = IDs_unique_pairs[index[0]]
                    else:
                        unassigned.append(vertex)
            else:
                unassigned = fold[:]

            # If there are remaining vertices with duplicate label pair labels
            if len(unassigned) and len(remainder_pairs):

                # Construct seed lists of remaining label boundary vertices
                seed_lists = []
                for remainder_pair in remainder_pairs:
                    seed_lists.append([x for i,x in enumerate(indices_fold_pairs)
                        if list(set(fold_pairs[i])) == list(set(remainder_pair))])

                # Segment into sets of vertices connected to label boundary seeds
                print("           Segment into separate label-pair regions")
                subfolds = segment(unassigned, neighbor_lists,
                                   seed_lists, min_region_size=50)

                # Assign a sulcus ID to each segment
                print("           Assign sulcus IDs to segmented vertices")
                for n_fold in np.unique(subfolds).tolist():
                    if n_fold > -1:
                        subfold = [i for i,x in enumerate(subfolds) if x == n_fold]
                        sulci[subfold] = IDs_remainder_pairs[n_fold]

    return sulci

#===============================================================================
# Extract sulci
#===============================================================================
def extract_sulci(label_pair_lists, labels, depth_file, area_file,
                  neighbor_lists, fraction_folds, do_fill_holes=True):
    """
    Extract sulci from a surface mesh using depth and a sulcus labeling protocol.

    First, extract all folds from a triangular surface mesh by a depth threshold
    (remove all non-fold vertices by assigning a value of -1 to them).

    Construct seed lists of label boundary vertices from anatomical labels
    on the mesh, where each seed list corresponds to label boundaries in a
    sulcus labeling protocol, and is assigned a sulcus ID.

    Segment the folds into sulci by propagating sulcus IDs from the seed vertices
    and fill holes resulting from shallower areas within a fold.

    Definitions::

      A fold is a group of connected vertices deeper than a depth threshold.

      A ''label list'' is the list of labels used to define a single sulcus.

      A ''label pair list'' contains pairs of labels, where each pair
      defines a boundary between two labeled regions.
      No two label pair lists share a label pair.

    A ''sulcus ID'' uniquely identifies a sulcus.
    It is the index to a sulcus label list (or sulcus label pair list).

    Parameters
    ----------
    label_pair_lists : list of sublists of subsublists of integers
        each subsublist contains a pair of labels, and the sublist of these
        label pairs represents the label boundaries defining a sulcus
    labels : numpy array of integers (optional)
        label numbers for all vertices, with -1s for unlabeled vertices
    depth_file : str
        surface mesh file in VTK format with faces and depth scalar values
    area_file : str
        surface mesh file in VTK format with faces and surface area scalar values
    neighbor_lists : list of lists of integers
        each list contains indices to neighboring vertices
    fraction_folds : float
        fraction of surface mesh considered folds
    min_sulcus_size : int
        minimum sulcus size (number of vertices)
    do_fill_holes : Boolean
        segment and fill holes?

    Returns
    -------
    sulci : array of integers
        sulcus numbers for all vertices, with -1s for non-sulcus vertices
    n_sulci :  int
        number of sulcus folds

    Examples
    --------
    >>> import os
    >>> from mindboggle.utils.io_vtk import load_scalars, write_scalar_lists
    >>> from mindboggle.utils.mesh_operations import find_neighbors, inside_faces
    >>> from mindboggle.extract.extract_folds import extract_sulci
    >>> from mindboggle.info.sulcus_boundaries import sulcus_boundaries
    >>> data_path = os.environ['MINDBOGGLE_DATA']
    >>> label_file = os.path.join(data_path, 'subjects', 'MMRR-21-1',
    >>>              'label', 'lh.labels.DKT25.manual.vtk')
    >>> depth_file = os.path.join(data_path, 'measures',
    >>>              '_hemi_lh_subject_MMRR-21-1', 'lh.pial.depth.vtk')
    >>> area_file = os.path.join(data_path, 'measures',
    >>>             '_hemi_lh_subject_MMRR-21-1', 'lh.pial.area.vtk')
    >>> points, faces, labels, n_vertices = load_scalars(label_file, True)
    >>> neighbor_lists = find_neighbors(faces, len(points))
    >>> label_pair_lists = sulcus_boundaries()
    >>> fraction_folds = 0.10  # low to speed up
    >>> min_sulcus_size = 50
    >>> # (do_fill_holes=False for speed)
    >>> sulci, n_sulci = extract_sulci(label_pair_lists, labels,
    >>>     depth_file, area_file, neighbor_lists, fraction_folds,
    >>>     do_fill_holes=False)
    >>> # Write results to vtk file and view with mayavi2:
    >>> indices = [i for i,x in enumerate(sulci) if x > -1]
    >>> write_scalar_lists('test_extract_sulci.vtk', points, indices,
    >>>     inside_faces(faces, indices), [sulci], ['sulci'])
    >>> os.system('mayavi2 -m Surface -d test_extract_sulci.vtk &')

    """
    import numpy as np
    from time import time
    from mindboggle.utils.io_vtk import load_scalars
    from mindboggle.extract.extract_folds import find_deep_vertices
    from mindboggle.utils.mesh_operations import detect_boundaries,\
        propagate, segment, fill_holes

    #---------------------------------------------------------------------------
    # Load deep vertices
    #---------------------------------------------------------------------------
    folds = find_deep_vertices(depth_file, area_file, fraction_folds)
    indices_folds = [i for i,x in enumerate(folds) if x == 1]
    if len(indices_folds):

        #---------------------------------------------------------------------------
        # Segment sulcus folds of a surface mesh
        #---------------------------------------------------------------------------
        print("  Segment surface mesh into sulcus folds")
        t0 = time()

        # Find all label boundary pairs within the fold
        indices_boundaries, label_pairs, unique_label_pairs = detect_boundaries(
            indices_folds, labels, neighbor_lists)

        # Construct seeds with indices to the vertices of each label boundary
        seeds = -1 * np.ones(len(labels))
        for ilist,label_pair_list in enumerate(label_pair_lists):
            I = [x for i,x in enumerate(indices_boundaries)
                 if np.sort(label_pairs[i]).tolist() in label_pair_list]
            seeds[I] = ilist

        # Segment into sets of vertices connected to label boundary seeds
        print("    Segment into separate label-pair regions...")
        t1 = time()
        points, faces, depths, n_vertices = load_scalars(depth_file, True)
        sulci = propagate(points, faces, folds, seeds, labels,
                          max_iters=200, tol=0.001, sigma=10)

        n_sulci = len([x for x in list(set(sulci)) if x != -1])
        print("    ...Segmented {0} sulcus folds in {1:.2f} seconds".
              format(n_sulci, time() - t1))

    else:
        n_sulci = 0

    #---------------------------------------------------------------------------
    # Fill holes in folds
    #---------------------------------------------------------------------------
    if n_sulci > 0 and do_fill_holes:

        # Find fold vertices that have not yet been segmented
        # (because they weren't sufficiently deep)
        t2 = time()
        nonsulcus_indices = [i for i,x in enumerate(sulci) if x==-1]

        # Segment holes in the folds
        print("    Find holes...")
        holes = segment(nonsulcus_indices, neighbor_lists)
        n_holes = len([x for x in list(set(holes)) if x != -1])

        # If there are any holes
        if n_holes > 0:

            # Ignore the largest hole (the background) and renumber holes
            max_hole_size = 0
            max_hole_index = 0
            for ihole in range(n_holes):
                I = np.where(holes == ihole)[0]
                if len(I) > max_hole_size:
                    max_hole_size = len(I)
                    max_hole_index = ihole
            holes[holes == max_hole_index] = -1
            if max_hole_index < n_holes:
                holes[holes > max_hole_index] -= 1
            n_holes -= 1
            print('    ...{0} holes segmented ({1:.2f} seconds)'.
                  format(n_holes, time() - t2))

            # Fill holes
            t3 = time()
            sulci = fill_holes(sulci, holes, neighbor_lists)
            print("    Filled holes ({0:.2f} seconds)".format(time() - t3))

    print("  ...Extracted and filled {0} sulcus folds in {1:.2f} seconds".
          format(n_sulci, time() - t0))

    return sulci, n_sulci


# Example for extract_sulci
if __name__ == "__main__":

    import os
    from mindboggle.utils.io_vtk import load_scalars, rewrite_scalar_lists
    from mindboggle.utils.mesh_operations import find_neighbors
    from mindboggle.extract.extract_folds import extract_sulci
    from mindboggle.info.sulcus_boundaries import sulcus_boundaries

    data_path = os.environ['MINDBOGGLE_DATA']
    label_file = os.path.join(data_path, 'subjects', 'MMRR-21-1',
                 'label', 'lh.labels.DKT25.manual.vtk')
    depth_file = os.path.join(data_path, 'measures',
                 '_hemi_lh_subject_MMRR-21-1', 'lh.pial.depth.vtk')
    area_file = os.path.join(data_path, 'measures',
                '_hemi_lh_subject_MMRR-21-1', 'lh.pial.area.vtk')

    points, faces, labels, n_vertices = load_scalars(label_file, True)
    neighbor_lists = find_neighbors(faces, len(points))
    label_pair_lists = sulcus_boundaries()

    fraction_folds = 0.10  # low to speed up
    min_sulcus_size = 50

    # do_fill_holes=False to speed up
    sulci, n_sulci = extract_sulci(label_pair_lists, labels,
        depth_file, area_file, neighbor_lists, fraction_folds, do_fill_holes=False)

    # Write results to vtk file and view with mayavi2:
    rewrite_scalar_lists(depth_file, 'test_extract_sulci.vtk',
                    [sulci], ['sulci'], sulci)
    os.system('mayavi2 -m Surface -d test_extract_sulci.vtk &')
