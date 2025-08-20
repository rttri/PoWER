# %%
import geopandas as gpd
import pandas as pd

charger_data_path = "dataset/alt_fuel_stations_all_vehtypes.csv"
# need to use new shapefile
census_tracts = gpd.read_file("dataset/census_tract_shapefile.shp").to_crs("EPSG:4326")

data = pd.read_csv(charger_data_path)
data_oak = data[data["City"].isin(["Oakland", "Piedmont", "Berkeley", "Emeryville"])]

gdf = gpd.GeoDataFrame(data_oak, geometry=gpd.points_from_xy(data_oak.Longitude, data_oak.Latitude))
gdf.crs = "EPSG:4326"

joined_gdf = gpd.sjoin(gdf, census_tracts, how="left")

# Add the census tract information to your original DataFrame
data_oak["census_tract"] = joined_gdf["GEOID"]  # Replace 'TRACTCE' with the appropriate column name from your shapefile

# %%
data_count = data_oak.drop_duplicates()[
    [
        "census_tract",
        "Longitude",
        "Latitude",
        "EV Level1 EVSE Num",
        "EV Level2 EVSE Num",
        "EV DC Fast Count",
        "EV J1772 Connector Count",
        "EV J1772 Power Output (kW)",
        "EV CCS Connector Count",
        "EV CCS Power Output (kW)",
        "EV CHAdeMO Connector Count",
        "EV CHAdeMO Power Output (kW)",
        "EV J3400 Connector Count",
        "EV J3400 Power Output (kW)",
    ]
]

# all EV J1772 Power Output (kW) > 1 if not null
# all EV J1772 Connector are L2 in the column

assert data_count[data_count["EV J1772 Power Output (kW)"] > 0]["EV J1772 Power Output (kW)"].min() > 1

data_count.rename(
    columns={
        "EV J1772 Connector Count": "EV J1772 Connector Count - L2",
        "EV J1772 Power Output (kW)": "EV J1772 Power Output (kW) - L2",
    },
    inplace=True,
)

data_count["EV Level1 EVSE Num"] = data_count["EV Level1 EVSE Num"].fillna(0)
data_count["EV Level2 EVSE Num"] = data_count["EV Level2 EVSE Num"].fillna(0)
data_count["EV DC Fast Count"] = data_count["EV DC Fast Count"].fillna(0)

# %%
data_count["EV Level1 Power Output (kW)"] = 1
data_count["EV Level2 Power Output (kW)"] = data_count["EV J1772 Power Output (kW) - L2"]
data_count["EV Level2 Power Output (kW)"].fillna(13, inplace=True)

data_count.drop(columns=["EV J1772 Connector Count - L2", "EV J1772 Power Output (kW) - L2"], inplace=True)

data_count["EV DC Fast Count"] = data_count["EV DC Fast Count"].fillna(0)
data_count["EV CHAdeMO Connector Count"] = data_count["EV CHAdeMO Connector Count"].fillna(0)
data_count["EV CCS Connector Count"] = data_count["EV CCS Connector Count"].fillna(0)
data_count["EV J3400 Connector Count"] = data_count["EV J3400 Connector Count"].fillna(0)

# for every row, if EV DC Fast Count is 0, then J3400 connector is Level 2,
# so we set EV J3400 Connector Count to 0, and use Level 2 to replace it
data_count["EV J3400 Connector Count"] = data_count["EV J3400 Connector Count"].mask(
    data_count["EV DC Fast Count"] == 0, 0
)


data_count["EV other DC Fast Count"] = (
    data_count["EV DC Fast Count"]
    - data_count["EV CHAdeMO Connector Count"]
    - data_count["EV CCS Connector Count"]
    - data_count["EV J3400 Connector Count"]
)
# note that EV other DC Fast Count could be negative, which means that two connectors are sharing a port (and only one car can charge at a time)

data_count["EV other DC Fast Power Output (kW)"] = 150
data_count["EV CHAdeMO Power Output (kW)"] = data_count["EV CHAdeMO Power Output (kW)"].fillna(150)
data_count["EV J3400 Power Output (kW)"] = data_count["EV J3400 Power Output (kW)"].fillna(150)
data_count["EV CCS Power Output (kW)"] = data_count["EV CCS Power Output (kW)"].fillna(150)

data_count["EV other DC Fast Power Output (kW)"] = data_count["EV other DC Fast Power Output (kW)"].mask(
    data_count["EV other DC Fast Count"] == 0, 0
)
data_count["EV CHAdeMO Power Output (kW)"] = data_count["EV CHAdeMO Power Output (kW)"].mask(
    data_count["EV CHAdeMO Connector Count"] == 0, 0
)
data_count["EV J3400 Power Output (kW)"] = data_count["EV J3400 Power Output (kW)"].mask(
    data_count["EV J3400 Connector Count"] == 0, 0
)
data_count["EV CCS Power Output (kW)"] = data_count["EV CCS Power Output (kW)"].mask(
    data_count["EV CCS Connector Count"] == 0, 0
)


# organize columns
col = [
    "census_tract",
    "Longitude",
    "Latitude",
    "EV Level1 EVSE Num",
    "EV Level1 Power Output (kW)",
    "EV Level2 EVSE Num",
    "EV Level2 Power Output (kW)",
    "EV DC Fast Count",
    "EV CHAdeMO Connector Count",
    "EV CHAdeMO Power Output (kW)",
    "EV CCS Connector Count",
    "EV CCS Power Output (kW)",
    "EV J3400 Connector Count",
    "EV J3400 Power Output (kW)",
    "EV other DC Fast Count",
    "EV other DC Fast Power Output (kW)",
]
data_count = data_count[col]

data_count.to_csv("dataset/alt_fuel_stations_all_types_processed.csv", index=False)
# %%
