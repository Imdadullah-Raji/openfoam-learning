#!/bin/bash

angles=( 5 10 15)

for aoa in "${angles[@]}"; 
do
    caseName="aoa_${aoa}"

    echo "Creating $caseName ..."

    if [ -d "$caseName" ]; then
        rm -rf "$caseName"
    fi

    cp -r aoa_0 "$caseName"

    python3 scripts/naca0012_gen.py \
    "$aoa" \
    "$caseName/constant/triSurface/naca0012.stl"

    cd "$caseName"
    blockMesh
    surfaceFeatures
    snappyHexMesh -overwrite
    python3 patch_correct.py constant/polyMesh/boundary front=empty back=empty
    extrudeMesh
    foamRun
    cd ..
    
done

echo "All simulations completed!"