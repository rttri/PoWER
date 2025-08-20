"""
Author: Ruiting Wang
Date: January 2025

This function calculates the distance between two gps coordinates using the Google Maps API.

"""

import geopandas as gpd

# %%
import googlemaps
import pandas as pd

gmaps = googlemaps.Client(key="your api key")  # replace with your own API key!

# %%
work_flow_path = "helper/od_process/n_ij_census_tract_LODES_data.csv"
work_flow_mat = pd.read_csv(work_flow_path, index_col=0)
census_tracts = gpd.read_file("dataset/tl_2022_06_tract/tl_2022_06_tract.shp").to_crs("EPSG:4326")
# 4326 is the coordinate system on a sphere, which is used by Google Maps API (e.g. distance calculation)
# 3857 is the coordinate system on a plane, which is used by the shapefile (e.g. plotting)

ct_list = work_flow_mat.columns.tolist()[:-1]
census_tracts["centroid"] = census_tracts.centroid
census_tracts["centroid_lat"] = census_tracts.centroid.y
census_tracts["centroid_lon"] = census_tracts.centroid.x


# %%
# sort ct by ct_list
census_tracts["GEOID"] = census_tracts["GEOID"].astype(str)
# remove the first zero in the GEOID
census_tracts["GEOID"] = census_tracts["GEOID"].apply(lambda x: x[1:])
census_tracts = census_tracts[census_tracts["GEOID"].isin(ct_list)]
census_tracts = census_tracts.sort_values(by="GEOID")
# make sure the order of census tract is matching the commuting matrix
assert census_tracts["GEOID"].tolist() == ct_list


# %%
def create_distance_matrix():
    distance_matrix = pd.DataFrame(index=ct_list, columns=ct_list)
    for i in ct_list:
        for j in ct_list:
            if i == j:
                distance_matrix.loc[i, j] = calculate_radius(census_tracts[census_tracts["GEOID"] == i])
            else:
                lat1 = census_tracts[census_tracts["GEOID"] == i]["centroid_lat"].values[0]
                lon1 = census_tracts[census_tracts["GEOID"] == i]["centroid_lon"].values[0]
                lat2 = census_tracts[census_tracts["GEOID"] == j]["centroid_lat"].values[0]
                lon2 = census_tracts[census_tracts["GEOID"] == j]["centroid_lon"].values[0]
                distance_matrix.loc[i, j] = calculate_distance(lat1, lon1, lat2, lon2)
    return distance_matrix


def calculate_distance(lat1, lon1, lat2, lon2):

    distance = gmaps.distance_matrix([str(lat1) + " " + str(lon1)], [str(lat2) + " " + str(lon2)], mode="driving")
    # print(distance)
    return distance["rows"][0]["elements"][0]["distance"]["text"].split(" ")[0]


def calculate_radius(census_tract):
    """
    calculate the maximum driving distance in a census tract. We use 0.5*max_dist as the radius, which is used to compute the commuting VMT in the same census tract.
    """
    min_lat = census_tract.bounds["miny"].values[0]
    min_lon = census_tract.bounds["minx"].values[0]
    max_lat = census_tract.bounds["maxy"].values[0]
    max_lon = census_tract.bounds["maxx"].values[0]
    distance = gmaps.distance_matrix(
        [str(min_lat) + " " + str(min_lon)], [str(max_lat) + " " + str(max_lon)], mode="driving"
    )
    return float(distance["rows"][0]["elements"][0]["distance"]["text"].split(" ")[0]) / 2


# %%
distance_matrix = create_distance_matrix()
# %%
distance_matrix.to_csv("helper/od_process/d_ij_census_tract_LODES_data.csv")
# %%
