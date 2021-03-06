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
RUN conda install -y -n axiome2 -c bioconda -c anaconda -c conda-forge -c cyclus pandaseq make bc unzip zip java-jre
RUN conda install -y -n axiome2 -c bioconda -c conda-forge -c r r r-plyr r-dplyr r-getopt r-labdsv r-vegan r-ape r-car r-optparse

# Install extra dependencies needed to run
RUN apt-get update && apt-get install -y libsm6 libxrender-dev
RUN mkdir -p /home/support_binaries
RUN wget -O /home/support_binaries/rdp_classifier_2.2.zip https://sourceforge.net/projects/rdp-classifier/files/rdp-classifier/rdp_classifier_2.2.zip
RUN /bin/bash -c "source activate axiome2 && unzip /home/support_binaries/rdp_classifier_2.2.zip -d /home/support_binaries && rm /home/support_binaries/rdp_classifier_2.2.zip && source deactivate"
ENV RDP_JAR_PATH=/home/support_binaries/rdp_classifier_2.2/rdp_classifier-2.2.jar
RUN cd /home/support_binaries && git clone https://github.com/neufeld/MESaS.git
RUN echo "Create the folder '/home/support_binaries/usearch' and add your own usearch and uclust binaries there." > /home/support_binaries/README.txt
ENV PATH="/home/support_binaries/MESaS/scripts:/home/support_binaries/usearch:${PATH}"

# This might help for running matplotlib with no display, but I can't get it to work yet...
# RUN sed -i 's/Qt4Agg$/agg/' $(python -c 'import matplotlib; print matplotlib.matplotlib_fname()')

# Install axiome2 directly from Github
RUN /bin/bash -c "source activate axiome2 && pip install git+https://github.com/neufeld/AXIOME2.git && source deactivate"

# Add code to automatically start environment when logging in
RUN echo "source activate axiome2 > /dev/null" >> /root/.bashrc

RUN mkdir -p /home/axiome2

# Make core_set_aligned.fasta.imputed easy to find
RUN ln -s /opt/conda/envs/axiome2/lib/python2.7/site-packages/qiime_test_data/align_seqs/core_set_aligned.fasta.imputed /home/axiome2

ENTRYPOINT cd /home/axiome2 && \
	echo "Welcome to the AXIOME2 docker container. Note that the pynast alignment file can be found at '/home/axiome2/core_set_aligned.fasta.imputed'. Type 'exit' to leave the container." && \
	/bin/bash

