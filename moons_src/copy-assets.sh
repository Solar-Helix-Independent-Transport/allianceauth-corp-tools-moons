#!/bin/bash

echo "Cleaning old assets."
rm -rf ../moons/static/moons/assets
rm ../moons/static/moons/manifest.json
echo "Copying new assets."
cp build/static/.vite/manifest.json ../moons/static/moons/manifest.json
cp -r build/static/assets ../moons/static/moons/assets
cp -r build/static/static/moons/ ../moons/static/
echo "Assets copied successfully."
