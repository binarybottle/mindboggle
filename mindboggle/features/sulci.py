#!/usr/bin/env python
"""
Functions to extract sulci from folds.

Authors:
    - Arno Klein, 2012-2013  (arno@mindboggle.info)  http://binarybottle.com

Copyright 2013,  Mindboggle team (http://mindboggle.info), Apache v2.0 License

"""


def extract_sulci(labels_file, folds_or_file, hemi, min_boundary=1,
                  sulcus_names=[]):
    """
    Identify sulci from folds in a brain surface according to a labeling
    protocol that includes a list of label pairs defining each sulcus.

    A fold is a group of connected, deep vertices.

    Steps for each fold ::

        1. Remove fold if it has fewer than two labels.
        2. Remove fold if its labels do not contain a sulcus label pair.
        3. Find vertices with labels that are in only one of the fold's
           label boundary pairs. Assign the vertices the sulcus with the label
           pair if they are connected to the label boundary for that pair.
        4. If there are remaining vertices, segment into sets of vertices
           connected to label boundaries, and assign a unique ID to each set.

    Parameters
    ----------
    labels_file : string
        file name for surface mesh VTK containing labels for all vertices
    folds_or_file : list or string
        fold number for each vertex / name of VTK file containing fold scalars
    hemi : string
        hemisphere abbreviation in {'lh', 'rh'} for sulcus labels
    min_boundary : integer
        minimum number of vertices for a sulcus label boundary segment
    sulcus_names : list of strings
        names of sulci

    Returns
    -------
    sulci : list of integers
        sulcus numbers for all vertices (-1 for non-sulcus vertices)
    n_sulci : integers
        number of sulci
    sulci_file : string
        output VTK file with sulcus numbers (-1 for non-sulcus vertices)

    Examples
    --------
    >>> import os
    >>> from mindboggle.utils.io_vtk import read_scalars, rewrite_scalars
    >>> from mindboggle.features.sulci import extract_sulci
    >>> from mindboggle.utils.plots import plot_surfaces
    >>> path = os.environ['MINDBOGGLE_DATA']
    >>> # Load labels, folds, neighbor lists, and sulcus names and label pairs
    >>> labels_file = os.path.join(path, 'arno', 'labels', 'relabeled_lh.DKTatlas40.gcs.vtk')
    >>> folds_file = os.path.join(path, 'arno', 'features', 'folds.vtk')
    >>> folds_or_file, name = read_scalars(folds_file)
    >>> hemi = 'lh'
    >>> min_boundary = 10
    >>> sulcus_names = []
    >>> #
    >>> sulci, n_sulci, sulci_file = extract_sulci(labels_file, folds_or_file, hemi, min_boundary, sulcus_names)
    >>> # View:
    >>> plot_surfaces('sulci.vtk')

    """
    import os
    from time import time
    import numpy as np

    from mindboggle.utils.io_vtk import read_scalars, read_vtk, rewrite_scalars
    from mindboggle.utils.mesh import find_neighbors
    from mindboggle.utils.segment import extract_borders, propagate, segment
    from mindboggle.LABELS import DKTprotocol


    # Load fold numbers if folds_or_file is a string:
    if isinstance(folds_or_file, str):
        folds, name = read_scalars(folds_or_file)
    elif isinstance(folds_or_file, list):
        folds = folds_or_file

    dkt = DKTprotocol()

    if hemi == 'lh':
        pair_lists = dkt.left_sulcus_label_pair_lists
    elif hemi == 'rh':
        pair_lists = dkt.right_sulcus_label_pair_lists
    else:
        print("Warning: hemisphere not properly specified ('lh' or 'rh').")

    # Load points, faces, and neighbors:
    faces, o1, o2, points, npoints, labels, o3, o4 = read_vtk(labels_file)
    neighbor_lists = find_neighbors(faces, npoints)

    # Array of sulcus IDs for fold vertices, initialized as -1.
    # Since we do not touch gyral vertices and vertices whose labels
    # are not in the label list, or vertices having only one label,
    # their sulcus IDs will remain -1:
    sulci = -1 * np.ones(npoints)

    #-------------------------------------------------------------------------
    # Loop through folds
    #-------------------------------------------------------------------------
    fold_numbers = [int(x) for x in np.unique(folds) if x != -1]
    n_folds = len(fold_numbers)
    print("Extract sulci from {0} folds...".format(n_folds))
    t0 = time()
    for n_fold in fold_numbers:
        fold = [i for i,x in enumerate(folds) if x == n_fold]
        len_fold = len(fold)

        # List the labels in this fold:
        fold_labels = [labels[x] for x in fold]
        unique_fold_labels = [int(x) for x in np.unique(fold_labels)
                              if x != -1]

        #---------------------------------------------------------------------
        # NO MATCH -- fold has fewer than two labels
        #---------------------------------------------------------------------
        if len(unique_fold_labels) < 2:
            # Ignore: sulci already initialized with -1 values:
            if not unique_fold_labels:
                print("  Fold {0} ({1} vertices): "
                      "NO MATCH -- fold has no labels".
                      format(n_fold, len_fold))
            else:
                print("  Fold {0} ({1} vertices): "
                  "NO MATCH -- fold has only one label ({2})".
                  format(n_fold, len_fold, unique_fold_labels[0]))
            # Ignore: sulci already initialized with -1 values

        else:
            # Find all label boundary pairs within the fold:
            indices_fold_pairs, fold_pairs, unique_fold_pairs = \
                extract_borders(fold, labels, neighbor_lists,
                                ignore_values=[], return_label_pairs=True)

            # Find fold label pairs in the protocol (pairs are already sorted):
            fold_pairs_in_protocol = [x for x in unique_fold_pairs
                                      if x in dkt.unique_sulcus_label_pairs]

            if unique_fold_labels:
                print("  Fold {0} labels: {1} ({2} vertices)".format(n_fold,
                      ', '.join([str(x) for x in unique_fold_labels]),
                      len_fold))
            #-----------------------------------------------------------------
            # NO MATCH -- fold has no sulcus label pair
            #-----------------------------------------------------------------
            if not fold_pairs_in_protocol:
                print("  Fold {0}: NO MATCH -- fold has no sulcus label pair".
                      format(n_fold, len_fold))

            #-----------------------------------------------------------------
            # Possible matches
            #-----------------------------------------------------------------
            else:
                print("  Fold {0} label pairs in protocol: {1}".format(n_fold,
                      ', '.join([str(x) for x in fold_pairs_in_protocol])))

                # Labels in the protocol (includes repeats across label pairs):
                labels_in_pairs = [x for lst in fold_pairs_in_protocol
                                   for x in lst]

                # Labels that appear in one or more sulcus label boundary:
                unique_labels = []
                nonunique_labels = []
                for label in np.unique(labels_in_pairs):
                    if len([x for x in labels_in_pairs if x == label]) == 1:
                        unique_labels.append(label)
                    else:
                        nonunique_labels.append(label)

                #-------------------------------------------------------------
                # Vertices whose labels are in only one sulcus label pair
                #-------------------------------------------------------------
                # Find vertices with a label that is in only one of the fold's
                # label pairs (the other label in the pair can exist in other
                # pairs). Assign the vertices the sulcus with the label pair
                # if they are connected to the label boundary for that pair.
                #-------------------------------------------------------------
                if unique_labels:

                    for pair in fold_pairs_in_protocol:

                        # If one or both labels in label pair is/are unique:
                        unique_labels_in_pair = [x for x in pair
                                                 if x in unique_labels]
                        n_unique = len(unique_labels_in_pair)
                        if n_unique:

                            ID = None
                            for i, pair_list in enumerate(pair_lists):
                                if not isinstance(pair_list, list):
                                    pair_list = [pair_list]
                                if pair in pair_list:
                                    ID = i
                                    break
                            if ID:
                                # Seeds from label boundary vertices
                                # (fold_pairs and pair already sorted):
                                indices_pair = [x for i,x
                                    in enumerate(indices_fold_pairs)
                                    if fold_pairs[i] == pair]

                                # Vertices with unique label(s) in pair:
                                indices_unique_labels = [fold[i]
                                     for i,x in enumerate(fold_labels)
                                     if x in dkt.unique_sulcus_label_pairs]

                                # Propagate from seeds to labels in label pair:
                                sulci2 = segment(indices_unique_labels,
                                                 neighbor_lists,
                                                 min_region_size=1,
                                                 seed_lists=[indices_pair],
                                                 keep_seeding=False,
                                                 spread_within_labels=True,
                                                 labels=labels)
                                sulci[sulci2 != -1] = ID

                                # Print statement:
                                if n_unique == 1:
                                    ps1 = '1 label'
                                else:
                                    ps1 = 'Both labels'
                                if len(sulcus_names):
                                    ps2 = sulcus_names[ID]
                                else:
                                    ps2 = ''
                                print("    {0} unique to one fold pair: "
                                      "{1} {2}".
                                      format(ps1, ps2, unique_labels_in_pair))

                #-------------------------------------------------------------
                # Vertex labels shared by multiple label pairs
                #-------------------------------------------------------------
                # Propagate labels from label borders to vertices with labels
                # that are shared by multiple label pairs in the fold.
                #-------------------------------------------------------------
                if len(nonunique_labels):
                    # For each label shared by different label pairs:
                    for label in nonunique_labels:
                        # Print statement:
                        print("    Propagate sulcus borders with label {0}".
                              format(int(label)))

                        # Construct seeds from label boundary vertices:
                        seeds = -1 * np.ones(len(points))

                        for ID, pair_list in enumerate(pair_lists):
                            if not isinstance(pair_list, list):
                                pair_list = [pair_list]
                            label_pairs = [x for x in pair_list if label in x]
                            for label_pair in label_pairs:
                                indices_pair = [x for i,x
                                    in enumerate(indices_fold_pairs)
                                    if np.sort(fold_pairs[i]).
                                    tolist() == label_pair]
                                if indices_pair:

                                    # Do not include short boundary segments:
                                    if min_boundary > 1:
                                        indices_pair2 = []
                                        seeds2 = segment(indices_pair,
                                                         neighbor_lists)
                                        useeds2 = [x for x in
                                                   np.unique(seeds2)
                                                   if x != -1]
                                        for seed2 in useeds2:
                                            iseed2 = [i for i,x
                                                      in enumerate(seeds2)
                                                      if x == seed2]
                                            if len(iseed2) >= min_boundary:
                                                indices_pair2.extend(iseed2)
                                            else:
                                                if len(iseed2) == 1:
                                                    print("    Remove "
                                                          "assignment "
                                                          "of ID {0} from "
                                                          "1 vertex".
                                                          format(seed2))
                                                else:
                                                    print("    Remove "
                                                          "assignment "
                                                          "of ID {0} from "
                                                          "{1} vertices".
                                                          format(seed2,
                                                                 len(iseed2)))
                                        indices_pair = indices_pair2

                                    # Assign sulcus IDs to seeds:
                                    seeds[indices_pair] = ID

                        # Identify vertices with the label:
                        label_array = -1 * np.ones(len(points))
                        indices_label = [fold[i] for i,x
                                         in enumerate(fold_labels)
                                         if x == label]
                        if len(indices_label):
                            label_array[indices_label] = 1

                            # Propagate from seeds to vertices with label:
                            #indices_seeds = []
                            #for seed in range(int(max(seeds))+1):
                            #    indices_seeds.append([i for i,x
                            #                          in enumerate(seeds)
                            #                          if x == seed])
                            #sulci2 = segment(indices_label, neighbor_lists,
                            #                 50, indices_seeds, False, True,
                            #                 labels)
                            sulci2 = propagate(points, faces,
                                               label_array, seeds, sulci,
                                               max_iters=10000,
                                               tol=0.001, sigma=5)
                            sulci[sulci2 != -1] = sulci2[sulci2 != -1]

    #-------------------------------------------------------------------------
    # Print out assigned sulci
    #-------------------------------------------------------------------------
    sulcus_numbers = [int(x) for x in np.unique(sulci) if x != -1]
                      # if not np.isnan(x)]
    n_sulci = len(sulcus_numbers)
    print("Extracted {0} sulci from {1} folds ({2:.1f}s):".
          format(n_sulci, n_folds, time()-t0))
    if sulcus_names:
        for sulcus_number in sulcus_numbers:
            print("  {0}: {1}".format(sulcus_number,
                                      sulcus_names[sulcus_number]))
    elif sulcus_numbers:
        print("  " + ", ".join([str(x) for x in sulcus_numbers]))

    #-------------------------------------------------------------------------
    # Print out unresolved sulci
    #-------------------------------------------------------------------------
    unresolved = [i for i in range(len(pair_lists))
                  if i not in sulcus_numbers]
    if len(unresolved) == 1:
        print("The following sulcus is unaccounted for:")
    else:
        print("The following {0} sulci are unaccounted for:".
              format(len(unresolved)))
    if sulcus_names:
        for sulcus_number in unresolved:
            print("  {0}: {1}".format(sulcus_number,
                                      sulcus_names[sulcus_number]))
    else:
        print("  " + ", ".join([str(x) for x in unresolved]))

    #-------------------------------------------------------------------------
    # Return sulci, number of sulci, and file name
    #-------------------------------------------------------------------------
    sulci_file = os.path.join(os.getcwd(), 'sulci.vtk')
    rewrite_scalars(labels_file, sulci_file, sulci, 'sulci', sulci)
    sulci = [int(x) for x in sulci]

    if not os.path.exists(sulci_file):
        raise(IOError(sulci_file + " not found"))

    return sulci, n_sulci, sulci_file


#if __name__ == "__main__":
