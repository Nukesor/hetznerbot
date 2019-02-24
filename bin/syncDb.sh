#!/usr/bin/bash

host=nuke@jarvis

echo 'Dumping DB on remote'
ssh $host 'pg_dump -O -F c hetznerbot > hetznerbot.dump'
echo 'Sync DB'
scp $host:hetznerbot.dump ./

echo 'Drop and recreate DB'
dropdb hetznerbot || true
createdb hetznerbot

echo 'Restoring DB'
pg_restore -O -j 4 -F c -d hetznerbot hetznerbot.dump

echo 'Deleting dumps'
rm hetznerbot.dump
ssh $host 'rm hetznerbot.dump'
echo 'Done'
