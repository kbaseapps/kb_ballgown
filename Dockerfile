FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.
# -----------------------------------------

RUN conda install -y r-essentials r-base r-xml r-rcurl
RUN R -q -e 'install.packages("BiocManager", repos="http://cran.us.r-project.org")' && \
    R -q -e 'BiocManager::install("ballgown", ask=FALSE)'
RUN R -q -e 'install.packages("getopt",  repos="http://cran.us.r-project.org")'

# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
