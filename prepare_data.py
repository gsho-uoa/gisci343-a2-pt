import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

BASE_DIR = Path("/Users/georgiashort/Desktop/GIS/A2/gisci343-a2-pt")

df = pd.read_csv(
    BASE_DIR / "basic-app" / "data" / "auckland-transport-hourly-bus-boardings-2025-to-2026.csv",
    skiprows=10,
    header=0
)

new_cols = []
for col in df.columns:
    try:
        new_cols.append(pd.to_datetime(col).strftime("%b %Y"))
    except Exception:
        new_cols.append(col)

df.columns = new_cols
df = df.dropna(axis=1, how="all")

id_cols = [
    "Route No",
    "Route Name",
    "RPTP Level of Service",
    "RPTP Range",
    "RPTP Revised Range",
    "Area",
]

patronage_long = df.melt(
    id_vars=id_cols,
    var_name="Month",
    value_name="Boardings"
)

patronage_long["Route No"] = patronage_long["Route No"].astype(str).str.strip()


BASE_DIR = Path("/Users/georgiashort/Desktop/GIS/A2/gisci343-a2-pt")
DATA_DIR = BASE_DIR / "basic-app" / "data"

routes = gpd.read_file(DATA_DIR / "BusService_1148991059056210830.gpkg")
stops = gpd.read_file(DATA_DIR / "BusService_-4169205071737169352.gpkg")

ikea = gpd.GeoDataFrame(
    {"name": ["IKEA Sylvia Park"]},
    geometry=[Point(174.84644611668557, -36.916075676043036)],
    crs="EPSG:4326"
)

ikea_2193 = ikea.to_crs(2193)
routes_2193 = routes.to_crs(2193)
stops_2193 = stops.to_crs(2193)

ikea_buffer = ikea_2193.buffer(1000).iloc[0]

routes_1km = routes_2193[routes_2193.intersects(ikea_buffer)].copy()
stops_1km = stops_2193[stops_2193.intersects(ikea_buffer)].copy()


route_ids = routes_1km["ROUTENUMBER"].astype(str).str.strip()

patronage_ikea = patronage_long[
    patronage_long["Route No"].isin(route_ids)
].copy()

before_months = ["Jul 2025", "Aug 2025", "Sep 2025", "Oct 2025", "Nov 2025"]

patronage_ikea["Period"] = patronage_ikea["Month"].apply(
    lambda x: "Before IKEA" if x in before_months else "After IKEA"
)

patronage_ikea[["min_target", "max_target"]] = (
    patronage_ikea["RPTP Revised Range"]
    .str.split(" - ", expand=True)
    .astype(float)
)

def classify(row):
    if row["Boardings"] < row["min_target"]:
        return "Below target"
    elif row["Boardings"] > row["max_target"]:
        return "Above target"
    else:
        return "Within target"

patronage_ikea["Performance"] = patronage_ikea.apply(classify, axis=1)


stops_2193["distance_m"] = stops_2193.distance(ikea_2193.geometry.iloc[0])
closest_stop = stops_2193.loc[stops_2193["distance_m"].idxmin()]

closest_stop_summary = pd.DataFrame({
    "stop_name": [closest_stop["STOPNAME"]],
    "distance_m": [round(closest_stop["distance_m"], 1)]
})


route_area_summary = (
    patronage_ikea[["Route No", "Route Name", "Area"]]
    .drop_duplicates()
    .sort_values(["Area", "Route No"])
)

area_counts = (
    route_area_summary["Area"]
    .value_counts()
    .reset_index()
)

area_counts.columns = ["Area", "Number of routes"]

df.to_csv(DATA_DIR / "patronage_clean.csv", index=False)
patronage_long.to_csv(DATA_DIR / "patronage_long.csv", index=False)
patronage_ikea.to_csv(DATA_DIR / "patronage_ikea.csv", index=False)

routes_1km.to_crs(4326).to_file(
    DATA_DIR / "routes_1km.gpkg",
    driver="GPKG"
)

stops_1km.to_crs(4326).to_file(
    DATA_DIR / "stops_1km.gpkg",
    driver="GPKG"
)

closest_stop_summary.to_csv(
    DATA_DIR / "closest_stop_summary.csv",
    index=False
)

route_area_summary.to_csv(
    DATA_DIR / "route_area_summary.csv",
    index=False
)

area_counts.to_csv(
    DATA_DIR / "area_counts.csv",
    index=False
)

print("Data preparation complete.")
print("Routes near IKEA:", sorted(route_ids.unique()))
print("Closest stop:", closest_stop_summary.iloc[0].to_dict())
print(area_counts)

