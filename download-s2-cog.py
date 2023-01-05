import argparse
import json
import os
import gdal
import time
import subprocess
import shutil
import random
import string
import logging

from datetime import datetime

from pystac_client import Client as stac_client
from shapely.geometry import shape, GeometryCollection

SEARCH_API_URL = "https://earth-search.aws.element84.com/v0"



start = time.time()

log = logging.getLogger("download-s2-cog")


def setup_logging():
    log.setLevel(logging.DEBUG)

    # Create console handler which logs all messages (info and higher) to console.
    # The console logging does not include the time.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter("%(asctime)s, %(name)s, %(levelname)s, %(message)s", "%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)
    log.addHandler(console_handler)

# set-up logging
setup_logging()

def run(startdate, enddate, aoi_geojson, output_epsg, dstdir, tmpdir):
    log.info("Opening geojson file {}..".format(aoi_geojson))
    aoi_polygon = None
    with open(aoi_geojson) as f:
        features = list(json.load(f)["features"])
        log.info("Geojson file has {} features.".format(len(features)))
        aoi_polygon = features[0]

    # Search for the scenes using STAC catalog
    api_url = SEARCH_API_URL
    client = stac_client.open(api_url)
    collection = "sentinel-s2-l2a-cogs"  # Sentinel-2, Level 2A, COGs

    datetime_start_str = startdate + "T00:00:00Z"
    datetime_end_str = enddate + "T00:00:00Z"
    print(datetime_end_str)

    search = client.search(
        collections=[collection],
        intersects=aoi_polygon['geometry'],
        datetime=[datetime_start_str, '2023-01-31T00:00:00Z'],
        max_items=10,
    )
    num_matched = search.matched()
    log.info("Found {} matching scenes.".format(num_matched))

    if num_matched == 0:
        return

    # Browse the assets
    found_items = search.get_all_items()
    latest_scene = found_items[0]
    assets = latest_scene.assets  # first item's asset dictionary
    log.info("ASSETS of the first found scene:")
    log.info(assets.keys())

    # assets information..
    for key, asset in assets.items():
        print(f"{key}: {asset.title}")

    # downloading a selected asset B04 covering the geojson file.
    b04_href = assets["B04"].href
    log.info("url of B04: " + b04_href)

    # bounding box of the polygon in lon/lat
    polygon_shape = shape(aoi_polygon["geometry"])
    bbox =  polygon_shape.bounds
    log.info("bounding box of aoi polygon:")
    log.info(polygon_shape.bounds)

    gdalwarp_cmd = ["gdalwarp", "-te",
                    str(bbox[0]),
                    str(bbox[1]),
                    str(bbox[2]),
                    str(bbox[3]),
                    "-te_srs",
                    "EPSG:4326",
                    "-tr",
                    "10", "10",
                    "/vsicurl/" + b04_href,
                    os.path.join(dstdir, "test_output_b04.tif")]
                    #-te_srs EPSG:4326 -tr 10 10 /vsicurl/https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/33/U/VR/2023/1/S2A_33UVR_20230103_0_L2A/B04.tif /tmp/S2A_33UVR_20230103_0_L2A_B04.tif
    print(" ".join(gdalwarp_cmd))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script for downloading subsets of Sentinel-2 scenes from AWS COG Cloud.")

    parser.add_argument('--startdate', type=str, help='start datetime in yyyy-mm-dd format', required=True)
    parser.add_argument('--enddate', type=str, help='end datetime in yyyy-mm-dd format', required=True)
    parser.add_argument('--aoi_geojson', type=str, help='geojson file of the AOI', required=False, default=None)
    parser.add_argument('--output_epsg', type=str, help='EPSG code of output subsets e.g. EPSG:32633', required=True)
    parser.add_argument('--dstdir', type=str, help='Destination directory to save outputs.', required=True)
    parser.add_argument('--tmpdir', type=str, help='Destination directory to save outputs.', required=True)

    args = parser.parse_args()

    run(startdate=args.startdate,
        enddate=args.enddate,
        aoi_geojson=args.aoi_geojson,
        output_epsg=args.output_epsg,
        dstdir=args.dstdir,
        tmpdir=args.tmpdir
        )