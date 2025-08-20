"""

Author: Ruiting Wang
Date: August 2024

This module provides functions to plot demographic features on maps using geopandas and contextily.

"""

import contextily as ctx
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

# ref: https://medium.com/@jl_ruiz/plot-maps-from-the-us-census-bureau-using-geopandas-and-contextily-in-python-df787647ef77


def plot_color_feature_cont(df, feature, name, legend_name, cmap="coolwarm", dpi=100, normalize=True):
    f, ax = plt.subplots(1, 1, figsize=(10, 6), sharex=True, sharey=True)
    f.tight_layout(pad=0.8)
    ax.set_axis_off()
    plt.title(name, fontsize=14)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.2)
    ux = df.plot(feature, ax=ax, edgecolor="k", cmap=cmap, alpha=0.5, legend=True, cax=cax)
    ctx.add_basemap(ux, source=ctx.providers.OpenStreetMap.Mapnik)
    if normalize:
        norm = mcolors.Normalize(vmin=0, vmax=1)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        f.colorbar(sm, cax=cax)
    plt.ylabel(legend_name, fontsize=12)
    plt.savefig("%s.png" % name, dpi=dpi, bbox_inches="tight")
    return 0


def plot_color_feature_discrete(
    df, feature, name, legend_name, legend_labels, bin_list, cmap=mcolors.ListedColormap(["green", "red"]), dpi=100
):
    f, ax = plt.subplots(1, 1, figsize=(10, 6), sharex=True, sharey=True)
    f.tight_layout(pad=0.8)
    ax.set_axis_off()
    plt.title(name, fontsize=14)
    # divider = make_axes_locatable(ax)
    legend_elements = [mpatches.Patch(color=cmap(i), label=legend_labels[i]) for i in range(len(cmap.colors))]

    ux = df.plot(
        feature, ax=ax, edgecolor="k", cmap=cmap, alpha=0.5, legend=False, classification_kwds=dict(bins=bin_list)
    )
    ctx.add_basemap(ux, source=ctx.providers.OpenStreetMap.Mapnik)
    print(legend_elements)
    plt.legend(
        handles=legend_elements,
        labels=legend_labels,
        title=legend_name,
        loc="upper right",
        fontsize=12,
    )
    plt.ylabel(legend_name, fontsize=12)
    plt.savefig("%s .png" % name, dpi=dpi)
    return 0
