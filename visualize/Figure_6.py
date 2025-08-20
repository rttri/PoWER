"""
Author: Ruiting Wang
Date: August 2024

This file is used to visualize the optimization results of the EV charger designing problem.

There are four key elements in the visualization:

1. The base map is the choropleth map of the region, with the color representing the base feature.

2. The number of chargers installed in each tract is represented by the size of the markers on the map. (flag_char)

3. The equity indicator after the installation of the chargers is represented by the size of the markers on the map. (flag_eq)

4. The edges represent the commuting flows between tracts. The width of the edges represents the number of people commuting between tracts. (flag_edge)

On the basemap, the three other elements (2-4) can be plotted or muted by setting the flags.
"""

# %%
import json  # noqa: F401
import os
import sys

import matplotlib
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))


from opt.data_process import DataProcessor  # noqa: E402

if not os.path.exists("images"):
    os.mkdir("images")

# read the configuration file of the set of parameters
output_dir = "../output/ev_opt_run_1-4000kW/"
k = 4
# set font arial
matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = "Arial"

# read config

with open(output_dir + "kwargs_lst.json") as f:
    config = json.load(f)

k = config["k_value"]
equity_indicator_list = config["equity_indicator_list"]
demographic_group_list = config["demographic_group_list"]
disparity_index_list = config["disparity_index_list"]
max_add_capacity_list = config["max_add_capacity_list"]
multi_obj_setting = config["multi_obj_setting"]

# read results
npzfile = np.load(output_dir + "result_val.npz")
charger_capacity_wp = npzfile["arr_0"]
equivalent_char_capacity = npzfile["arr_1"]
equity_indicator_xi = npzfile["arr_2"]
objective_value = npzfile["arr_3"]
obj_sol_within = npzfile["arr_4"]
obj_sol_between = npzfile["arr_5"]

# read map data
data_processor = DataProcessor()
# set demographic partition based on quantiles
kwargs = {
    "income_bins": k,
    "mud_bins": k,
    "employment_bins": k,
}
# three dfs respectively: demographic data, commute matrix, and VKT flow matrix
df1, df2, df3 = data_processor.process_demo_data(**kwargs)

# set crs to 3857 (from spherical to flat)
df1.crs = "EPSG:4326"

# %%
equity_indicator = "char_capacity_per_capita"
n0 = len(equity_indicator_list)
demographic_group = "income_level"
n1 = len(demographic_group_list)
disparity_index = "relative_mean_abs_dev"
n2 = len(disparity_index_list)
max_add_capacity = 1000
n3 = len(max_add_capacity_list)
multi_obj = 0.5
n4 = len(multi_obj_setting)

count_n = (
    equity_indicator_list.index(equity_indicator) * n1 * n2 * n3 * n4
    + demographic_group_list.index(demographic_group) * n2 * n3 * n4
    + disparity_index_list.index(disparity_index) * n3 * n4
    + max_add_capacity_list.index(max_add_capacity) * n4
    + np.where(multi_obj_setting == multi_obj)[0][0]
)
# print(demographic_group_list.index(demographic_group) , disparity_index_list.index(disparity_index), max_per_ct_max_total.index([max_per_ct, max_total]), n1, n2, n3, count_n)

charger_capacity_wp_val = charger_capacity_wp[count_n]
equity_indicator_xi_val = equity_indicator_xi[count_n]
obj = objective_value[count_n]


