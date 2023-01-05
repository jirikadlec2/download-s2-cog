# download-s2-cog
Download subset from Sentinel-2 L2A AWS COG cloud data

Depends on gdal and pystac_client library, to install dependencies do:

pip3 install pystac-client==0.4.0

Example of running the script:

python3 download-s2-cog.py --startdate 2022-11-13 --enddate 2023-11-14 --aoi_geojson example.geojson --output_epsg "EPSG:3035" --dstdir /tmp --tmpdir /tmp

This will print out gdalwarp command for downloading and subsetting the band (here B04) data.
