"""

Author: Ruiting Wang
Date: January 2025

This script is used to run the optimization model for EV charger deployment.

"""

import datetime as dt
import json
import os
import warnings

import numpy as np

# import pandas as pd
from data_process import DataProcessor

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

from ev_opt import EV_Opt  # noqa: E402

time = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_dir = "../output/ev_opt_run_" + time + "/"
k = 4
ex_factor = 0
disparity_index_list = ["relative_mean_abs_dev"]
max_add_capacity_list = list(range(0, 2000, 1000))

if not os.path.exists(output_dir):
    os.makedirs(output_dir)


data_processor = DataProcessor()
# set demographic partition based on quantiles
kwargs = {
    "income_bins": k,
    "mud_bins": k,
    "employment_bins": k,
}
# three dfs respectively: demographic data, commute matrix, and vkt flow matrix
df1, df2, df3 = data_processor.process_demo_data(**kwargs)

# set crs to 3857 (from spherical to flat)
df1.crs = "EPSG:4326"
df1 = df1.to_crs("EPSG:3857")


equity_indicator_list = [
    "char_capacity_per_capita",
    "char_capacity_per_car",
    "char_capacity_per_VKT_out",
]
demographic_group_list = [
    "income_level",
    "mud_level",
    "employment_level",
    "major_ethnicity",
]


multi_obj_setting = np.linspace(0, 10, 11) / 10


config = {
    "k_value": k,
    "equity_indicator_list": equity_indicator_list,
    "demographic_group_list": demographic_group_list,
    "disparity_index_list": disparity_index_list,
    "max_add_capacity_list": max_add_capacity_list,
    "multi_obj_setting": multi_obj_setting.tolist(),
}


with open(output_dir + "/kwargs_lst.json", "w") as f:
    json.dump(config, f)

"""
# Using DataFrame to store results takes up a lot of memory but is more readable.
# Do not use when running batch jobs with large datasets.
df_result_val = pd.DataFrame(
    columns=[
        "equity_indicator",
        "demographic_group",
        "disparity_index",
        "max_add_capacity",
        "weight_within",  # intra
        "weight_between",  # inter
        "charger_capacity_wp",
        "equivalent_char_capacity",
        "equity_xi",
        "objective_value",
        "obj_sol_within",
        "obj_sol_between",
    ]
)
"""

Optimizer = EV_Opt(df1, df2, df3, output_dir, ex_factor)
kwargs = {}

for equity_indicator in equity_indicator_list:
    for demographic_group in demographic_group_list:
        for disparity_index in disparity_index_list:
            for max_add_capacity in max_add_capacity_list:
                for multi_obj_bet_weight in multi_obj_setting:
                    kwargs["multi_obj_bet_weight"] = multi_obj_bet_weight
                    kwargs["max_add_capacity"] = max_add_capacity
                    m, sol0, sol1 = Optimizer.optimization(
                        equity_indicator, demographic_group, disparity_index, **kwargs
                    )
                    # df_result_val.loc[len(df_result_val)] = [
                    #     equity_indicator,
                    #     demographic_group,
                    #     disparity_index,
                    #     max_add_capacity,
                    #     1 - multi_obj_bet_weight,
                    #     multi_obj_bet_weight,
                    #     sol1["charger_capacity_wp"],
                    #     sol1["equivalent_char_capacity"],
                    #     sol1["equity_xi"],
                    #     sol1["objective_value"],
                    #     sol0["obj_val_within"],
                    #     sol0["obj_val_between"],
                    # ]
                    np.savez(
                        output_dir
                        + "result_val_{}_{}_{}_{}_{}_{}.npz".format(
                            equity_indicator,
                            demographic_group,
                            disparity_index,
                            max_add_capacity,
                            multi_obj_bet_weight,
                            ex_factor,
                        ),
                        sol1["charger_capacity_wp"],
                        sol1["equivalent_char_capacity"],
                        sol1["equity_xi"],
                        sol1["objective_value"],
                        sol0["obj_val_within"],
                        sol0["obj_val_between"],
                    )


# df_result_val.to_csv(output_dir + "df_result_val.csv", index=False)
