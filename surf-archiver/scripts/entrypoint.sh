#!/bin/bash

set -e


if getent passwd "$USER" > /dev/null; then
    echo "User \"$USER\" already exists"
else
    echo "Creating user \"$USER\""
    useradd -m -s /bin/bash guest
    echo "$USER:$USER" | chpasswd
fi

echo "Granting access to /data"
chown -R $USER:$USER /data

echo "Creating environment file for \"$USER\""
python /app/surf_archiver/scripts/write_env_file.py 


# Allow running other programs, e.g. bash
if [[ -z "$1" ]]; then
    echo "Executing sshd"
    exec /usr/sbin/sshd -D -e
else
    echo "Executing $*"
    /usr/sbin/sshd -q
    exec "$@"
fi
