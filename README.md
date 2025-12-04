# DPWH GIS Query Tool

A simple Python tool to query a table of all roads from the ArcGIS server of the Department of Public Works and Highways (DPWH)'s [Road and Bridge Information Application](https://www.dpwh.gov.ph/dpwh/gis/rbi). The tool retrieves data from the Road Classification features layer, which classifies whether a road or a segment of a road is an Expressway or a Primary, Secondary, or Tertiary road.

## Data Fields

The generated data contains the following columns:

**For Expressways:**

- `region`: The region that the road is located in.
- `province`: The province that the road is located in.
- `deo`: Name of the District Engineering Office that the road segment is a part of. Note that DEOs may span one or more cities or municipalities.
- `cong_district`: The congressional district that the road segment is a part of.
- `road_class`: Labels whether the road is a `Primary`, `Secondary`, or `Tertiary` road.
- `road_name`: The road that the road segment is a part of; this may be the whole segment or a divided one-way segment of a road.
- `road_length`: Road segment length in meters.

**For National Roads:**

- `region`: The region that the road is located in.
- `road_class`: Labels whether the road is an `Expressway`, `Elevated Expressway`, or `Skyway`.
- `xpres_way`: The road segment name; this may be a whole segment or a divided one-way segment of the expressway.
- `xpres_name`: The expressway that the road segment is a part of.
- `road_length`: Road segment in meters.

## Requirements

- Python 3.8+

## Installation

1. Clone or download the project:

   ```bash
   git clone <repository-url>
   cd DPWH_GIS
   ```

2. Create and activate a virtual environment:

    ```bash
   python -m venv env
   env\Scripts\activate.bat  # On Windows
   # or
   source env/bin/activate  # On macOS/Linux
   ```

## Usage

Run the main script:

```bash
python query_gis_data.py
```

The script supports the following options:

- Expressways or National Roads (Primary, Secondary, and Tertiary Roads)
- Roads from all regions or a specific region
- Maximum number of roads (or set to `-1` to get all available data)

The average time it takes to query all national roads should be no more than 2 seconds. After querying the data, it will get all unique roads and save the data as a CSV file in the `gis_data/` directory.
