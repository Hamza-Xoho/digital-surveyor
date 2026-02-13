#!/usr/bin/env python3
"""
Identify the Environment Agency LiDAR tile name for given BNG coordinates.
Usage: python download_tiles.py <easting> <northing>
"""
import sys

# OS National Grid 100km square letters
GRID_LETTERS = {
    (0, 0): "SV", (1, 0): "SW", (2, 0): "SX", (3, 0): "SY", (4, 0): "SZ",
    (5, 0): "TV", (6, 0): "TW",
    (0, 1): "SQ", (1, 1): "SR", (2, 1): "SS", (3, 1): "ST", (4, 1): "SU",
    (5, 1): "TQ", (6, 1): "TR",
    (0, 2): "SL", (1, 2): "SM", (2, 2): "SN", (3, 2): "SO", (4, 2): "SP",
    (5, 2): "TL", (6, 2): "TM",
    (0, 3): "SF", (1, 3): "SG", (2, 3): "SH", (3, 3): "SJ", (4, 3): "SK",
    (5, 3): "TF", (6, 3): "TG",
    (0, 4): "SA", (1, 4): "SB", (2, 4): "SC", (3, 4): "SD", (4, 4): "SE",
    (5, 4): "TA", (6, 4): "TB",
}


def bng_to_tile_ref(easting: float, northing: float) -> str:
    """Convert BNG easting/northing to 5km OS tile reference (e.g. TQ31)."""
    e100 = int(easting / 100000)
    n100 = int(northing / 100000)

    letters = GRID_LETTERS.get((e100, n100))
    if not letters:
        raise ValueError(f"Coordinates ({easting}, {northing}) outside GB grid")

    e_10k = int((easting % 100000) / 10000)
    n_10k = int((northing % 100000) / 10000)

    return f"{letters}{e_10k}{n_10k}"


def get_download_info(easting: float, northing: float) -> dict:
    """Get tile reference and download URL for given coordinates."""
    tile_ref = bng_to_tile_ref(easting, northing)
    return {
        "tile_ref": tile_ref,
        "expected_filename": f"{tile_ref}_DTM_1m.tif",
        "download_page": "https://environment.data.gov.uk/survey",
        "instructions": (
            f"1. Go to https://environment.data.gov.uk/survey\n"
            f"2. Search for tile: {tile_ref}\n"
            f"3. Select 'LIDAR Composite DTM 1m' dataset\n"
            f"4. Download the GeoTIFF for tile {tile_ref}\n"
            f"5. Save as: lidar-data/{tile_ref}_DTM_1m.tif"
        ),
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python download_tiles.py <easting> <northing>")
        print("Example: python download_tiles.py 530739 104456")
        sys.exit(1)

    e, n = float(sys.argv[1]), float(sys.argv[2])
    info = get_download_info(e, n)
    print(f"\nTile reference: {info['tile_ref']}")
    print(f"Expected filename: {info['expected_filename']}")
    print(f"\nDownload instructions:")
    print(info["instructions"])
