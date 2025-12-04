import requests
from time import time
import os
import pandas as pd

import constants

regions = constants.REGIONS
road_class_types = constants.ROAD_CLASS_TYPES
gis_data_dir = constants.GIS_DATA_DIR
feature_layer_url = constants.FEATURE_LAYER_URL

def get_int_input(prompt: str, min_value=None, max_value=None, allow_minus_one=False):
    while True:
        try:
            raw = input(prompt).strip()
            if raw.lower() in {"q", "quit", "exit"}:
                print("Exiting.")
                exit(0)
            val = int(raw)
            if allow_minus_one and val == -1:
                return val
            if (min_value is not None and val < min_value) or (max_value is not None and val > max_value):
                low = min_value if min_value is not None else "-inf"
                high = max_value if max_value is not None else "inf"
                print(f"Value must be between {low} and {high}.")
                continue
            return val
        except ValueError:
            print("Invalid integer. Try again.")
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            exit(1)

def select_option(options: list, prompt: str, return_index=False, show_selection=True):
    if not options:
        raise ValueError("Empty list passed to options parameter")
    while True:
        try:
            print()
            for idx, item in enumerate(options, start=1):
                print(f"[{idx}] {item}")
            print()
            raw = input(prompt).strip()
            if raw.lower() in {"q", "quit", "exit"}:
                print("Exiting.")
                exit(0)
            value = int(raw)
            if 1 <= value <= len(options):
                sel_idx = value - 1
                selection = options[sel_idx]
                if show_selection:
                    print(f"\nSelected: {selection}\n")
                if return_index:
                    return sel_idx
                else:
                    return selection
            else:
                print(f"Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Enter the option number.")
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            exit(1)

def query_road_data(layer_index: int, params: dict):
    timeout_sec = 15.0
    query_url = f"{feature_layer_url}/{layer_index}/query"
    start = time()
    try:
        resp = requests.get(query_url, params=params, timeout=timeout_sec)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Request failed for layer {layer_index}: {exc}") from exc

    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError(f"Invalid JSON returned (status {resp.status_code})") from exc

    elapsed = time() - start
    print(f"Queried layer {layer_index} in {elapsed:.2f}s; features: {len(data.get("features", []))}")
    return data

def process_features(features: list, is_expressway: bool):
    roads = []
    for feature in features:
        attr = feature.get("attributes", {}) or {}
        region = attr.get("REGION")
        if is_expressway:
            road_class = attr.get("ROAD_CLASS")
            xpres_way = attr.get("XPRES_WAY")
            xpres_name = attr.get("XPRES_NAME")
            shape_length = attr.get("Shape__Length")
            roads.append((region, road_class, xpres_way, xpres_name, shape_length))
        else:
            province = attr.get("PROVINCE")
            deo = attr.get("DEO")
            cong_district = attr.get("CONG_DIST")
            road_class = attr.get("ROAD_SEC_CLASS")
            road_name = attr.get("ROAD_NAME")
            sec_length = attr.get("SEC_LENGTH")
            roads.append((region, province, deo, cong_district, road_class, road_name, sec_length))
    return roads

def generate_output_csv(df: pd.DataFrame):
    filename = input("\nEnter output filename (without extension): ")
    os.makedirs(gis_data_dir, exist_ok=True)

    output_path = os.path.join(gis_data_dir, f"{filename.strip()}.csv")
    df.to_csv(output_path, encoding="utf-8", index=False)

    print(f"\nSaved {len(df)} entries to {output_path}")

def main():
    try:
        # Road Class Types
        road_class_type = select_option(road_class_types, "Enter type of road to query: ")
        is_expressway = road_class_type == "Expressway"

        # Road Region
        region_name = select_option(regions, "Enter region: ")
        is_all = region_name == "All Regions"

        # Fix region names for Expressway road type
        if is_expressway:
            region_map = {
                "National Capital Region": "NCR",
                "Cordillera Administrative Region": "CAR",
                "Negros Island Region": "NIR",
                "Region VII": "RVII" # seriously dpwh
            }
            region_name = region_map.get(region_name, region_name)

        # Max number of entries
        max_count = get_int_input("Enter the maximum number of roads (or -1 for no limit): ")
        max_count_num = "all" if max_count == -1 else max_count

        # Specify region in the query
        where_param = "1=1" if is_all else f"REGION='{region_name}'"
        if is_all:
            print(f"Will query {max_count_num} {road_class_type} roads from all regions")
        else:
            print(f"Will query {max_count_num} {road_class_type} roads from {region_name}")

        # Querying ArcGIS
        params = {
            "where": where_param,
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json"
        }

        if max_count != -1:
            params["resultRecordCount"] = max_count

        print("\nQuerying ArcGIS...\n")

        if is_expressway:
            data = query_road_data(0, params)
        else:
            data = {"features": []}
            new_data = query_road_data(1, params)
            features = new_data.get("features", []) or []
            data["features"].extend(features)

        # Data Processing
        features = data.get("features", []) or []
        if not features:
            print("\nArcGIS returned no features")
            return

        roads = process_features(features, is_expressway)

        # Keep only unique names
        seen = set()
        unique_roads = []
        for r in roads:
            if r not in seen:
                seen.add(r)
                unique_roads.append(r)
        print(f"\nFound {len(roads)} segments ({len(unique_roads)} unique roads)")

        if is_expressway:
            columns = ["region", "road_class", "xpres_way", "xpres_name", "road_length"]
            sort_cols = ["region", "road_class", "xpres_way", "xpres_name"]
        else:
            columns = ["region", "province", "deo", "cong_district", "road_class", "road_name", "road_length"]
            sort_cols = ["region", "province", "deo", "cong_district","road_class", "road_name"]

        df = pd.DataFrame(unique_roads, columns=columns)
        df.sort_values(by=sort_cols, inplace=True)

        generate_output_csv(df)

    except Exception as exc:
        print(f"Error: {exc}")
        exit(1)

if __name__ == "__main__":
    main()