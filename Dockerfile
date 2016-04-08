FROM ubuntu:14.04
MAINTAINER Duane Johnson <duane.johnson@gmail.com>

ADD downloads/cuda_7.5.18_linux.run /tmp/cuda_install/cuda.run

ENV INSTALL_PREFIX /usr/local
ENV CUDA_PREFIX /usr/local/cuda-7.5
ENV CUDNN_ENABLED 1

# Install deb packages
RUN apt-get update && apt-get install -y --force-yes \
  build-essential \
  git \
  libopenblas-dev \
  python-dev \
  python-numpy \
  python-scipy \
  python-setuptools \
  vim \
  wget

# Install cuda base library
RUN cd /tmp/cuda_install && \
# Make the run file executable and extract
  chmod +x cuda.run && sync && \
  ./cuda.run -extract=`pwd` && \
# Install CUDA drivers (silent, no kernel)
  ./NVIDIA-Linux-x86_64-*.run -s --no-kernel-module && \
# Install toolkit (silent)  
  ./cuda-linux64-rel-*.run -noprompt && \
# Clean up
  rm -rf *
# Add to path
ENV PATH=/usr/local/cuda-7.5/bin:$PATH \
  LD_LIBRARY_PATH=/usr/local/cuda-7.5/lib64:$LD_LIBRARY_PATH

# Install cuDNN
ADD downloads/cuda /usr/local/cuda-7.5
RUN easy_install cython

# Install cudarray
ADD cudarray /tmp/cudarray
RUN cd /tmp/cudarray && \
  make && make install && \
  python setup.py install && \
  rm -rf *

# Install Pillow image library dependencies
# RUN apt-get update && apt-get install -y --force-yes \
#   libjpeg-dev \
#   libfreetype6-dev \
#   python-liblcms
RUN apt-get install -y --force-yes \
  libjpeg-dev \
  libfreetype6-dev \
  python-liblcms
 
# Install deeppy
ADD deeppy /tmp/deeppy
RUN cd /tmp/deeppy && \
  python setup.py install

ADD neural_artistic_style /style
ADD downloads/imagenet-vgg-verydeep-19.mat /style/imagenet-vgg-verydeep-19.mat

