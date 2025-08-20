"""

Author: Ruiting Wang
Date: August 2024

This script is used to process the demographic data and commuting data.

"""

# %%
import geopandas as gpd

# import numpy as np
import pandas as pd


# %%
class DataProcessor:
    """
    DataProcessor class is used to process the demographic data and commuting data.
    """

    def __init__(
        self,
        demo_path="../dataset/demographic_data_with_residential_charger.csv",
        # work_flow_path="../dataset/Echo O-D Pair Processing/01 Census Tracts/O_D_pairs_lat_lon_work_pop_April_June_2022_cts_pivot.csv",
        work_flow_path="../helper/od_process/n_ij_census_tract_LODES_data.csv",
        dist_matrix_path="../helper/od_process/d_ij_census_tract_LODES_data.csv",
        charger_num_path="../dataset/alt_fuel_stations_all_types_processed.csv",
    ):
        self.demo_data = pd.read_csv(demo_path, index_col=0).reset_index(drop=True)
        self.work_flow_mat = pd.read_csv(work_flow_path, index_col=0)
        self.dist_matrix_km = pd.read_csv(dist_matrix_path, index_col=0)
        self.charger_num = pd.read_csv(charger_num_path, index_col=0)

    def process_demo_data(self, **kwargs):
        """
        Process the demographic data. Add categorical columns for income, MUD, employment based on the thresholds.

        If the thresholds are not provided in **kwargs, the data will be divided into four categories based on the quantiles.
        """

        # remove the rows with missing data (two CTs with 15 and 20 people)
        self.demo_data = self.demo_data[
            self.demo_data["Median household income in the past 12 months (in 2022 inflation-adjusted dollars)"].astype(
                float
            )
            > 0
        ]

        # demographic partition
        if "income_bins" in kwargs:
            bins_num = kwargs["income_bins"]
        else:
            bins_num = 4
        assert bins_num >= 1, "The number of bins should be greater than 1."
        self.demo_data["income_level"] = pd.qcut(
            self.demo_data["Median household income in the past 12 months (in 2022 inflation-adjusted dollars)"],
            q=bins_num,
            labels=[f"Q{i}" for i in range(1, bins_num + 1)],
        )

        if "mud_bins" in kwargs:
            bins_num = kwargs["mud_bins"]
        else:
            bins_num = 4
        assert bins_num >= 1, "The number of bins should be greater than 1."
        self.demo_data["mud_level"] = pd.qcut(
            self.demo_data["perc_multi_unit_dwellings"],
            q=bins_num,
            labels=[f"Q{i}" for i in range(1, bins_num + 1)],
        )
        # else:
        #     self.demo_data["mud_level"] = pd.cut(
        #         self.demo_data["perc_multi_unit_dwellings"],
        #         bins=[0] + self.demo_data["perc_multi_unit_dwellings"].quantile([0.25, 0.5, 0.75]).to_list() + [np.inf],
        #         labels=["Low", "Medium", "High", "Very High"],
        #     )

        if "employment_bins" in kwargs:
            bins_num = kwargs["employment_bins"]
        else:
            bins_num = 4
        assert bins_num >= 1, "The number of bins should be greater than 1."
        self.demo_data["employment_level"] = pd.qcut(
            self.demo_data["Employment Status for the Population 16 Years and Over"]
            / self.demo_data["Total Population"],
            q=bins_num,
            labels=[f"Q{i}" for i in range(1, bins_num + 1)],
        )
        # else:
        #     self.demo_data["employment_level"] = pd.cut(
        #         self.demo_data["Employment Status for the Population 16 Years and Over"]
        #         / self.demo_data["Total Population"],
        #         bins=[0]
        #         + (
        #             self.demo_data["Employment Status for the Population 16 Years and Over"]
        #             / self.demo_data["Total Population"]
        #         )
        #         .quantile([0.25, 0.5, 0.75])
        #         .to_list()
        #         + [np.inf],
        #         labels=["Low", "Medium", "High", "Very High"],
        # )

        # update ethnicity labels
        self.demo_data = self.demo_data.replace(
            {
                "Race - White Alone": "White",
                "Race - Black or African American alone": "Black",
                "Race - Asian alone": "Asian",
                "Race - Some Other Race alone": "Other",
            }
        )

        # compute charger capacity (including home and not home chargers)
        charger_num = self.process_charger_capacity()
        self.demo_data = self.demo_data.merge(charger_num, left_on="tract_GEOID", right_on="census_tract", how="left")
        self.demo_data.drop(columns=["census_tract"], inplace=True)
        self.demo_data["char_num_not_home"] = self.demo_data["char_num_not_home"].fillna(0).astype(int)
        self.demo_data["char_capacity_not_home"] = self.demo_data["char_capacity_not_home"].fillna(0).astype(int)

        self.demo_data["char_num_home"] = (
            self.demo_data["exist_home_chargers_per_veh"] * self.demo_data["Total Vehicle Count"]
        ).astype(int)
        self.demo_data["char_capacity_home"] = self.demo_data["char_num_home"]

        # keep only the columns that are needed
        self.demo_data["Total Population"] = self.demo_data["Total Population"].astype(int)
        self.demo_data = self.demo_data[
            [
                "tract_GEOID",
                "Total Population",
                "Employment Status for the Population 16 Years and Over",
                "Median household income in the past 12 months (in 2022 inflation-adjusted dollars)",
                "perc_multi_unit_dwellings",
                "income_level",
                "mud_level",
                "employment_level",
                "Majority Race",
                "char_num_home",
                "char_capacity_home",
                "char_capacity_not_home",
                "char_num_not_home",
                "Total Vehicle Count",
                "num_public_charger",
                "Identified as disadvantaged",
                "geometry",
            ]
        ]

        # rename the columns
        self.demo_data.rename(
            columns={
                "tract_GEOID": "tract_id",
                "Total Population": "popu",
                "Majority Race": "major_ethnicity",
                "Employment Status for the Population 16 Years and Over": "employed_popu",
                "Median household income in the past 12 months (in 2022 inflation-adjusted dollars)": "income",
                "Total Vehicle Count": "veh_num",
                "num_public_charger": "pub_char_num",
                "Identified as disadvantaged": "disadvantaged",
            },
            inplace=True,
        )

        self.demo_data.reset_index(drop=True, inplace=True)
        self.demo_data = gpd.GeoDataFrame(self.demo_data)
        self.demo_data["geometry"] = gpd.GeoSeries.from_wkt(self.demo_data["geometry"])
        self.demo_data.set_geometry("geometry", inplace=True)

        # filter out the census tracts that are not in Oakland
        self.filter_oakland_cts()
        self.process_work_flow_data()

        # update the distance matrix col and index to int
        self.dist_matrix_km.columns = self.dist_matrix_km.columns.astype(int)
        self.dist_matrix_km.index = self.dist_matrix_km.index.astype(int)
        col = self.demo_data["tract_id"].values.tolist()
        self.dist_matrix_km = self.dist_matrix_km[col].T[col].T

        # element-wise multiplication of the distance matrix and the commuting matrix
        self.vmt_matrix = pd.DataFrame(
            self.dist_matrix_km.values * self.work_flow_mat.values,
            index=self.dist_matrix_km.index,
            columns=self.dist_matrix_km.columns,
        )

        # update work population at the census tract level (scalded by percentage).
        # Note that the employed population is used as the base population for scaling.

        self.demo_data["work_popu_LODES"] = self.work_flow_mat.values.sum(
            axis=0
        )  # summation of the column or working cts
        self.demo_data["employed_popu_LODES"] = self.work_flow_mat.values.sum(
            axis=1
        )  # summation of the row or living cts
        self.demo_data["work_popu_processed"] = (
            (
                self.demo_data["employed_popu"]
                / self.demo_data["employed_popu_LODES"]
                * self.demo_data["work_popu_LODES"]
            )
            .round(0)
            .astype(int)
        )

        # NOTE: four columns in the dataset represent the population
        # "popu" is the total population
        # "employed_popu" is the employed population in the CT based on the census data
        # "employed_popu_LODES" is the population live in the CT but work in others based on the echo data (the concept is similar to employed population)
        # "work_popu_LODES" is the population that goes to the CT to work based on the echo data
        # "work_popu_processed" is the population that goes to the CT to work, converted from the ratio of "popu"
        # and will be the final population used in the optimization model

        return self.demo_data, self.work_flow_mat, self.vmt_matrix

    def process_charger_capacity(self):
        """
        Compute the charger capacity for each census tract.
        """

        charger_num = self.charger_num.copy()
        charger_num.drop(columns=["Longitude", "Latitude"], inplace=True)
        charger_num["L1_capacity"] = charger_num["EV Level1 EVSE Num"] * charger_num["EV Level1 Power Output (kW)"]
        charger_num["L2_capacity"] = charger_num["EV Level2 EVSE Num"] * charger_num["EV Level2 Power Output (kW)"]
        charger_num["DCFC_capacity"] = (
            charger_num["EV CHAdeMO Connector Count"] * charger_num["EV CHAdeMO Power Output (kW)"]
            + charger_num["EV CCS Connector Count"] * charger_num["EV CCS Power Output (kW)"]
            + charger_num["EV J3400 Connector Count"] * charger_num["EV J3400 Power Output (kW)"]
            + charger_num["EV other DC Fast Count"] * charger_num["EV other DC Fast Power Output (kW)"]
        )
        charger_num["char_capacity_not_home"] = (
            charger_num["L1_capacity"] + charger_num["L2_capacity"] + charger_num["DCFC_capacity"]
        )
        charger_num["char_num_not_home"] = (
            charger_num["EV Level1 EVSE Num"] + charger_num["EV Level2 EVSE Num"] + charger_num["EV DC Fast Count"]
        )

        charger_num = (
            charger_num.groupby("census_tract")[["char_capacity_not_home", "char_num_not_home"]].sum().reset_index()
        )
        return charger_num

    def process_work_flow_data(self):
        """
        process the commuting data to matrix of visiting frequency between OD pairs. The data is in the form of
        a pivot table with the columns and rows as the census tracts.

        """
        self.work_flow_mat.fillna(0, inplace=True)
        self.work_flow_mat.columns = [
            int(float(i)) if isinstance(i, object) else i for i in self.work_flow_mat.columns[:-1]
        ] + self.work_flow_mat.columns[-1:].tolist()
        self.work_flow_mat.index = [
            int(float(i)) if isinstance(i, object) else i for i in self.work_flow_mat.index[:-1]
        ] + self.work_flow_mat.index[-1:].tolist()

        self.work_flow_mat = self.work_flow_mat.round(0).astype(int)
        col = self.demo_data["tract_id"].values.tolist()
        self.work_flow_mat = self.work_flow_mat[col].T[col].T
        return 0

    # def demo_categorize(self, demo_group):
    #     """
    #     Categorize the demographic data based on the selected demographic features.
    #     """
    #     if demo_group == "income":
    #         self.demo_data["demo_group"] = self.demo_data["income_level"]
    #     elif demo_group == "MUD":
    #         self.demo_data["demo_group"] = self.demo_data["mud_level"]
    #     elif demo_group == "employment":
    #         self.demo_data["demo_group"] = self.demo_data["employment_level"]
    #     elif demo_group == "major_ethnicity":
    #         self.demo_data["demo_group"] = self.demo_data["major_ethnicity"]
    #     elif demo_group == "DAC":
    #         self.demo_data["demo_group"] = self.demo_data["disadvantaged"]
    #     # if no demographic groups are selected, categorize people by CT
    #     elif demo_group == "none":
    #         self.demo_data["demo_group"] = self.demo_data["tract_id"]
    #     else:
    #         raise ValueError("Invalid demographic group")

    #     demo_category_list = []
    #     for item in self.demo_data["demo_group"].unique():
    #         demo_category_list.append(self.demo_data[self.demo_data["demo_group"] == item].index)
    #     return demo_category_list

    def filter_oakland_cts(self):
        """
        Keep only the census tracts that are in Oakland.
        """
        self.oak_ct_list = (
            self.demo_data["tract_id"]
            .astype(str)
            .str.startswith(("600140", "600141", "60014262", "60014261", "60019819", "60019820", "60019832"))
        )
        self.demo_data = self.demo_data[self.oak_ct_list].reset_index(drop=True)

        return 0

    def save_data(self, output_path):
        self.demo_data.to_csv(output_path, index=False)


# %%
