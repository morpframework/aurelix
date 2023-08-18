FROM quay.io/centos/centos:stream9-minimal as base

RUN microdnf update -y && microdnf install -y \
    --enablerepo=crb \
    python3.11 python3.11-devel python3.11-pip \
    postgresql-devel mariadb-devel && \
    microdnf clean all

RUN mkdir -p /opt/aurelix/ /opt/app/

ADD setup.cfg /opt/aurelix/
ADD setup.py /opt/aurelix/
ADD MANIFEST.in /opt/aurelix/
ADD aurelix /opt/aurelix/aurelix

RUN python3.11 -m venv /opt/virtualenv && \
    /opt/virtualenv/bin/pip install -e /opt/aurelix

ENV AURELIX_CONFIG=/opt/app/app.yaml

ENTRYPOINT ["/opt/virtualenv/bin/aurelix", "-l", "0.0.0.0"]
