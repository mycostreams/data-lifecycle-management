#!/bin/bash

dir=$(dirname "$0")

cd "$dir/.."

if [ ! -d Fiji.app ]
then
  echo "Installing Fiji"
  wget -nv https://downloads.imagej.net/fiji/archive/20240220-2017/fiji-nojre.zip \
      && unzip fiji-nojre.zip \
      && rm fiji-nojre.zip \
      && echo "Installation complete"
else
  echo "Fiji already installed"
fi