# %%
def plot_map(
    df1,
    df2,
    arrow_feature,
    equity_indicator_xi_val,
    charger_capacity_wp_val,
    marker_feature,
    base_feature,
    title,
    filename,
    flag_eq=True,
    flag_edge=True,
    flag_char=True,
    color="blue",
):
    """
    Plot the map of the region.

    Parameters
    ----------
    df1 : DataFrame
        The DataFrame containing the base feature of each tract.
    df2 : DataFrame
        The DataFrame containing the commuting pattern between tracts.
    arrow_feature : str
        The feature to be represented by the arrows. "inflow" or "outflow".
    equity_indicator_xi_val : float
        The equity indicator value.
    charger_capacity_wp_val : int
        The number of chargers to be installed.
    marker_feature : str
        The feature to be represented by the markers. Such as "added_charger_power_wp", "eq_added_charger_power_wp".
    base_feature : str
        The base feature to be plotted. Should be a column in df1. Such as "income", "MUD", etc.
    title : str
        The title of the plot.
    filename : str
        The filename of the plot.
    flag_eq : bool, optional
        Whether to plot the "eq_added_charger_power_wp". The default is True.
    flag_edge : bool, optional
        Whether to plot the edges. The default is True.
    flag_char : bool, optional
        Whether to plot the "added_charger_power_wp". The default is True.

    Returns
    -------
    None (all plots are saved as images, html files, and vector files in output_dir folder).

    """
    df1["added_charger_power_wp"] = charger_capacity_wp_val
    df1["equity_indicator_after"] = equity_indicator_xi_val

    df1["Charger power<br>(existing)"] = df1["char_capacity_not_home"] + df1["char_capacity_home"]
    df1["Charger power<br>(after installation)"] = (
        df1["char_capacity_not_home"] + df1["char_capacity_home"] + df1["added_charger_power_wp"]
    )

    # the equivalent accessible charger power increase
    if equity_indicator == "char_capacity_per_capita":
        df1["char_power_after_eq"] = df1["equity_indicator_after"] * df1["popu"]
    elif equity_indicator == "char_capacity_per_car":
        df1["char_power_after_eq"] = df1["equity_indicator_after"] * df1["veh_num"]
    elif equity_indicator == "char_capacity_per_VKT_out":
        df1["char_power_after_eq"] = df1["equity_indicator_after"] * df1["VMT_flow_out_km"]
    else:
        raise ValueError("Invalid equity indicator")

    df1["eq_added_charger_power_wp"] = df1["char_power_after_eq"] - df1["Charger power<br>(existing)"]

    fig = px.choropleth_mapbox(
        df1,
        geojson=df1.geometry,
        locations=df1.index,
        color=df1[base_feature],
        color_continuous_scale="temps",
        range_color=(df1[base_feature].min(), df1[base_feature].max()),
        zoom=10,
        opacity=0.5,
        labels="Total Power of Chargers Before",
    )
    if flag_edge:
        if arrow_feature == "inflow":
            origin_nodes = ""
            destination_nodes = df1[df1.added_charger_power_wp > 0].tract_id.values
            for i in range(len(destination_nodes)):
                add_edge(
                    df1, df2, fig, origin_nodes, destination_nodes[i], base_feature, arrow_feature, title, filename
                )
        else:
            raise ValueError("Not implemented")
    if flag_char:
        add_nodes(
            df1,
            fig,
            "added_charger_power_wp",
            color="blue",
        )

    df1 = df1.sort_values(by=marker_feature)
    flag0 = 0
    flag1 = 0
    flag2 = 0
    # print(df[df[goal].round() > 0][goal].min(), df[df[goal].round() > 0][goal].median())

    # only show legend for min, max, median of the non-zero values
    for i, row in df1.iterrows():
        # print(round(row[goal]), round(df[df[goal].round() > 0][goal].median()))

        if round(row[marker_feature]) > 0:
            if (
                round(row[marker_feature]) == round(df1[df1[marker_feature].round() > 0][marker_feature].min())
                and flag0 == 0
            ):
                fig.add_trace(
                    go.Scattermapbox(
                        mode="markers",
                        lon=[row["geometry"].centroid.x],
                        lat=[row["geometry"].centroid.y],
                        marker=go.scattermapbox.Marker(
                            size=np.log2((row[marker_feature])) + 1,
                            color=color,
                        ),
                        showlegend=True,
                        name="Charger total power (kW) " + str(round(row[marker_feature])),
                    )
                )
                flag0 = 1
            elif round(row[marker_feature]) == round(df1[marker_feature].max()) and flag1 == 0:
                fig.add_trace(
                    go.Scattermapbox(
                        mode="markers",
                        lon=[row["geometry"].centroid.x],
                        lat=[row["geometry"].centroid.y],
                        marker=go.scattermapbox.Marker(
                            size=np.log2((row[marker_feature])) + 1,
                            color=color,
                        ),
                        showlegend=True,
                        name="Charger total power (kW) " + str(round(row[marker_feature])),
                    ),
                )
                flag1 = 1

            elif (
                round(row[marker_feature]) >= round(df1[df1[marker_feature].round() > 0][marker_feature].median())
            ) and flag2 == 0:
                fig.add_trace(
                    go.Scattermapbox(
                        mode="markers",
                        lon=[row["geometry"].centroid.x],
                        lat=[row["geometry"].centroid.y],
                        marker=go.scattermapbox.Marker(
                            size=np.log2((row[marker_feature])) + 1,
                            color=color,
                        ),
                        showlegend=True,
                        name="Charger total power (kW) " + str(round(row[marker_feature])),
                    )
                )
                flag2 = 1
            else:
                fig.add_trace(
                    go.Scattermapbox(
                        mode="markers",
                        lon=[row["geometry"].centroid.x],
                        lat=[row["geometry"].centroid.y],
                        marker=go.scattermapbox.Marker(
                            size=np.log2((row[marker_feature])) + 1,
                            # cmin=np.log2(df[goal].min()),
                            # cmax=np.log2(df[goal].max()),
                            color=color,
                        ),
                        showlegend=False,
                    ),
                )
    if flag_eq:
        add_nodes(
            df1,
            fig,
            "eq_added_charger_power_wp",
            color="red",
        )

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lon=-122.23, lat=37.8),
            zoom=10.7,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            title=title,
            bgcolor="LightSteelBlue",
        ),
    )
    fig.update_layout(legend={"itemsizing": "trace"})

    # color the map based on original numner of chargers

    fig.show()
    fig.write_image(output_dir + "/" + filename + ".pdf")
    fig.write_image(output_dir + "/" + filename + ".png", scale=2)
    fig.write_html(output_dir + "/" + filename + ".html")


