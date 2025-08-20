"""

Author: Ruiting Wang
Date: January 2025

This module provides the class for evaluating equity in electric vehicle (EV) charger distribution.

"""

import numpy as np


class EVChargerEquityEvaluationwEqChar:
    def __init__(self, df_data, df_commute_data, df_vkt_data):

        self.df1 = df_data
        self.df2 = df_commute_data
        self.df3 = df_vkt_data
        self.char_num_home = self.df1["char_num_home"]
        self.char_num_not_home = self.df1["char_num_not_home"]
        self.char_capacity_home = self.df1["char_capacity_home"]
        self.char_capacity_not_home = self.df1["char_capacity_not_home"]
        self.work_popu = self.df1["work_popu_LODES"]
        self.n_trip_ij = self.df2.values
        self.d_trip_ij = self.df3.values
        self.popu_ct = self.df1["popu"]
        self.num_of_veh_ct = self.df1["veh_num"]

        if "workplace_char_capacity_kW" not in df_data.columns:
            if "workplace_char_num" not in df_data.columns:
                self.df1["workplace_char_capacity_kW"] = 0
                self.df1["workplace_char_num"] = 0
            else:
                self.df1["workplace_char_capacity_kW"] = self.df1["workplace_char_num"] * 13
        else:
            if "workplace_char_num" not in df_data.columns:
                self.df1["workplace_char_num"] = self.df1["workplace_char_capacity_kW"] / 13
            else:
                pass

        self.eq_wp_char_dist()
        self.compute_info()

    def eq_wp_char_dist(self):
        self.workplace_char_capacity_kW = self.df1["workplace_char_capacity_kW"].values
        self.n_trip_ij_pct = self.n_trip_ij / self.n_trip_ij.sum(axis=0)[None, :]
        assert self.n_trip_ij_pct.shape == self.n_trip_ij.shape
        assert self.n_trip_ij.sum(axis=0)[102] == self.work_popu.values[102]
        self.eq_workplace_char_capacity_kW = self.n_trip_ij_pct @ self.workplace_char_capacity_kW
        self.df1["eq_workplace_char_capacity_kW"] = self.eq_workplace_char_capacity_kW

    def compute_info(self):
        self.df1["car_ownership_rate"] = self.df1["veh_num"] / self.df1["popu"]

        self.df1["total_char_num"] = (
            self.df1["char_num_not_home"] + self.df1["char_num_home"] + self.df1["workplace_char_num"]
        )
        self.df1["eq_total_char_num"] = (
            self.df1["char_num_not_home"] + self.df1["char_num_home"] + self.df1["eq_workplace_char_capacity_kW"] / 13
        )

        self.df1["total_char_capacity"] = (
            self.df1["char_capacity_not_home"] + self.df1["char_capacity_home"] + self.df1["workplace_char_capacity_kW"]
        )
        self.df1["eq_total_char_capacity"] = (
            self.df1["char_capacity_not_home"]
            + self.df1["char_capacity_home"]
            + self.df1["eq_workplace_char_capacity_kW"]
        )
        # real number of chargers
        self.df1["char_per_capita"] = self.df1["total_char_num"] / self.df1["popu"]
        self.df1["char_per_veh"] = self.df1["total_char_num"] / self.df1["veh_num"]
        self.df1["char_capacity_per_capita"] = self.df1["total_char_capacity"] / self.df1["popu"]
        self.df1["char_capacity_per_car"] = self.df1["total_char_capacity"] / self.df1["veh_num"]
        # equivalent number of chargers
        self.df1["eq_char_per_capita"] = self.df1["eq_total_char_num"] / self.df1["popu"]
        self.df1["eq_char_per_veh"] = self.df1["eq_total_char_num"] / self.df1["veh_num"]
        self.df1["eq_char_capacity_per_capita"] = self.df1["eq_total_char_capacity"] / self.df1["popu"]
        self.df1["eq_char_capacity_per_car"] = self.df1["eq_total_char_capacity"] / self.df1["veh_num"]

        # real number of chargers
        self.df1["VKT_flow_out_km"] = self.df3.sum(axis=1).values
        self.df1["char_per_VKT_out"] = self.df1["total_char_num"] / self.df1["VKT_flow_out_km"]
        self.df1["char_capacity_per_VKT_out"] = self.df1["total_char_capacity"] / self.df1["VKT_flow_out_km"]

        self.df1["VKT_flow_in_km"] = self.df3.sum(axis=0).values
        self.df1["char_per_VKT_in"] = self.df1["total_char_num"] / self.df1["VKT_flow_in_km"]
        self.df1["char_capacity_per_VKT_in"] = self.df1["total_char_capacity"] / self.df1["VKT_flow_in_km"]

        # equivalent number of chargers
        self.df1["eq_VKT_flow_out_km"] = self.df3.sum(axis=1).values
        self.df1["eq_char_per_VKT_out"] = self.df1["eq_total_char_num"] / self.df1["eq_VKT_flow_out_km"]
        self.df1["eq_char_capacity_per_VKT_out"] = self.df1["eq_total_char_capacity"] / self.df1["eq_VKT_flow_out_km"]

        self.df1["eq_VKT_flow_in_km"] = self.df3.sum(axis=0).values
        self.df1["eq_char_per_VKT_in"] = self.df1["eq_total_char_num"] / self.df1["eq_VKT_flow_in_km"]
        self.df1["eq_char_capacity_per_VKT_in"] = self.df1["eq_total_char_capacity"] / self.df1["eq_VKT_flow_in_km"]

    def compute_equity(self, equity_indicator, demographic_group, disparity_index, **kwargs):
        """
        This function computes the equity ofs
        """
        if demographic_group not in ["income_level", "mud_level", "employment_level", "major_ethnicity"]:
            raise ValueError("Invalid demongraphic group")

        if equity_indicator not in [
            "char_per_capita",
            "char_capacity_per_capita",
            "char_per_veh",
            "char_capacity_per_car",
            "char_per_VKT_out",
            "char_capacity_per_VKT_out",
        ]:
            raise ValueError("Invalid equity indicator")

        if disparity_index not in [
            "mean_abs_dev",
            "relative_mean_abs_dev",
            "gini_coefficient",
            "lorenz_curve",
            "theil_index",
        ]:
            raise ValueError("Invalid disparity index")

        if equity_indicator == "char_per_capita":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["char_per_capita"].values)
            )

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["total_char_num", "popu"]].sum()
            temp["char_per_capita"] = temp["total_char_num"] / temp["popu"]
            inter_disparity = self.compute_disparity(disparity_index, temp["char_per_capita"].values)
            return inter_disparity, intra_disparity

        elif equity_indicator == "char_capacity_per_capita":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["char_capacity_per_capita"].values)
            )

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["total_char_capacity", "popu"]].sum()
            temp["char_capacity_per_capita"] = temp["total_char_capacity"] / temp["popu"]
            inter_disparity = self.compute_disparity(disparity_index, temp["char_capacity_per_capita"].values)

            return inter_disparity, intra_disparity

        elif equity_indicator == "char_per_veh":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["char_per_veh"].values)
            )

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["total_char_num", "veh_num"]].sum()
            temp["char_per_veh"] = temp["total_char_num"] / temp["veh_num"]
            inter_disparity = self.compute_disparity(disparity_index, temp["char_per_veh"].values)
            return inter_disparity, intra_disparity

        elif equity_indicator == "char_capacity_per_car":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["char_capacity_per_car"].values)
            )

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["total_char_capacity", "veh_num"]].sum()
            temp["char_capacity_per_car"] = temp["total_char_capacity"] / temp["veh_num"]
            inter_disparity = self.compute_disparity(disparity_index, temp["char_capacity_per_car"].values)
            return inter_disparity, intra_disparity

        elif equity_indicator == "char_per_VKT_out":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["char_per_VKT_out"].values)
            )

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["total_char_num", "VKT_flow_out_km"]].sum()
            temp["char_per_VKT_out"] = temp["total_char_num"] / temp["VKT_flow_out_km"]
            inter_disparity = self.compute_disparity(disparity_index, temp["char_per_VKT_out"].values)
            return inter_disparity, intra_disparity

        elif equity_indicator == "char_capacity_per_VKT_out":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["char_capacity_per_VKT_out"].values)
            )

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["total_char_capacity", "VKT_flow_out_km"]].sum()
            temp["char_capacity_per_VKT_out"] = temp["total_char_capacity"] / temp["VKT_flow_out_km"]
            inter_disparity = self.compute_disparity(disparity_index, temp["char_capacity_per_VKT_out"].values)
            return inter_disparity, intra_disparity

    def compute_equity_eq_wpc(self, equity_indicator, demographic_group, disparity_index, **kwargs):
        """
        This function computes the equity ofs
        """
        if demographic_group not in ["income_level", "mud_level", "employment_level", "major_ethnicity"]:
            raise ValueError("Invalid demongraphic group")

        if equity_indicator not in [
            "eq_char_per_capita",
            "eq_char_capacity_per_capita",
            "eq_char_per_veh",
            "eq_char_capacity_per_car",
            "eq_char_per_VKT_out",
            "eq_char_capacity_per_VKT_out",
        ]:
            raise ValueError("Invalid equity indicator")

        if disparity_index not in [
            "mean_abs_dev",
            "relative_mean_abs_dev",
            "gini_coefficient",
            "lorenz_curve",
            "theil_index",
        ]:
            raise ValueError("Invalid disparity index")

        if equity_indicator == "eq_char_per_capita":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["eq_char_per_capita"].values)
            )

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["eq_total_char_num", "popu"]].sum()
            temp["eq_char_per_capita"] = temp["eq_total_char_num"] / temp["popu"]
            inter_disparity = self.compute_disparity(disparity_index, temp["eq_char_per_capita"].values)
            return inter_disparity, intra_disparity

        elif equity_indicator == "eq_char_capacity_per_capita":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["eq_char_capacity_per_capita"].values)
            )
            if demographic_group == "major_ethnicity":
                print(self.df1.groupby(demographic_group)[["eq_char_capacity_per_capita"]].mean())
                print(intra_disparity)

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["eq_total_char_capacity", "popu"]].sum()
            temp["eq_char_capacity_per_capita"] = temp["eq_total_char_capacity"] / temp["popu"]
            inter_disparity = self.compute_disparity(disparity_index, temp["eq_char_capacity_per_capita"].values)

            if demographic_group == "major_ethnicity":
                print(temp)
                print(inter_disparity)

            return inter_disparity, intra_disparity

        elif equity_indicator == "eq_char_per_veh":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["eq_char_per_veh"].values)
            )

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["eq_total_char_num", "veh_num"]].sum()
            temp["eq_char_per_veh"] = temp["eq_total_char_num"] / temp["veh_num"]
            inter_disparity = self.compute_disparity(disparity_index, temp["eq_char_per_veh"].values)
            return inter_disparity, intra_disparity

        elif equity_indicator == "eq_char_capacity_per_car":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["eq_char_capacity_per_car"].values)
            )

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["eq_total_char_capacity", "veh_num"]].sum()
            temp["eq_char_capacity_per_car"] = temp["eq_total_char_capacity"] / temp["veh_num"]
            inter_disparity = self.compute_disparity(disparity_index, temp["eq_char_capacity_per_car"].values)
            return inter_disparity, intra_disparity

        elif equity_indicator == "eq_char_per_VKT_out":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["eq_char_per_VKT_out"].values)
            )

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["eq_total_char_num", "VKT_flow_out_km"]].sum()
            temp["eq_char_per_VKT_out"] = temp["eq_total_char_num"] / temp["VKT_flow_out_km"]
            inter_disparity = self.compute_disparity(disparity_index, temp["eq_char_per_VKT_out"].values)
            return inter_disparity, intra_disparity

        elif equity_indicator == "eq_char_capacity_per_VKT_out":
            # select the data in each group, compute disparity index in each group
            intra_disparity = self.df1.groupby(demographic_group).apply(
                lambda x: self.compute_disparity(disparity_index, x["eq_char_capacity_per_VKT_out"].values)
            )

            # compute the disparity index in the whole region
            temp = self.df1.groupby(demographic_group)[["eq_total_char_capacity", "VKT_flow_out_km"]].sum()
            temp["eq_char_capacity_per_VKT_out"] = temp["eq_total_char_capacity"] / temp["VKT_flow_out_km"]
            inter_disparity = self.compute_disparity(disparity_index, temp["eq_char_capacity_per_VKT_out"].values)
            return inter_disparity, intra_disparity

    def compute_disparity(self, disparity_index, data):
        """
        This function computes the mean absolute deviation of the input data.
        :return: mean absolute deviation of the input data
        """
        if disparity_index == "mean_abs_dev":
            return np.mean(np.abs(data - np.mean(data)))

        elif disparity_index == "relative_mean_abs_dev":
            return np.mean(np.abs(data - np.mean(data))) / np.mean(data)

        # elif disparity_index == "gini_coefficient":
        #     data = np.sort(data)
        #     n = data.shape[0]
        #     index = np.arange(1, n + 1)
        #     return 2 * np.sum((n + 1 - index) * data) / (n * np.sum(data))

        elif disparity_index == "gini_coefficient":
            data = np.sort(data)
            n = data.shape[0]
            index = np.arange(1, n + 1)
            return 1 + (1 / n) - (2 / n) * np.sum((n + 1 - index) * data) / (np.sum(data))

        elif disparity_index == "lorenz_curve":
            data = np.sort(data)
            n = data.shape[0]
            index = np.arange(1, n + 1)
            return np.sum((2 * index - n - 1) * data) / (n * np.sum(data))

        elif disparity_index == "theil_index":
            return np.sum(data * np.log(data / np.mean(data)))

        else:
            raise ValueError("Invalid disparity index")
