#!/bin/bash
mkdir -p bin
find src -name "*.java" > sources.txt
javac -cp "lib/*" -d bin @sources.txt