def add_edge(df1, df2, fig, origin, destination, base_feature, arrow_feature, title, filename):
    df1 = df1.set_index("tract_id")
    if arrow_feature == "inflow":
        dest_ct = destination
        df2_temp = df2.loc[:, dest_ct]
        for i in range(len(df2)):
            ori_ct = df2_temp.index[i]
            if df2_temp.iloc[i] > 0:
                fig.add_trace(
                    go.Scattermapbox(
                        mode="lines+markers",
                        marker=dict(size=3),
                        lon=[df1.loc[ori_ct].geometry.centroid.x, df1.loc[dest_ct].geometry.centroid.x],
                        lat=[df1.loc[ori_ct].geometry.centroid.y, df1.loc[dest_ct].geometry.centroid.y],
                        line=dict(width=df2_temp.iloc[i] / 5, color="darkblue"),
                        opacity=0.5,
                        showlegend=False,
                    )
                )

    elif arrow_feature == "outflow":
        ori_ct = origin
        df2_temp = df2.loc[ori_ct, :]
        for i in range(len(df2)):
            dest_ct = df2_temp.index[i]
            if df2_temp.iloc[i] > 0:
                fig.add_trace(
                    go.Scattermapbox(
                        mode="lines+markers",
                        marker=dict(size=3),
                        lon=[df1.loc[ori_ct].geometry.centroid.x, df1.loc[dest_ct].geometry.centroid.x],
                        lat=[df1.loc[ori_ct].geometry.centroid.y, df1.loc[dest_ct].geometry.centroid.y],
                        line=dict(width=df2_temp.iloc[i] / 15, color="darkblue"),
                        opacity=0.5,
                        showlegend=False,
                    )
                )


def add_nodes(
    df1,
    fig,
    marker_feature,
    color="red",
):
    """
    Method to add nodes to the map. The size of the nodes is determined by the marker_feature. The color of the nodes is determined by the color parameter.

    """
    for i, row in df1.iterrows():
        # print(round(row[goal]), round(df[df[goal].round() > 0][goal].median()))

        if round(row[marker_feature]) > 0:
            fig.add_trace(
                go.Scattermapbox(
                    mode="markers",
                    lon=[row["geometry"].centroid.x],
                    lat=[row["geometry"].centroid.y],
                    marker=go.scattermapbox.Marker(
                        size=np.log2((row[marker_feature])) + 1,
                        # cmin=np.log2(df[goal].min()),
                        # cmax=np.log2(df[goal].max()),
                        color=color,
                    ),
                    showlegend=False,
                ),
            )

    pass


# %%
arrow_feature = "inflow"
df1.rename(columns={"income": "Income"}, inplace=True)

# plotting the actual geographical location of the chargers
plot_map(
    df1,
    df2,
    arrow_feature,
    equity_indicator_xi_val,
    charger_capacity_wp_val,
    "added_charger_power_wp",
    "Income",
    title="Installed workplace charger<br>capacity (kW, log-scale)",
    filename="fig_char_1000_income_rmad",
    flag_char=True,
    flag_eq=False,
    flag_edge=False,
    color="blue",
)

# plotting the equivalent accessible charger capacity increase (and the commuting flows)
plot_map(
    df1,
    df2,
    arrow_feature,
    equity_indicator_xi_val,
    charger_capacity_wp_val,
    "eq_added_charger_power_wp",
    "Income",
    title="Equivalent accessible charger<br>capacity increase (kW, log-scale)",
    filename="fig_eq_1000_income_rmad",
    flag_char=True,
    flag_eq=True,
    flag_edge=True,
    color="red",
)

# %%
