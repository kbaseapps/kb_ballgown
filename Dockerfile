FROM kbase/kbase:sdkbase.latest
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# RUN apt-get update

# Here we install a python coverage tool and an
# https library that is out of date in the base image.

RUN pip install coverage

# update security libraries in the base image
RUN pip install cffi --upgrade \
    && pip install pyopenssl --upgrade \
    && pip install ndg-httpsclient --upgrade \
    && pip install pyasn1 --upgrade \
    && pip install requests --upgrade \
    && pip install 'requests[security]' --upgrade

# -----------------------------------------
RUN echo Starting R and Bioconductor update, followed by Ballgown installation && \
	echo "deb http://cran.rstudio.com/bin/linux/ubuntu trusty/" >> /etc/apt/sources.list && \
	gpg --keyserver keyserver.ubuntu.com --recv-key E084DAB9 && \
	gpg -a --export E084DAB9 | sudo apt-key add - && \
	apt-get update && \
	rm -rf /usr/lib/R && \
	rm -rf /usr/local/lib/R

ENV DEBIAN_FRONTEND=noninteractive

RUN echo "##########" About to install a new R "###########" && \
	apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confnew" install r-base

RUN echo "##########" About to load bioconductor and ballgown "###########" && \
	R -q -e 'chooseCRANmirror(ind=48); install.packages(c("getopt")); source("https://bioconductor.org/biocLite.R"); biocLite("ballgown")' && \
	echo "##########" Finished loading bioconductor and ballgown "###########" && \
	echo Completed: R and Bioconductor update, followed by Ballgown installation

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
