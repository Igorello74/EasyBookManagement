#!/bin/bash

echo "This script is going to flush the whole database (delete all data),"
echo "delete all backups (backups folder) and create a new super user."
echo
read -p "Are you sure (y/n)? " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo canceled.
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1
fi

echo
echo "Okay, let's start then!"
docker exec -it easybookmanagement-web-1 bash scripts/_clean.sh