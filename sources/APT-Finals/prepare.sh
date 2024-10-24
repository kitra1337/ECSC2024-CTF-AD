#!/usr/bin/env bash

set -e

# Prepare service
rm -r ../../services/APT-Finals/*
cp go.mod go.sum Dockerfile docker-compose.yml init.sql ./*.go ../../services/APT-Finals/
cp -r ./pkg ../../services/APT-Finals/
mkdir ../../services/APT-Finals/cmd
cp -r ./cmd/client ../../services/APT-Finals/cmd/
cp -r ./cmd/server ../../services/APT-Finals/cmd/

# memez
mkdir ../../services/APT-Finals/cmd/checker
cp ./lmao.txt ../../services/APT-Finals/cmd/checker

# Prepare checker
go build -v -o ../../checkers/APT-Finals-1/checker ./cmd/checker
go build -v -o ../../checkers/APT-Finals-2/checker ./cmd/checker
