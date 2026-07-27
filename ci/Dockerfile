# CI image for axion-hdl: pre-built GHDL + Verilator so test workflows
# don't need to compile them from source on every run.
# Rebuilt only when this file changes (see .github/workflows/docker-image.yml).
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        ghdl \
        git help2man perl make autoconf g++ flex bison ccache \
        libfl2 libfl-dev zlib1g zlib1g-dev \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# cocotb requires Verilator >=5.036; Ubuntu 22.04's apt package (4.038) is
# too old, so build "stable" from source instead.
RUN git clone --depth 1 --branch stable https://github.com/verilator/verilator.git /tmp/verilator-src \
    && cd /tmp/verilator-src \
    && autoconf \
    && ./configure \
    && make -j"$(nproc)" \
    && make install \
    && rm -rf /tmp/verilator-src

RUN ghdl --version && verilator --version
