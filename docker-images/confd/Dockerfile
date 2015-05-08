FROM ubuntu:14.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install curl && \
    curl -o /usr/bin/confd -L https://github.com/kelseyhightower/confd/releases/download/v0.9.0/confd-0.9.0-linux-amd64 && \
    chmod 755 /usr/bin/confd

ADD etc/confd/ /etc/confd

CMD /usr/bin/confd -interval=60 -node=http://$COREOS_PRIVATE_IPV4:4001
