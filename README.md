# POWER - Planning Of Workplace Equitable Recharge

## What's this?

This repository contains the code and data for the paper  

**Title: Leveraging Commuting Patterns and Workplace Charging to Advance Equitable EV Charger Access**

***Authors: Ruiting Wang, Ha-Kyung Kwon, Katherine H. Jordan, Scott J. Moura, Madhur Boloor, Michael L. Machala***

The study introduces a framework to improve accessibility and quantify social equity priorities in electric vehicle charging infrastructure through strategic workplace charger placement.

The research develops a customizable equity evaluation model to quantify access disparities across demographic groups. This model is integrated into an optimization framework to guide charging infrastructure deployment decisions. Using commuting patterns, the case study of Oakland, California demonstrates that strategically placing workplace chargers can achieve, on average, a 1.8-fold reduction in relative mean absolute deviation compared to benchmark scenarios. The analysis highlights that targeted workplace charger deployment in high-commuter zones can significantly enhance citywide equity.

This framework equips policymakers with quantifiable metrics to evaluate trade-offs between potentially conflicting equity considerations, such as income and accessibility.

## Contents

1. [Highlights](#highlights)
2. [Datasets](#datasets)
3. [Setup](#setup)
4. [License](#license)

## Highlights

- New framework highlights the equity trade-offs of charger placement.
- Model optimizes equitable charger placement using workplace commuting patterns.
- Workplace charging can improve infrastructure equity under budget limitations.


## Datasets

This project utilizes various datasets to analyze commuting patterns and workplace charging for equitable EV charger access. Below is an overview of the datasets:

| Name                          | Description                                                                 | Coverage       | Resolution          | Source                              |
|-------------------------------|-----------------------------------------------------------------------------|----------------|---------------------|-------------------------------------|
| Demographic Data              | Includes income, population, employment rate, multi-unit dwelling rate, ethnicity, vehicle number, etc. | Nationwide     | Census Blocks       | [Census Bureau](https://www.census.gov/) |
| Residential Charger Data      | Provides data on residential EV charger installations.                     | California      | By demographics      | [Home Charging Access in California (Local Surveys)](https://www.energy.ca.gov/publications/2022/home-charging-access-california) |
| Commuting Patterns            | Tracks daily travel behavior and workplace locations.                      | Nationwide     | Census tract         | [LEHD Origin-Destination Employment Statistics](https://lehd.ces.census.gov/data/) |
| EV Charger Locations          | Provides existing EV charger locations and capacities.                     | Nationwide     | Latitude/Longitude   | [Alternative Fuels Data Center](https://afdc.energy.gov/stations/) |

These datasets are combined to perform equity analysis, optimization, and evaluation of EV charger access solutions.

## Setup

### Installation
Clone the repository:
   ```bash
   git clone https://github.com/ev-equity.git
   cd ev-equity
   ```

In order to install all the required dependencies, create a virtual environment using Conda and install the packages listed in the `.yml` file.

   ```bash
   conda env create -f environment.yml
   ```

### LODES Data

The `LODES` data files are not included in this repository due to their size. You can download the required files from the official source:

- [LODES Data Download Page](https://lehd.ces.census.gov/data/lodes/LODES8/ca/od/)

#### Required Files
Download the following files and place them in the `dataset/LODES/` directory:
- `ca_od_aux_JT00_2021.csv.gz`
- `ca_od_aux_JT01_2021.csv.gz`
- `ca_od_aux_JT02_2021.csv.gz`
- `ca_od_aux_JT03_2021.csv.gz`
- `ca_od_aux_JT04_2021.csv.gz`
- `ca_od_aux_JT05_2021.csv.gz`
- `ca_od_main_JT00_2021.csv.gz`
- `ca_od_main_JT01_2021.csv.gz`
- `ca_od_main_JT02_2021.csv.gz`
- `ca_od_main_JT03_2021.csv.gz`
- `ca_od_main_JT04_2021.csv.gz`
- `ca_od_main_JT05_2021.csv.gz`

#### Automating the Download
You can use the following Python script to automate the download process:

```python
import os
import requests

base_url = "https://lehd.ces.census.gov/data/lodes/LODES8/ca/od/"
files = [
    "ca_od_aux_JT00_2021.csv.gz",
    "ca_od_aux_JT01_2021.csv.gz",
    "ca_od_aux_JT02_2021.csv.gz",
    "ca_od_aux_JT03_2021.csv.gz",
    "ca_od_aux_JT04_2021.csv.gz",
    "ca_od_aux_JT05_2021.csv.gz",
    "ca_od_main_JT00_2021.csv.gz",
    "ca_od_main_JT01_2021.csv.gz",
    "ca_od_main_JT02_2021.csv.gz",
    "ca_od_main_JT03_2021.csv.gz",
    "ca_od_main_JT04_2021.csv.gz",
    "ca_od_main_JT05_2021.csv.gz",
]

output_dir = "dataset/LODES"
os.makedirs(output_dir, exist_ok=True)

for file in files:
    url = base_url + file
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(output_dir, file), "wb") as f:
            f.write(response.content)
        print(f"Downloaded {file}")
    else:
        print(f"Failed to download {file}: {response.status_code}")

```

### Shape File Data

Download a shapefile that covers a region larger than Oakland, such as Alameda County. You can find the shapefile at the following link: [Alameda County Shapefile](https://data.acgov.org/datasets/7b064a13a9234bfba97654007ccbf8e8/explore?location=37.679577%2C-121.906442%2C10.26).

### Repository Structure

```plaintext
├── dataset/
│   ├── alt_fuel_stations_all_vehtypes.csv               # Raw input EV charging station data from AFDC
│   ├── alt_fuel_stations_all_types_processed.csv        # Processed EV charging station data from AFDC
│   ├── demographic_data_with_residential_charger.csv    # Processed demographic data with residential charger information
│   ├── census_tract_shapefile.shp                       # Shapefile with geographic boundaries larger than Oakland
│   ├── LODES/                                           # Folder containing LEHD Origin-Destination Employment Statistics (LODES) data

├── demographics/                                        # Folder for demographic analysis and visualization
│   ├── demo_visualize_Figure1-3.ipynb                   # Jupyter Notebook for visualizing demographic data (Figures 1-3)
│   ├── plot_demo_groups.py                              # Python script for plotting demographic groups

├── helpers/                                             # Folder for helper scripts
│   ├── data_processing/
│   │   ├── charger_type_process.py                      # Script for processing EV charging station and charger type data
│   │   ├── demo_with_residential_charger.py             # Script for estimating residential chargers from demographic data
│   ├── od_process/                                      # Scripts for origin-destination (OD) data processing
│   │   ├── distance_matrix.py                           # Script for calculating distance matrices
│   │   ├── read_lodes_od.ipynb                          # Jupyter Notebook for reading and processing LODES OD data
│   │   ├── d_ij_census_tract_LODES_data.csv             # Distance matrix data for Census Tracts from LODES
│   │   ├── n_ij_census_tract_LODES_data.csv             # OD flow data for Census Tracts from LODES

├── opt/                                                 # Folder for optimization scripts
│   ├── data_process.py                                  # Handles data preprocessing tasks to bring all datasets together
│   ├── ev_opt.py                                        # Implements optimization model
│   ├── ev_eval_w_eqchar.py                              # Evaluates multiple equity metrics given a charging plan
│   ├── ev_opt_run.py                                    # Runs optimization experiments

├── output/                                              # Folder where all results are stored

├── visualize/                                           # Stores visualizations and related notebooks
│   ├── Figure_4.ipynb                                   # Jupyter Notebook for generating Figure 4
│   ├── Figure_5_and_7.ipynb                             # Jupyter Notebook for generating Figures 5 and 7
│   ├── Figure_6.py                                      # Python script for generating Figure 6
│   ├── Figure_8.ipynb                                   # Jupyter Notebook for generating Figure 8

├── README.md                                            # Documentation for the repository
├── environment.yml                                      # Conda environment file with Python dependencies
├── .gitignore                                           # Specifies files and directories to be ignored by Git

```

## License

[![CC BY-NC-ND 4.0][cc-by-nc-nd-shield]][cc-by-nc-nd]

This work is licensed under a [Creative Commons Attribution-NonCommercial-NoDerivs 4.0 International License][cc-by-nc-nd].

[cc-by-nc-nd]: http://creativecommons.org/licenses/by-nc-nd/4.0/
[cc-by-nc-nd-shield]: https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey.svg
