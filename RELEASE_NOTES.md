### Version 2.0.0
- Since the installation of R, Bioconductor and Ballgown has been unstable, a version of Docker image
with Ballgown already installed has been created and used as the base image. So, in this version,
the docker image for Ballgown is being built from kbase/kb_ballgown_base:latest, instead of the original
kbase/kbase:sdkbase.latest. Apart from the required changes in the Dockerfile, the following 2 files have
been added too.

    - Dockerfile_base - Dockerfile to create the kb_ballgown_base to reinstall a different version of
                        Ballgown, if needed and create kb_ballgown_base image again.
    - create_ballgown_base.md - Instructions for creating the kb_ballgown_base image.

### Version 1.0.2
- First release version
