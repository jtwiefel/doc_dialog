# syntax=docker/dockerfile:1

#https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
#FROM nvidia/cuda:11.6.2-cudnn8-devel-ubuntu20.04
#needed to upgrade this because tf was not compatible with the given cudnn version 8.3.2, needs at least 8.9
FROM nvidia/cuda:12.2.2-cudnn8-devel-ubuntu22.04
#RUN rm /etc/apt/sources.list.d/cuda.list && apt-get update 
RUN apt-get clean
RUN apt-get update
RUN apt-get update && apt-get install -y apt-transport-https
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata
#RUN apt install -y python3.9 python3.9-dev
#
RUN apt install -y python3-pip
RUN apt install -y python-is-python3 
RUN apt install -y git
#RUN pip install torch==1.13.1+cu116 torchvision==0.14.1+cu116 torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cu116

#sound
RUN apt update
#RUN apt install -y pulseaudio socat
#RUN apt install -y alsa-utils
#RUN apt install -y ffmpeg
#RUN apt install -y portaudio19-dev
#RUN pip install websocket-client
#RUN pip install rel
RUN apt install -y telnet
WORKDIR /workspace/python
COPY ../python/requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install flash-attn --no-build-isolation
#RUN CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install llama-cpp-python==0.2.55
#COPY ../python/requirements_trainer_whisper_tiny.txt requirements_trainer_whisper_tiny.txt
#RUN pip install -r requirements_trainer_whisper_tiny.txt
#COPY ../python/exxxa_euregon/utils/download_models.py download_models.py
#RUN python download_models.py
#RUN git config --global --add safe.directory /workspace/llama.cpp
CMD bash

#CMD python websocket_server.py