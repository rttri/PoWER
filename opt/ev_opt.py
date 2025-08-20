"""

Author: Ruiting Wang
Date: August 2024

This script contains the key functions for the EV charger planning optimization model.

"""

import gurobipy as gp
import numpy as np
from gurobipy import GRB


def softtime(model, where):
    """
    Set soft stopping criterion for the optimization model using callbacks.
    Stop the model if:
    1. The runtime exceeds the softlimit
    2. The optimality gap is less than the softgap

    (Note: this is for quick testing of data.)
    """
    softlimit = 20
    softgap = 0.05

    if where == GRB.Callback.MIP:
        runtime = model.cbGet(GRB.Callback.RUNTIME)
        if runtime > 10:
            objbst = model.cbGet(GRB.Callback.MIP_OBJBST)
            objbnd = model.cbGet(GRB.Callback.MIP_OBJBND)
            if objbst == 0:
                gap = 0
            else:
                gap = abs(objbst - objbnd) / objbst

            if runtime > softlimit and gap < softgap:
                model.terminate()


class EV_Opt:
    """
    EV_Opt class contains the key functions for the EV charger planning optimization model.

    Attributes
    ----------
    census_tract : list
        List of census tracts
    output_dir : str
        Output directory for the optimization model

    """

    def __init__(self, df_data, df_commute_data, df_vmt_data, output_dir, exclusivity_factor):
        self.df1 = df_data
        self.df2 = df_commute_data
        self.df3 = df_vmt_data
        self.exclusivity_factor = exclusivity_factor
        self.char_num_home = self.df1["char_num_home"]
        self.char_num_not_home = self.df1["char_num_not_home"]
        self.char_capacity_home = self.df1["char_capacity_home"]
        self.char_capacity_not_home = self.df1["char_capacity_not_home"]
        self.work_popu = self.df1["work_popu_LODES"]
        # we use work_popu_LODES to compute the ratio of worker flows
        self.n_trip_ij = self.df2.values
        self.d_trip_ij = self.df3.values
        self.popu_ct = self.df1["popu"]
        self.num_of_veh_ct = self.df1["veh_num"]

        self.census_tract = self.df1.tract_id.values
        self.n_ct = len(self.df2)
        self.output_dir = output_dir

        self.df1["car_ownership_rate"] = self.df1["veh_num"] / self.df1["popu"]
        self.df1["total_char_num"] = self.df1["char_num_not_home"] + self.df1["char_num_home"]
        self.df1["total_char_capacity"] = self.df1["char_capacity_not_home"] + self.df1["char_capacity_home"]
        self.df1["VKT_flow_out_km"] = self.df3.sum(axis=1).values

    def optimization(self, equity_indicator, demographic_group, disparity_index, grb_mute=True, **kwargs):
        """
        Optimization function for the EV charger planning model.

        Parameters
        ----------
        (Three key inputs for evaluation of equity.)
        equity_indicator : str
            Equity indicator for the optimization model
        demographic_group : str
            Demographic group for the optimization model
        disparity_index : str
            Disparity index for the optimization model

        #####################
        stopped here: check how to document kwargs.

        """
        max_add_capacity = kwargs["max_add_capacity"]

        m = gp.Model("charger_planning")
        if grb_mute:
            m.params.OutputFlag = 0
            m.params.LogToConsole = 0

        x = m.addVars(self.n_ct, vtype=GRB.CONTINUOUS, name="charger_capacity_wp")
        char_eq = m.addVars(self.n_ct, lb=0, vtype=GRB.CONTINUOUS, name="equvalent_char_capacity")
        xi = m.addVars(self.n_ct, lb=0, vtype=GRB.CONTINUOUS, name="equity_indicator")

        # Constraints - charger capacity limit
        m.addConstrs((x[i] <= max_add_capacity for i in range(self.n_ct)), name="char_cap_l1")
        m.addConstr((gp.quicksum(x[i] for i in range(self.n_ct)) <= max_add_capacity), name="char_cap_l2")

        # Constraints - equivalent charger capacity in each census tract
        m.addConstrs(
            (
                char_eq[i]
                == self.df1["total_char_capacity"][i]
                + gp.quicksum(x[j] * self.n_trip_ij[i, j] / self.work_popu[j] for j in range(self.n_ct))
                * (1 - self.exclusivity_factor)
                for i in range(self.n_ct)
            ),
            name="char_capacity_each_ct",
        )

        # compute equity indicator xi, add related constraints
        self.compute_xi_val(m, char_eq, xi, equity_indicator, **kwargs)

        # compute equity indicator value in each group
        val = self.compute_group_val(m, char_eq, equity_indicator, demographic_group, **kwargs)

        self.get_equity_objective(m, xi, val, disparity_index, demographic_group, **kwargs)

        sol0, sol1 = self.solve(m, equity_indicator, demographic_group, disparity_index, grb_mute=grb_mute, **kwargs)

        return m, sol0, sol1

    def compute_xi_val(self, m, char_eq, xi, equity_indicator, **kwargs):
        # TODO: change name of variables
        if equity_indicator == "char_capacity_per_capita":
            m.addConstrs(
                (xi[i] == char_eq[i] / self.popu_ct[i] for i in range(self.n_ct)),
                name="char_capacity_per_capita_each_ct",
            )

        elif equity_indicator == "char_capacity_per_car":
            m.addConstrs(
                (xi[i] == char_eq[i] / self.num_of_veh_ct[i] for i in range(self.n_ct)),
                name="char_capacity_per_car_each_ct",
            )

        elif equity_indicator == "char_capacity_per_VKT_out":
            m.addConstrs(
                (xi[i] == char_eq[i] / self.df1["VKT_flow_out_km"][i] for i in range(self.n_ct)),
                name="char_capacity_per_VKT_out_each_ct",
            )

        else:
            raise ValueError("Invalid equity indicator")

    def compute_group_val(self, m, char_eq, equity_indicator, demographic_group, **kwargs):

        if demographic_group not in ["income_level", "mud_level", "employment_level", "major_ethnicity"]:
            raise ValueError("Invalid demongraphic group")
        else:
            demo_category_list = []
            for item in self.df1[demographic_group].unique():
                demo_category_list.append(self.df1[self.df1[demographic_group] == item].index)
            n_group = len(demo_category_list)
            val_group = demo_category_list

        val = m.addVars(n_group, vtype=GRB.CONTINUOUS, name="indicator_group_value")

        if equity_indicator == "char_capacity_per_capita":
            # compute the total population in each group (e.g. low income group)
            popu_group = np.array([sum(self.popu_ct[val_group[i]]) for i in range(n_group)])

            # compute the equity indicator for each group as a whole
            m.addConstrs(
                (val[i] == gp.quicksum(char_eq[j] for j in val_group[i]) / popu_group[i] for i in range(n_group)),
                name="demographic_group_value",
            )

        elif equity_indicator == "char_capacity_per_car":
            num_veh_group = np.array([sum(self.num_of_veh_ct[val_group[i]]) for i in range(n_group)])

            m.addConstrs(
                (val[i] == gp.quicksum(char_eq[j] for j in val_group[i]) / num_veh_group[i] for i in range(n_group)),
                name="demographic_group_value",
            )

        elif equity_indicator == "char_capacity_per_VKT_out":
            VKT_group = np.array([sum(self.df1["VKT_flow_out_km"][val_group[i]]) for i in range(n_group)])

            m.addConstrs(
                (val[i] == gp.quicksum(char_eq[j] for j in val_group[i]) / VKT_group[i] for i in range(n_group)),
                name="demographic_group_value",
            )

        else:
            raise ValueError("Invalid equity indicator")

        return val

    def get_equity_objective(self, m, xi, val, disparity_index, demographic_group, **kwargs):
        obj_between = m.addVar(vtype=GRB.CONTINUOUS, name="obj_val_between")
        obj_within = m.addVar(vtype=GRB.CONTINUOUS, name="obj_val_within")

        m, obj_val_between = self.disparity_fn(m, val, disparity_index, **kwargs)
        m.addConstr(obj_between == obj_val_between)

        m, obj_val_within = self.get_within_disparity_objective(m, xi, demographic_group, disparity_index, **kwargs)
        m.addConstr(obj_within == obj_val_within)

        multi_obj_bet_weight = kwargs["multi_obj_bet_weight"]

        assert isinstance(multi_obj_bet_weight, float)
        assert 0 <= multi_obj_bet_weight <= 1

        tot_weighted_obj = obj_val_between * multi_obj_bet_weight + obj_val_within * (1 - multi_obj_bet_weight)

        m.setObjective(tot_weighted_obj)
        return m

    def get_within_disparity_objective(self, m, xi, demographic_group, disparity_index, **kwargs):

        if demographic_group not in ["income_level", "mud_level", "employment_level", "major_ethnicity"]:
            raise ValueError("Invalid demongraphic group")
        else:
            demo_category_list = []
            for item in self.df1[demographic_group].unique():
                demo_category_list.append(self.df1[self.df1[demographic_group] == item].index)
            n_group = len(demo_category_list)
            val_group = demo_category_list

        within_group = m.addVars(n_group, vtype=GRB.CONTINUOUS, name="within_group_disparity")

        for k in range(n_group):
            subset_xi = [xi[i] for i in list(val_group[k].values)]
            m, obj_val_within_one_group = self.disparity_fn(m, subset_xi, disparity_index, **kwargs)
            m.addConstr(within_group[k] == obj_val_within_one_group)

        obj_val_within = gp.quicksum(within_group[k] for k in range(n_group)) / n_group

        return m, obj_val_within

    def disparity_fn(self, m, val, disparity_index, **kwargs):
        if disparity_index == "var":
            m, obj_val = self.variance(m, val, **kwargs)
        elif disparity_index == "coeff_of_var":
            m, obj_val = self.coeff_of_var(m, val, **kwargs)
        elif disparity_index == "mean_abs_dev":
            m, obj_val = self.mean_abs_dev(m, val, **kwargs)
        elif disparity_index == "relative_mean_abs_dev":
            m, obj_val = self.relative_mean_abs_dev(m, val, **kwargs)
        elif disparity_index == "gini_coefficient":
            m, obj_val = self.gini_equity_index(m, val, **kwargs)
        else:
            raise ValueError("Invalid method")

        return m, obj_val

    def variance(self, m, val, **kwargs):
        obj_val = gp.quicksum(
            (val[i] - gp.quicksum(val[j] for j in range(len(val))) / len(val)) ** 2 for i in range(len(val))
        ) / len(val)

        return m, obj_val

    def coeff_of_var(self, m, val, **kwargs):
        aux1 = m.addVar(vtype=GRB.CONTINUOUS, name="aux1")  # 1 / mean
        aux2 = m.addVar(vtype=GRB.CONTINUOUS, name="aux2")  # variance
        aux3 = m.addVar(vtype=GRB.CONTINUOUS, name="aux3")  # sqrt(variance), or std

        m.addConstr(aux1 * (gp.quicksum(val[j] for j in range(len(val))) / len(val)) == 1, name="auxiliary_1")
        m.addConstr(
            aux2
            == gp.quicksum(
                (val[i] - gp.quicksum(val[j] for j in range(len(val))) / len(val)) ** 2 for i in range(len(val))
            )
            / len(val),
            name="auxiliary_2",
        )

        m.addGenConstrPow(aux2, aux3, 0.5, "auxiliary_3")

        obj_val = aux3 * aux1
        m.params.NonConvex = 2

        return m, obj_val

    def mean_abs_dev(self, m, val, **kwargs):
        aux = m.addVars(len(val), vtype=GRB.CONTINUOUS, name="auxiliary")
        m.addConstrs(
            (aux[i] >= val[i] - gp.quicksum(val[j] for j in range(len(val))) / len(val) for i in range(len(val))),
            name="auxiliary_positive",
        )
        m.addConstrs(
            (aux[i] >= gp.quicksum(val[j] for j in range(len(val))) / len(val) - val[i] for i in range(len(val))),
            name="auxiliary_negative",
        )

        obj_val = gp.quicksum(aux[i] for i in range(len(val))) / len(val)

        return m, obj_val

    def gini_equity_index(self, m, val, **kwargs):
        aux1 = m.addVars(len(val), len(val), vtype=GRB.CONTINUOUS, name="aux1")
        aux2 = m.addVar(vtype=GRB.CONTINUOUS, name="aux2_1_over_sum")

        m.addConstr(
            aux2 * gp.quicksum(val[j] for j in range(len(val))) == 1,
            name="auxiliary_2_over_sum",
        )
        m.addConstrs(
            (aux1[i, j] >= val[i] - val[j] for i in range(len(val)) for j in range(len(val))), name="auxiliary_positive"
        )
        m.addConstrs(
            (aux1[i, j] >= val[j] - val[i] for i in range(len(val)) for j in range(len(val))), name="auxiliary_negative"
        )
        obj_val = gp.quicksum(aux1[i, j] for i in range(len(val)) for j in range(len(val))) / (2 * len(val)) * aux2

        m.params.NonConvex = 2
        return m, obj_val

    def relative_mean_abs_dev(self, m, val, **kwargs):
        aux = m.addVars(len(val), vtype=GRB.CONTINUOUS, name="aux1_abs")
        aux2 = m.addVar(vtype=GRB.CONTINUOUS, name="aux2_mean")
        aux_disparity = m.addVar(vtype=GRB.CONTINUOUS)

        m.addConstrs(
            (aux[i] >= val[i] - gp.quicksum(val[j] for j in range(len(val))) / len(val) for i in range(len(val))),
            name="auxiliary_positive",
        )
        m.addConstrs(
            (aux[i] >= gp.quicksum(val[j] for j in range(len(val))) / len(val) - val[i] for i in range(len(val))),
            name="auxiliary_negative",
        )

        m.addConstr(aux2 == gp.quicksum(val[j] for j in range(len(val))) / len(val), name="auxiliary_mean")

        # Add constraint to represent the objective value
        m.addConstr(
            aux_disparity * aux2 == gp.quicksum(aux[i] for i in range(len(val))) / len(val), name="objective_constraint"
        )

        obj_val = aux_disparity
        m.params.NonConvex = 2

        return m, obj_val

    def solve(self, m, equity_indicator, demographic_group, disparity_index, grb_mute=True, sol_mute=True, **kwargs):

        if grb_mute:
            pass

        else:
            m.params.LogFile = "%s/char_plan_%s_%s_%s_%d.log" % (
                self.output_dir,
                disparity_index,
                equity_indicator,
                demographic_group,
                kwargs["max_add_capacity"],
            )

        m.params.TimeLimit = 600
        m.params.MIPGap = 0.005
        m.optimize(softtime)

        # print("Optimization status: ", m.status)

        if m.status == GRB.INFEASIBLE:
            # compute IIS
            m.computeIIS()
            m.write("model_2025.ilp")
            return None

        # get the set of variables
        x = m.getVars()
        # solution = {}
        # get sol by their name not by position
        solution0 = {var.varName: var.X for var in x}
        solution1 = {}

        solution1["objective_value"] = m.objVal

        solution1["charger_capacity_wp"] = [x[i].x for i in range(self.n_ct)]
        solution1["equivalent_char_capacity"] = [x[i + self.n_ct].x for i in range(self.n_ct)]
        solution1["equity_xi"] = [x[i + 2 * self.n_ct].x for i in range(self.n_ct)]

        if sol_mute:
            pass
        else:
            m.write(
                "%s/char_plan_%s_%s_%s_%d_%d.sol"
                % (
                    self.output_dir,
                    disparity_index,
                    equity_indicator,
                    demographic_group,
                    kwargs["max_add_capacity"],
                    kwargs["multi_obj_bet_weight"],
                )
            )
        return solution0, solution1
