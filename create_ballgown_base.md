

The installation of Ballgown has been breaking often because of the poor packaging
of BioConductor. So in order to freeze a successful installation of Ballgown,
the docker image with a working installation of R, Bioconductor and Ballgown are saved
in KBase docker hub, kbase/kb_ballgown_base:latest

The Dockerfile pulls the kb_ballgown_base image, which has the installation of Ballgown
from the docker hub and uses it.

However, if we need to install another version of Ballgown, the new image is created with
installation of Ballgown on top of sdkbase, using the Dockerfile_base.

### The kb_ballgown_base image can be created following the instructions below.

#### Remove any Ballgown related docker images
docker images | grep ballgown
docker rmi -f <IMAGE_ID>

#### Remove all the anonymous docker images
docker rmi $(sudo docker images -a | grep '^<none>' | awk '{print $3}')

#### Save the original dockerfile and use the Dockerfile_base to create the base image
mv Dockerfile Dockerfile_ORIG
mv Dockerfile_base Dockerfile

#### Docker image test/kb_ballgown gets created in the following step
kb-sdk test

#### Make sure that the versions of R, Bioconductor and Ballgown are the required ones and
#### their installations succeeded.

#### retag the docker image to the name kb_ballgown_base
docker tag test/kb_ballgown:latest <username>/kb_ballgown_base:latest

#### Push the image to your local docker hub

#### Get the kbase administrator move the image to KBase docker hub account

### Use the following steps to use the Ballgown base image again
#### Save the Dockerfile to Dockerfile_base and retain the original Dockerfile

mv Dockerfile Dockerfile_base
mv Dockerfile_ORIG Dockerfile

#### Remove all the Ballgown related docker images
docker images | grep ballgown
docker rmi -f <IMAGE_ID>

#### Remove all the anonymous docker images
docker rmi $(sudo docker images -a | grep '^<none>' | awk '{print $3}')

#### Run tests with the created kb_ballgown_base
#### When kb-sdk test is run, it makes use of the updated docker image
#### kb_ballgown_base from the docker hub account of KBase

kb-sdk test

