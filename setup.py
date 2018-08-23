#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Mindboggle: package for automated human brain image labeling and morphometry.

"""

import os
import sys
from os.path import join as pjoin

# BEFORE importing distguts, remove MANIFEST. distguts doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

# For some commands, use setuptools.
if len(set(('develop', 'bdist_egg', 'bdist_rpm', 'bdist', 'bdist_dumb',
            'bdist_wininst', 'install_egg_info', 'egg_info', 'easy_install',
            )).intersection(sys.argv)) > 0:
    pass
from distutils.core import setup

# Get version and release info, which is all stored in info.py
ver_file = pjoin(os.getcwd(), 'info.py')
exec(open(ver_file).read())

def main(**extra_args):
    setup(name=NAME,
          maintainer=MAINTAINER,
          maintainer_email=MAINTAINER_EMAIL,
          description=DESCRIPTION,
          long_description=LONG_DESCRIPTION,
          url=URL,
          download_url=DOWNLOAD_URL,
          license=LICENSE,
          classifiers=CLASSIFIERS,
          author=AUTHOR,
          author_email=AUTHOR_EMAIL,
          platforms=PLATFORMS,
          version=VERSION,
          requires=REQUIRES,
          provides=PROVIDES,
          packages=['mindboggle',
                    'mindboggle.data',
                    'mindboggle.evaluate',
                    'mindboggle.features',
                    'mindboggle.guts',
                    'mindboggle.mio',
                    'mindboggle.shapes',
                    'mindboggle.shapes.zernike',
                    'mindboggle.thirdparty'],
          package_data={'mindboggle': [pjoin('data', '*.nii.gz'),
                                       pjoin('data', '*.txt')]},
          scripts=[pjoin('mindboggle', 'mindboggle'),
                   pjoin('mindboggle', 'mindboggle123'),
                   pjoin('colors_script', 'calc_colormap.py'),
                   pjoin('colors_script', 'convert_to_mipav_lut.py')],
          **extra_args
         )

if __name__ == "__main__":
    main()
