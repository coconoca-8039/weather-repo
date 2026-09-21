#!/bin/bash

cd "$(dirname "$0")" || exit 1

echo "=== Weather charts start ==="

python3 ASurface.py
echo "Surface Fin"

python3 A850hPa.py
echo "850 hPa Fin"

python3 A700hPa.py
echo "700 hPa Fin"

python3 A500hPa.py
echo "500 hPa Fin"

python3 A300hPa.py
echo "300 hPa Fin"

python3 cloud_coverpy
echo "Cloud Cover Fin"