#!/bin/sh

cd /tmp
rm -rf config_repo
git clone $REPO config_repo
rsync -av --delete config_repo/confd /etc/confd
