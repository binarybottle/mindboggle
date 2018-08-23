#!/bin/bash

# Generate a dockerfile for building a mindboggle container
docker run --rm kaczmarj/neurodocker:0.4.1 generate docker \
  --base neurodebian:stretch \
  --pkg-manager apt \
  --install graphviz tree git-annex-standalone vim \
    emacs-nox nano less ncdu tig sed build-essential \
    libsm-dev libx11-dev libxt-dev libxext-dev libglu1-mesa \
  --freesurfer version=6.0.0-min \
  --ants version=b43df4bfc8 method=source cmake_opts='-DBUILD_SHARED_LIBS=ON' make_opts='-j 4'\
  --run 'ln -s /usr/lib/x86_64-linux-gnu /usr/lib64' \
  --miniconda \
    conda_install="python=3.6 pip jupyter cmake mesalib vtk pandas \
      matplotlib colormath nipype" \
    pip_install="datalad[full] duecredit" \
    create_env="mb" \
    activate=true \
  --workdir /opt \
  --run 'mkdir -p /opt/data && cd /opt/data && \
    curl -sSL https://osf.io/download/rh9km/?revision=2 -o templates.zip && \
    unzip templates.zip && \
    rm -f /opt/data/templates.zip && \
    curl -sSL https://osf.io/download/d2cmy/ -o OASIS-TRT-20_jointfusion_DKT31_CMA_labels_in_OASIS-30_v2.nii.gz && \
    curl -sSL https://osf.io/download/qz3kx/ -o OASIS-TRT_brains_to_OASIS_Atropos_template.tar.gz && \
    tar zxf OASIS-TRT_brains_to_OASIS_Atropos_template.tar.gz && \
    rm OASIS-TRT_brains_to_OASIS_Atropos_template.tar.gz && \
    curl -sSL https://osf.io/download/dcf94/ -o OASIS-TRT_labels_to_OASIS_Atropos_template.tar.gz && \
    tar zxf OASIS-TRT_labels_to_OASIS_Atropos_template.tar.gz && \
    rm OASIS-TRT_labels_to_OASIS_Atropos_template.tar.gz' \
  --run-bash 'source /opt/miniconda-latest/etc/profile.d/conda.sh && \
        conda activate mb && \
        git clone https://github.com/nipy/mindboggle.git && \
        cd /opt/mindboggle && \
        git checkout edf95a3 && \
        python setup.py install && \
        sed -i "s/7.0/8.1/g" vtk_cpp_tools/CMakeLists.txt && \
        mkdir /opt/vtk_cpp_tools && \
        cd /opt/vtk_cpp_tools && \
        cmake /opt/mindboggle/vtk_cpp_tools && \
        make' \
  --env vtk_cpp_tools=/opt/vtk_cpp_tools \
  --run-bash 'source /opt/miniconda-latest/etc/profile.d/conda.sh && \
        conda activate mb && \
        conda install -y flask && \
        git clone https://github.com/akeshavan/roygbiv && \
        cd /opt/roygbiv && \
        git checkout fbbf31c29952d0ea22ed05d98e0a5a7e7d0827f9 && \
        python setup.py install && \
        cd /opt && \
        git clone https://github.com/akeshavan/nbpapaya && \
        cd /opt/nbpapaya && \
        git checkout 60119b6e1de651f250af26a3541d9cb18e971526 && \
        git submodule update --init --recursive && \
        python setup.py install && \
        rm -rf /opt/roygbiv /opt/nbpapaya' \
  > Dockerfile
