FROM ubuntu:14.04
MAINTAINER Duane Johnson <duane.johnson@gmail.com>

ADD downloads/cuda /usr/local/cuda

ENV INSTALL_PREFIX /usr/local
ENV CUDA_PREFIX /usr/local/cuda
ENV CUDNN_ENABLED 1

# Install wget and build-essential
RUN apt-get update && apt-get install -y --force-yes \
  build-essential \
  git \
  libopenblas-dev \
  python-dev \
  python-numpy \
  python-setuptools \
  vim \
  wget

