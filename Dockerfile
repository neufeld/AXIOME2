# Dockerfile for AXIOME2
# Build and push with:
# docker build -t neufeld/axiome2:latest https://github.com/neufeld/AXIOME2.git
# docker push neufeld/axiome2

FROM continuumio/miniconda:4.5.4
LABEL maintainer="Jackson M. Tsuji <jackson.tsuji@uwaterloo.ca>"

# Update conda
RUN conda update -y conda

# Create conda env
RUN conda create -y -n axiome2 python=2.7
RUN conda install -y -n axiome2 -c bioconda qiime matplotlib=1.4.3 mock nose
RUN conda install -y -n axiome2 -c bioconda pandaseq
RUN conda install -y -n axiome2 -c bioconda -c conda-forge -c r r r-plyr r-dplyr r-getopt r-labdsv r-vegan r-ape r-car

# Install axiome2
RUN /bin/bash -c "source activate axiome2 && pip install axiome && source deactivate"

# Add custom binaries
RUN mkdir -p /home/support_binaries
RUN cd /home/support_binaries && git clone https://github.com/neufeld/MESaS.git
RUN echo "export PATH='/home/support_binaries/MESaS/scripts:\${PATH}'" >> /root/.bashrc
RUN mkdir -p /home/support_binaries/usearch
RUN echo "Create the folder '/home/support_binaries/usearch' and add your own usearch and uclust binaries there." > /home/support_binaries/README.txt
RUN echo "export PATH='/home/support_binaries/usearch:\${PATH}'" >> /root/.bashrc

# Add code to automatically start environment when logging in
RUN echo "source activate axiome2 > /dev/null" >> /root/.bashrc

RUN mkdir -p /home/axiome2

ENTRYPOINT cd /home/axiome2 && \
	echo "Welcome to the AXIOME2 docker container. Type 'exit' to leave the container." && \
	/bin/bash

