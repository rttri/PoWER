"""
Filename: demo_with_residential_charger.py
Author: Ruiting Wang
Date: 2024-06-24

Description: This script calculates the number of home chargers (per vehicle) for each census tract in Oakland, CA, based on the demographic data and the residential charger access survey data.

Note:
1. The residential charger access survey data is from the California Energy Commission's report (https://www.energy.ca.gov/sites/default/files/2022-01/CEC-600-2022-021.pdf).
2. The definition of the multi-family housing type in home charger access survey data includes all housings with more than one unit, thus is alligned with the definition in the demographic data.

"""

# %%
import pandas as pd

# %%
# Table C-5
raw_data = pd.DataFrame(
    {
        "income_group": [
            "60000_or_less",
            "60000_or_less",
            "60000_to_100000",
            "60000_to_100000",
            "100000_or_more",
            "100000_or_more",
        ],
        "housing_type": [
            "single_family",
            "multi_family",
            "single_family",
            "multi_family",
            "single_family",
            "multi_family",
        ],
        "exsiting_access_pct": [0.25, 0.09, 0.29, 0.22, 0.33, 0.26],
        "potential_access_pct": [0.4, 0.22, 0.46, 0.28, 0.50, 0.34],
    }
)
income_th1 = 60000
income_th2 = 100000

demo_df = pd.read_csv(
    "dataset/Demographic Processing 2/01 Census Tracts/Oakland_Census_Justice40_gpd_CTs.csv", index_col=0
).reset_index(drop=True)


# %%
# Calculate the number of home chargers
sf_exist_temp = raw_data.loc[
    demo_df["Median household income in the past 12 months (in 2022 inflation-adjusted dollars)"].apply(
        lambda x: 0 if x < income_th1 else (2 if x < income_th2 else 4)
    ),
    "exsiting_access_pct",
].reset_index(drop=True)

mf_exist_temp = raw_data.loc[
    demo_df["Median household income in the past 12 months (in 2022 inflation-adjusted dollars)"].apply(
        lambda x: 1 if x < income_th1 else (3 if x < income_th2 else 5)
    ),
    "exsiting_access_pct",
].reset_index(drop=True)

sf_potential_temp = raw_data.loc[
    demo_df["Median household income in the past 12 months (in 2022 inflation-adjusted dollars)"].apply(
        lambda x: 0 if x < income_th1 else (2 if x < income_th2 else 4)
    ),
    "potential_access_pct",
].reset_index(drop=True)

mf_potential_temp = raw_data.loc[
    demo_df["Median household income in the past 12 months (in 2022 inflation-adjusted dollars)"].apply(
        lambda x: 1 if x < income_th1 else (3 if x < income_th2 else 5)
    ),
    "potential_access_pct",
].reset_index(drop=True)

demo_df["potential_home_chargers_per_veh"] = (
    demo_df["perc_single_unit_dwellings"] / 100 * sf_potential_temp
    + demo_df["perc_multi_unit_dwellings"] / 100 * mf_potential_temp
)

demo_df["exist_home_chargers_per_veh"] = (
    demo_df["perc_single_unit_dwellings"] / 100 * sf_exist_temp
    + demo_df["perc_multi_unit_dwellings"] / 100 * mf_exist_temp
)

# Save the data
demo_df.to_csv("demographic_data_with_residential_charger.csv")
