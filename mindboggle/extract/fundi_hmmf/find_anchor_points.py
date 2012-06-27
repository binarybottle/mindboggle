#!/usr/bin/python
"""
Compute distance measures.

Authors:
Yrjo Hame  .  yrjo.hame@gmail.com  (original Matlab code)
Arno Klein  .  arno@mindboggle.info  (translated to Python)

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

import numpy as np

#===================
# Find anchor points
#===================
def find_anchor_points(vertices, L, min_distances, distance_threshold, max_distance):
    """
    Find anchor points

    Assign maximum likelihood vertices as "anchor points"
    for use in constructing fundus curves.
    Ensure tht anchor points are not close to one another.

    Inputs:
    ------
    vertices: [#vertices x 3] numpy array
    L: fundus likelihood values [#vertices x 1] numpy array
    min_distances: [#vertices x 1] numpy array
    distance_threshold: distance threshold
    max_distance: maximum distance

    Output:
    ------
    P: anchor points [#vertices x 1] numpy array

    """

    # Find maximum likelihood value
    maxL = max(L)
    imax = np.where(L == maxL)[0]

    # Initialize anchor point array and reset maximum likelihood value
    P = np.zeros(len(L))
    check_list = P.copy()
    check_list[imax] = 1
    P[imax] = 1
    L[imax] = -1

    # Loop until all vertices checked
    while min(check_list) == 0 and maxL > 0.5:

        # Find and reset maximum likelihood value
        maxL = max(L)
        imax = np.where(L = maxL)[0]
        check_list[imax] = 1
        L[imax] = -1

        # Anchor point vertices and distance values
        IP = P > 0
        lenP = sum(IP)
        P_vertices = vertices[IP,:]
        P_distances = min_distances[IP]

        # Find anchor point vertices close to vertex with maximum likelihood value
        i = 0
        found = 0
        while i < lenP and found == 0:

            # Compute Euclidean distance between points
            D = np.linalg.norm(P_vertices[i,:] - vertices[imax,:])

            # Compute directional distance between points
            if max_distance > D >= distance_threshold:
                dirV = np.dot(P_vertices[i,:] - vertices[imax,:], P_distances[i])
                D = np.linalg.norm(dirV)

            # If distance less than threshold, consider the point found
            if D < distance_threshold:
                found = 1

            i += 1

        # If there are no nearby anchor points,
        # assign the maximum likelihood vertex as an anchor point
        if not found:
            P[imax] = 1

    return P