#!/bin/sh
case "$1" in *sername*) echo x-access-token ;; *) printf '%s\n' "$GITHUB_BACKUP_TOKEN" ;; esac
