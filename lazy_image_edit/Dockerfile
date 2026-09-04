FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
darktable \
rawtherapee \
imagemagick \
make \
&& rm -rf /var/lib/apt/lists/*

WORKDIR /data

ENTRYPOINT ["bash"]
