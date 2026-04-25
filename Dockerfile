FROM ubuntu:latest
LABEL authors="andre"

ENTRYPOINT ["top", "-b"]