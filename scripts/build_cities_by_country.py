import csv
import json
import os
from collections import defaultdict

# -----------------------------------------
# CONFIG
# -----------------------------------------

# Local CSV path (after you manually download & extract it)
CSV_LOCAL_PATH = os.path.join(os.path.dirname(__file__), "_temp", "worldcities_basic.csv")

OUTPUT_CITIES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cities")
OUTPUT_COUNTRIES_JSON = os.path.join(os.path.dirname(__file__), "..", "data", "countries.json")
OUTPUT_COUNTRIES_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "countries.csv")

# -----------------------------------------
# HELPERS
# -----------------------------------------

def parse_population(value):
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def is_capital(capital_value):
    if not capital_value:
        return False
    cv = capital_value.strip().lower()
    # In SimpleMaps world cities, capital field is like:
    # "primary" (national capital), "admin" (admin capital), "minor", or ""
    return cv in ("primary", "admin")


def ensure_output_dirs():
    if not os.path.exists(OUTPUT_CITIES_DIR):
        os.makedirs(OUTPUT_CITIES_DIR, exist_ok=True)


def build_from_csv(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    by_country_cities = defaultdict(list)
    countries_meta = {}  # iso2 -> meta dict

    print(f"Reading CSV: {csv_path}")
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            iso2 = (row.get("iso2") or "").upper()
            if not iso2:
                continue  # skip rows without country code

            country_name = row.get("country") or ""
            iso3 = (row.get("iso3") or "").upper() if "iso3" in row else ""

            # ---- build cities ----
            city_obj = {
                "name": row.get("city") or "",
                "country_iso2": iso2,
                "state": row.get("admin_name") or "",
                "is_capital": is_capital(row.get("capital")),
                "latitude": float(row.get("lat") or 0),
                "longitude": float(row.get("lng") or 0),
                "population": parse_population(row.get("population"))
            }
            by_country_cities[iso2].append(city_obj)

            # ---- build countries meta ----
            if iso2 not in countries_meta:
                countries_meta[iso2] = {
                    "iso2": iso2,
                    "iso3": iso3,
                    "name": country_name,
                    "capital": "",
                    "region": "",      # not available in this dataset
                    "subregion": "",   # not available in this dataset
                    "latitude": None,
                    "longitude": None
                }

            # if this row is the primary capital, store it
            if (row.get("capital") or "").strip().lower() == "primary":
                countries_meta[iso2]["capital"] = row.get("city") or ""
                try:
                    countries_meta[iso2]["latitude"] = float(row.get("lat") or 0)
                    countries_meta[iso2]["longitude"] = float(row.get("lng") or 0)
                except ValueError:
                    countries_meta[iso2]["latitude"] = None
                    countries_meta[iso2]["longitude"] = None

    print(f"Countries found: {len(by_country_cities)}")

    # -----------------------------------
    # Write cities per country
    # -----------------------------------
    ensure_output_dirs()

    for iso2, cities in by_country_cities.items():
        out_path = os.path.join(OUTPUT_CITIES_DIR, f"{iso2}.json")
        cities_sorted = sorted(cities, key=lambda c: c["name"])
        with open(out_path, "w", encoding="utf-8") as out_f:
            json.dump(cities_sorted, out_f, ensure_ascii=False)
        print(f"Wrote {len(cities_sorted):5d} cities to {out_path}")

    # -----------------------------------
    # Write countries.json and countries.csv
    # -----------------------------------
    countries_list = sorted(countries_meta.values(), key=lambda c: c["name"])

    # Fill None lat/long with 0 for JSON consistency
    for c in countries_list:
        if c["latitude"] is None:
            c["latitude"] = 0
        if c["longitude"] is None:
            c["longitude"] = 0

    # JSON
    with open(OUTPUT_COUNTRIES_JSON, "w", encoding="utf-8") as jf:
        json.dump(countries_list, jf, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(countries_list)} countries to {OUTPUT_COUNTRIES_JSON}")

    # CSV
    fieldnames = ["iso2", "iso3", "name", "capital", "region", "subregion", "latitude", "longitude"]
    with open(OUTPUT_COUNTRIES_CSV, "w", encoding="utf-8", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()
        for c in countries_list:
            writer.writerow(c)
    print(f"Wrote {len(countries_list)} countries to {OUTPUT_COUNTRIES_CSV}")

    print("\nDone. All city and country files created.")


def main():
    print(f"Using CSV: {CSV_LOCAL_PATH}")
    build_from_csv(CSV_LOCAL_PATH)


if __name__ == "__main__":
    main()
