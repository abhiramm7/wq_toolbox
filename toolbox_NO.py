# -*- coding: utf-8 -*-
# @Author: Brooke Mason
# @Date:   2020-01-15 09:57:05
# @Last Modified by:   Brooke Mason
# @Last Modified time: 2020-06-11 22:21:36

# Import required modules
from pyswmm import Simulation, Nodes, Links
from wq_toolbox.nodes import Node_Quality
from scipy.integrate import ode 
import numpy as np
import matplotlib.pyplot as plt

# Nitrate 3 CSTRs in Series
def CSTR_tank(t, C, Qin, Cin, Qout, V, k):
    dCdt = (Qin*Cin - Qout*C)/V - k*C
    return dCdt

# DO Variables
k_DO = 0.000075 # rate/5 sec
Co_DO = 10.0    # mg/L

#----------------------------------------------------------------------#

# Uncontrolled Simulation
# Lists to store results
Ellsworth_inflow = []
Ellsworth_conc = []
Ellsworth_cuminload = []
Ellsworth_depth = []
Ellsworth_flooding = []
Ellsworth_outflow = []
Ellsworth_cumload = []

DBasin_inflow = []
DBasin_conc = []
DBasin_cuminload = []
DBasin_depth = []
DBasin_outflow = []
DBasin_cumload = []

Wetland_inflow = []
Wetland_conc = []
Wetland_cuminload = []
Wetland_depth = []
Wetland_flooding= []
Wetland_volume = []
Wetland_outflow = []
Wetland_cumload = []
Wetland_DO1 = []
Wetland_DO2 = []
Wetland_DO3 = []   
Wtlnd_bp_inflows = []

Channel_flow = []
Channel_conc = []
Channel_cuminload = []
Channel_depth = []
Channel_flooding = []
Channel_cumload = []

# Setup toolbox simulation
with Simulation("./modifiedMBDoyle_NO.inp") as sim:
    # Get asset information
    Ellsworth = Nodes(sim)["93-50408"]
    DBasin = Nodes(sim)["93-50404"]
    Wetland = Nodes(sim)["93-49759"]
    Wtlnd_bypass = Links(sim)["95-70294"]
    Channel = Links(sim)["95-70277"]
    
    # Setup dt calculation        
    start_time = sim.start_time
    last_timestep = start_time

    # Setup CSTR solver
    solver1 = ode(CSTR_tank)
    solver1.set_integrator("dopri5")
    solver2 = ode(CSTR_tank)
    solver2.set_integrator("dopri5")
    solver3 = ode(CSTR_tank)
    solver3.set_integrator("dopri5")

    # Tracking time for DO reaction
    t1 = 0
    t2 = 0
    t3 = 0

    # Step through the simulation    
    for index,step in enumerate(sim):

        # Calculate dt
        current_step = sim.current_time
        dt = (current_step - last_timestep).total_seconds()
        last_timestep = current_step

        # Get NO conc for each asset        
        Ell_p = Ellsworth.pollut_quality['NO']
        Ellsworth_conc.append(Ell_p)
        DB_p = DBasin.pollut_quality['NO']
        DBasin_conc.append(DB_p)
        Wt_p = Wetland.pollut_quality['NO']
        Wetland_conc.append(Wt_p)
        Ch_p = Channel.pollut_quality['NO']
        Channel_conc.append(Ch_p)

        # Get flow for  each asset
        Ell_if = Ellsworth.total_inflow
        Ellsworth_inflow.append(Ell_if)
        Ell_d = Ellsworth.depth
        Ellsworth_depth.append(Ell_d)
        Ell_fl = Ellsworth.flooding
        Ellsworth_flooding.append(Ell_fl)
        Ell_of = Ellsworth.total_outflow
        Ellsworth_outflow.append(Ell_of)
        DB_if = DBasin.total_inflow
        DBasin_inflow.append(DB_if)
        DB_d = DBasin.depth
        DBasin_depth.append(DB_d)
        DB_of = DBasin.total_outflow
        DBasin_outflow.append(DB_of)
        Wt_if = Wetland.total_inflow
        Wetland_inflow.append(Wt_if)
        Wt_d = Wetland.depth
        Wetland_depth.append(Wt_d)
        Wt_fl = Wetland.flooding
        Wetland_flooding.append(Wt_fl)
        Wt_v = Wetland.volume
        Wetland_volume.append(Wt_v)
        Wt_of = Wetland.total_outflow
        Wetland_outflow.append(DB_of)
        Wt_bp = Wtlnd_bypass.flow
        Wtlnd_bp_inflows.append(Wt_bp)
        Ch_f = Channel.flow
        Channel_flow.append(Ch_f)
        Ch_d = Channel.depth
        Channel_depth.append(Ch_d)

        # Calculate DO concentration in tank layers
        # reset DO if tank is empty
        if DB_d <= 0.01:
            t1 = 0
            t2 = 0
            t3 = 0
            DO1 = 0.0
            DO2 = 0.0
            DO3 = 0.0
            Wetland_DO1.append(DO1)
            Wetland_DO2.append(DO2)
            Wetland_DO3.append(DO3)
            k_ni = 0.0
        
        elif 0.01 < DB_d <= 3.00:
            # Calculate DO concentration in first layer
            t1 += dt
            t2 = 0
            t3 = 0
            DO1 = Co_DO*np.exp(-k_DO*t1)
            DO2 = 0.0
            DO3 = 0.0
            # Calculate nitate reaction rate based on DO concentration
            if DO1 <= 1.0:
                k_ni = 0.000029  # [1/5 sec]
            else:
                k_ni = 0.0
            Wetland_DO1.append(DO1)
            Wetland_DO2.append(DO2)
            Wetland_DO3.append(DO3)
        
        elif 3.0 < DB_d <= 6.0:
            # Calculate DO concentration in first two layers
            t1 += dt
            t2 += dt
            t3 = 0
            DO1 = Co_DO*np.exp(-k_DO*t1)
            DO2 = Co_DO*np.exp(-k_DO*t2)
            DO3 = 0.0
            # Calculate nitate reaction rate based on DO concentration
            if DO1 <= 1.0:
                k_ni1 = 0.000029
            else:
                k_ni1 = 0.0
            if DO2 <= 1.0:
                k_ni2 = 0.000029
            else:
                k_ni2 = 0.0
            Wetland_DO1.append(DO1)
            Wetland_DO2.append(DO2)
            Wetland_DO3.append(DO3)
        else:
            # Calculate DO concentration in all three layers
            t1 += dt
            t2 += dt
            t3 += dt
            DO1 = Co_DO*np.exp(-k_DO*t1)
            DO2 = Co_DO*np.exp(-k_DO*t2)
            DO3 = Co_DO*np.exp(-k_DO*t3)
            # Calculate nitate reaction rate based on DO concentration
            if DO1 <= 1.0:
                k_ni1 = 0.000029
            else:
                k_ni1 = 0.0
            if DO2 <= 1.0:
                k_ni2 = 0.000029
            else:
                k_ni2 = 0.0
            if DO3 <= 1.0:
                k_ni3 = 0.000029
            else:
                k_ni3 = 0.0
            k_ni = k_ni1 + k_ni2 + k_ni3
            Wetland_DO1.append(DO1)
            Wetland_DO2.append(DO2)
            Wetland_DO3.append(DO3)
        
        # Calculate NO concentration in tanks
        # Get parameters to calculate NO
        Cin=sim._model.getNodeCin("93-49759",0)

        #Solve ODE
        if index == 0:
            solver1.set_initial_value(0.0, 0.0)
            solver1.set_f_params(Wt_if,Cin,Wt_of,Wt_v,k_ni)
            solver1.integrate(solver1.t+dt)
            solver2.set_initial_value(0.0, 0.0)
            solver2.set_f_params(Wt_if,Cin,Wt_of,Wt_v,k_ni)
            solver2.integrate(solver2.t+dt)
            solver3.set_initial_value(0.0, 0.0)
            solver3.set_f_params(Wt_if,Cin,Wt_of,Wt_v,k_ni)
            solver3.integrate(solver3.t+dt)
        else:
            solver1.set_initial_value(solver1.y, solver1.t)
            solver1.set_f_params(Wt_if,Cin,Wt_of,Wt_v,k_ni)
            solver1.integrate(solver1.t+dt)
            solver2.set_initial_value(solver2.y, solver2.t)
            solver2.set_f_params(Wt_if,solver1.y,Wt_of,Wt_v,k_ni)
            solver2.integrate(solver2.t+dt)
            solver3.set_initial_value(solver3.y, solver3.t)
            solver3.set_f_params(Wt_if,solver2.y,Wt_of,Wt_v,k_ni)
            solver3.integrate(solver3.t+dt)
        
        # Set new concentration
        sim._model.setNodePollutant("93-49759", 0, solver3.y[0])

    sim._model.swmm_end()
    print(sim.runoff_error)
    print(sim.flow_routing_error)
    print(sim.quality_error)

# Convert inflow rate from cfs to m3/s
conv_cfs_cms = [0.02832]*len(Ellsworth_inflow)
Ellsworth_inflow_m = [a*b for a,b in zip(Ellsworth_inflow,conv_cfs_cms)]
DBasin_inflow_m = [a*b for a,b in zip(DBasin_inflow,conv_cfs_cms)]
Wetland_inflow_m = [a*b for a,b in zip(Wetland_inflow,conv_cfs_cms)]
Channel_flow_m = [a*b for a,b in zip(Channel_flow,conv_cfs_cms)]

# Convert outflow rate from cfs to m3/s
conv_cfs_cms = [0.02832]*len(Ellsworth_inflow)
Ellsworth_outflow_m = [a*b for a,b in zip(Ellsworth_outflow,conv_cfs_cms)]
DBasin_outflow_m = [a*b for a,b in zip(DBasin_outflow,conv_cfs_cms)]
Wetland_outflow_m = [a*b for a,b in zip(Wetland_outflow,conv_cfs_cms)]

# Convert flooding rate from cfs to m3/s
conv_cfs_cms = [0.02832]*len(Ellsworth_inflow)
Ellsworth_flooding_m = [a*b for a,b in zip(Ellsworth_flooding,conv_cfs_cms)]
Wetland_flooding_m = [a*b for a,b in zip(Wetland_flooding,conv_cfs_cms)]
Wtlnd_bypass_m = [a*b for a,b in zip(Wtlnd_bp_inflows,conv_cfs_cms)]

# Convert depth from ft to m
conv_ft_m = [0.3048]*len(Ellsworth_inflow)
Ellsworth_depth_m = [a*b for a,b in zip(Ellsworth_depth,conv_ft_m)]
DBasin_depth_m = [a*b for a,b in zip(DBasin_depth,conv_ft_m)]
Wetland_depth_m = [a*b for a,b in zip(Wetland_depth,conv_ft_m)]
Channel_depth_m = [a*b for a,b in zip(Channel_depth,conv_ft_m)]

# Convert volume from ft3 to m3
#conv_ft_m = [0.3048]*len(Ellsworth_inflow)
#Ellsworth_volume_m = [a*b for a,b in zip(Ellsworth_volume,conv_ft_m)]
#DBasin_volume_m = [a*b for a,b in zip(DBasin_volume,conv_ft_m)]
#Wetland_volume_m = [a*b for a,b in zip(Wetland_volume,conv_ft_m)]
#Channel_volume_m = [a*b for a,b in zip(Channel_volume,conv_ft_m)]

# Calculate load each timestep
conv_mgs_kgs = [0.000001]*len(Ellsworth_inflow)
timestep = [5]*len(Ellsworth_inflow)
Ellsworth_load = [a*b*c*d*e for a,b,c,d,e in zip(Ellsworth_conc,Ellsworth_outflow,conv_cfs_cms, conv_mgs_kgs,timestep)]
DBasin_load = [a*b*c*d*e for a,b,c,d,e in zip(DBasin_conc,DBasin_outflow,conv_cfs_cms,conv_mgs_kgs,timestep)]
Wetland_load = [a*b*c*d*e for a,b,c,d,e in zip(Wetland_conc,Wetland_outflow,conv_cfs_cms, conv_mgs_kgs,timestep)]
Channel_load = [a*b*c*d*e for a,b,c,d,e in zip(Channel_conc,Channel_flow,conv_cfs_cms,conv_mgs_kgs,timestep)]

# Calculate cumulative load (dt = 1)
Ellsworth_cumload = np.cumsum(Ellsworth_load)
DBasin_cumload = np.cumsum(DBasin_load)
Wetland_cumload = np.cumsum(Wetland_load)
Channel_cumload = np.cumsum(Channel_load)

# Calculate cumulative flooding
#Ellsworth_cumvol = np.cumsum(Ellsworth_flooding_m)
#DBasin_cumvol = np.cumsum(DBasin_flooding_m)
#Wetland_cumvol = np.cumsum(Wetland_flooding_m)
#Channel_cumvol = np.cumsum(Channel_flooding_m)

#----------------------------------------------------------------------#
# Controlled Simulation 
# Lists to store results
Ellsworth_inflowC = []
Ellsworth_concC = []
Ellsworth_cuminloadC = []
Ellsworth_depthC = []
Ellsworth_floodingC = []
Ellsworth_valveC = []
Ellsworth_outflowC = []
Ellsworth_cumloadC = []

DBasin_inflowC = []
DBasin_concC = []
DBasin_cuminloadC = []
DBasin_depthC = []
DBasin_outflowC = []
DBasin_cumloadC = []

Wetland_inflowC = []
Wetland_concC = []
Wetland_cuminload = []
Wetland_depthC = []
Wetland_floodingC = []
Wetland_volumeC = []
Wetland_valveC = []
Wetland_outflowC = []
Wetland_cumloadC = []
Wetland_DO1C = []
Wetland_DO2C = []
Wetland_DO3C = []
Wtlnd_bp_inflowsC = []

Channel_flowC = []
Channel_concC = []
Channel_cuminload = []
Channel_depthC = []
Channel_outflowC = []
Channel_cumloadC = []

# Setup toolbox simulation
with Simulation("./modifiedMBDoyle_NO.inp") as sim:
    
    # Get asset information
    Ellsworth = Nodes(sim)["93-50408"]
    Ells_valve = Links(sim)["95-70951"]
    DBasin = Nodes(sim)["93-50404"]
    Channel = Links(sim)["95-70277"]
    Wetland = Nodes(sim)["93-49759"]
    Wtlnd_bypass = Links(sim)["95-70294"]
    Wtlnd_valve = Links(sim)["95-70293"]

    # Setup dt calculation        
    start_time = sim.start_time
    last_timestep = start_time

    # Setup CSTR solver
    solver1 = ode(CSTR_tank)
    solver1.set_integrator("dopri5")
    solver2 = ode(CSTR_tank)
    solver2.set_integrator("dopri5")
    solver3 = ode(CSTR_tank)
    solver3.set_integrator("dopri5")

    # Tracking time for control actions every 15 minutes (5 sec time step)
    _tempcount1 = 180
    _tempcount2 = 180

    # Tracking time for DO reaction
    t1 = 0
    t2 = 0
    t3 = 0

    # Step through the simulation    
    for index,step in enumerate(sim):

        # Calculate dt
        current_step = sim.current_time
        dt = (current_step - last_timestep).total_seconds()
        last_timestep = current_step

        # Get TSS conc for each asset        
        Ell_p = Ellsworth.pollut_quality['NO']
        Ellsworth_concC.append(Ell_p)
        DB_p = DBasin.pollut_quality['NO']
        DBasin_concC.append(DB_p)
        Wt_p = Wetland.pollut_quality['NO']
        Wetland_concC.append(Wt_p)
        Ch_p = Channel.pollut_quality['NO']
        Channel_concC.append(Ch_p)

        # Get flow for  each asset
        Ell_if = Ellsworth.total_inflow
        Ellsworth_inflowC.append(Ell_if)
        Ell_d = Ellsworth.depth
        Ellsworth_depthC.append(Ell_d)
        Ell_fl = Ellsworth.flooding
        Ellsworth_floodingC.append(Ell_fl)
        Ell_of = Ellsworth.total_outflow
        Ellsworth_outflowC.append(Ell_of)
        DB_if = DBasin.total_inflow
        DBasin_inflowC.append(DB_if)
        DB_d = DBasin.depth
        DBasin_depthC.append(DB_d)
        DBasin_outflowC.append(DB_of)
        Wt_if = Wetland.total_inflow
        Wetland_inflowC.append(Wt_if)
        Wt_d = Wetland.depth
        Wetland_depthC.append(Wt_d)
        Wt_fl = Wetland.flooding
        Wetland_floodingC.append(Wt_fl)
        Wt_v = Wetland.volume
        Wetland_volumeC.append(Wt_v)
        Wt_of = Wetland.total_outflow
        Wetland_outflowC.append(DB_of)
        Wt_bp = Wtlnd_bypass.flow
        Wtlnd_bp_inflowsC.append(Wt_bp)
        Ch_f = Channel.flow
        Channel_flowC.append(Ch_f)
        Ch_d = Channel.depth
        Channel_depthC.append(Ch_d)

        # Calculate DO concentration in tank layers
        # reset DO if tank is empty
        if DB_d <= 0.01:
            t1 = 0
            t2 = 0
            t3 = 0
            DO1 = 0.0
            DO2 = 0.0
            DO3 = 0.0
            Wetland_DO1C.append(DO1)
            Wetland_DO2C.append(DO2)
            Wetland_DO3C.append(DO3)
            k_ni = 0.0
        
        elif 0.01 < DB_d <= 3.00:
            # Calculate DO concentration in first layer
            t1 += dt
            t2 = 0
            t3 = 0
            DO1 = Co_DO*np.exp(-k_DO*t1)
            DO2 = 0.0
            DO3 = 0.0
            # Calculate nitate reaction rate based on DO concentration
            if DO1 <= 1.0:
                k_ni = 0.000029  # [1/5 sec]
            else:
                k_ni = 0.0
            Wetland_DO1C.append(DO1)
            Wetland_DO2C.append(DO2)
            Wetland_DO3C.append(DO3)
        
        elif 3.0 < DB_d <= 6.0:
            # Calculate DO concentration in first two layers
            t1 += dt
            t2 += dt
            t3 = 0
            DO1 = Co_DO*np.exp(-k_DO*t1)
            DO2 = Co_DO*np.exp(-k_DO*t2)
            DO3 = 0.0
            # Calculate nitate reaction rate based on DO concentration
            if DO1 <= 1.0:
                k_ni1 = 0.000029
            else:
                k_ni1 = 0.0
            if DO2 <= 1.0:
                k_ni2 = 0.000029
            else:
                k_ni2 = 0.0
            Wetland_DO1C.append(DO1)
            Wetland_DO2C.append(DO2)
            Wetland_DO3C.append(DO3)
        else:
            # Calculate DO concentration in all three layers
            t1 += dt
            t2 += dt
            t3 += dt
            DO1 = Co_DO*np.exp(-k_DO*t1)
            DO2 = Co_DO*np.exp(-k_DO*t2)
            DO3 = Co_DO*np.exp(-k_DO*t3)
            # Calculate nitate reaction rate based on DO concentration
            if DO1 <= 1.0:
                k_ni1 = 0.000029
            else:
                k_ni1 = 0.0
            if DO2 <= 1.0:
                k_ni2 = 0.000029
            else:
                k_ni2 = 0.0
            if DO3 <= 1.0:
                k_ni3 = 0.000029
            else:
                k_ni3 = 0.0
            k_ni = k_ni1 + k_ni2 + k_ni3
            Wetland_DO1C.append(DO1)
            Wetland_DO2C.append(DO2)
            Wetland_DO3C.append(DO3)
        
        # Calculate NO concentration in tanks
        # Get parameters to calculate NO
        Cin=sim._model.getNodeCin("93-49759",0)

        #Solve ODE
        if index == 0:
            solver1.set_initial_value(0.0, 0.0)
            solver1.set_f_params(Wt_if,Cin,Wt_of,Wt_v,k_ni)
            solver1.integrate(solver1.t+dt)
            solver2.set_initial_value(0.0, 0.0)
            solver2.set_f_params(Wt_if,Cin,Wt_of,Wt_v,k_ni)
            solver2.integrate(solver2.t+dt)
            solver3.set_initial_value(0.0, 0.0)
            solver3.set_f_params(Wt_if,Cin,Wt_of,Wt_v,k_ni)
            solver3.integrate(solver3.t+dt)
        else:
            solver1.set_initial_value(solver1.y, solver1.t)
            solver1.set_f_params(Wt_if,Cin,Wt_of,Wt_v,k_ni)
            solver1.integrate(solver1.t+dt)
            solver2.set_initial_value(solver2.y, solver2.t)
            solver2.set_f_params(Wt_if,solver1.y,Wt_of,Wt_v,k_ni)
            solver2.integrate(solver2.t+dt)
            solver3.set_initial_value(solver3.y, solver3.t)
            solver3.set_f_params(Wt_if,solver2.y,Wt_of,Wt_v,k_ni)
            solver3.integrate(solver3.t+dt)
        
        # Set new concentration
        sim._model.setNodePollutant("93-49759", 0, solver3.y[0])

        # Wetland & Ellsworth Control Actions (every 15 mins - 5 sec timesteps)
        if _tempcount1 == 180:
            # If any of DO levels are above the anoxic zone
            if (DO1 or DO2 or DO3) > 1.0:
                # And if  the  wetland has capacity
                if Wt_d <= 9.5:
                    # Close the wetland valve and proprtionally open Ellsworth valve
                    Wtlnd_valve.target_setting = 0.0
                    Ells_valve.target_setting = min(1.0, 70.6/(np.sqrt(2.0*32.2*Ell_d))/25)
                    print("high DO, Wt cap")
                # If not, open the wetland valve and close the Ellsworth valve
                else:
                    Wtlnd_valve.target_setting = min(1.0, 70.6/(np.sqrt(2.0*32.2*Wt_d))/12.6)
                    Ells_valve.target_setting = 0.0
                    print("high DO, no Wt cap")
            # If all DO levels are in the anoxic zone
            elif (DO1 and DO2 and DO3) <= 1.0:
                # And if the Wetland NO concentration is low, open both valves
                if Wt_p <= 5.0:
                    Wtlnd_valve.target_setting = min(1.0, 70.6/(np.sqrt(2.0*32.2*Wt_d))/12.6)
                    Ells_valve.target_setting = min(1.0, 70.6/(np.sqrt(2.0*32.2*Ell_d))/25)
                    print("low DO, low NO")
                #  Else if the Wetlandn NO conc. is high
                else:
                    # And if the wetland still has capacity, close both valves
                    if Wt_d <= 9.5:
                        Wtlnd_valve.target_setting = 0.0
                        Ells_valve.target_setting = 0.0
                        print("low DO, high NO, Wt cap")
                    # If the wetland doesn't have capacity, open the wetland and close Ellsworth valve
                    else:
                        Wtlnd_valve.target_setting = min(1.0, 70.6/(np.sqrt(2.0*32.2*Wt_d))/12.6)
                        Ells_valve.target_setting = 0.0
                        print("low DO, high NO, no Wt cap")
            _tempcount1= 0
        _tempcount1+= 1

        Wetland_valveC.append(Wtlnd_valve.target_setting)
        Ellsworth_valveC.append(Ells_valve.target_setting)

    sim._model.swmm_end()
    print(sim.runoff_error)
    print(sim.flow_routing_error)
    print(sim.quality_error)

# Convert inflow rate from cfs to m3/s
conv_cfs_cms = [0.02832]*len(Ellsworth_inflowC)
Ellsworth_inflow_mC = [a*b for a,b in zip(Ellsworth_inflowC,conv_cfs_cms)]
DBasin_inflow_mC = [a*b for a,b in zip(DBasin_inflowC,conv_cfs_cms)]
Wetland_inflow_mC = [a*b for a,b in zip(Wetland_inflowC,conv_cfs_cms)]
Channel_flow_mC = [a*b for a,b in zip(Channel_flowC,conv_cfs_cms)]

# Convert outflow rate from cfs to m3/s
conv_cfs_cms = [0.02832]*len(Ellsworth_inflowC)
Ellsworth_outflow_mC = [a*b for a,b in zip(Ellsworth_outflowC,conv_cfs_cms)]
DBasin_outflow_mC = [a*b for a,b in zip(DBasin_outflowC,conv_cfs_cms)]
Wetland_outflow_mC = [a*b for a,b in zip(Wetland_outflowC,conv_cfs_cms)]

# Convert flooding rate from cfs to m3/s
conv_cfs_cms = [0.02832]*len(Ellsworth_inflowC)
Ellsworth_flooding_mC = [a*b for a,b in zip(Ellsworth_floodingC,conv_cfs_cms)]
Wetland_flooding_mC = [a*b for a,b in zip(Wetland_floodingC,conv_cfs_cms)]
Wtlnd_bypass_mC = [a*b for a,b in zip(Wtlnd_bp_inflowsC,conv_cfs_cms)]

# Convert depth from ft to m
conv_ft_m = [0.3048]*len(Ellsworth_inflowC)
Ellsworth_depth_mC = [a*b for a,b in zip(Ellsworth_depthC,conv_ft_m)]
DBasin_depth_mC = [a*b for a,b in zip(DBasin_depthC,conv_ft_m)]
Wetland_depth_mC = [a*b for a,b in zip(Wetland_depthC,conv_ft_m)]
Channel_depth_mC = [a*b for a,b in zip(Channel_depthC,conv_ft_m)]

# Convert volume from ft3 to m3
#conv_ft_mC = [0.3048]*len(Ellsworth_inflow)
#Ellsworth_volume_mC = [a*b for a,b in zip(Ellsworth_volumeC,conv_ft_m)]
#DBasin_volume_mC = [a*b for a,b in zip(DBasin_volumeC,conv_ft_m)]
#Wetland_volume_mC = [a*b for a,b in zip(Wetland_volumeC,conv_ft_m)]
#Channel_volume_mC = [a*b for a,b in zip(Channel_volumeC,conv_ft_m)]

# Calculate outflow load each timestep
conv_mgs_kgs = [0.000001]*len(Ellsworth_inflowC)
timestep = [5]*len(Ellsworth_inflowC)
Ellsworth_loadC = [a*b*c*d*e for a,b,c,d,e in zip(Ellsworth_concC,Ellsworth_outflowC,conv_cfs_cms, conv_mgs_kgs,timestep)]
DBasin_loadC = [a*b*c*d*e for a,b,c,d,e in zip(DBasin_concC,DBasin_outflowC,conv_cfs_cms,conv_mgs_kgs,timestep)]
Wetland_loadC = [a*b*c*d*e for a,b,c,d,e in zip(Wetland_concC,Wetland_outflowC,conv_cfs_cms, conv_mgs_kgs,timestep)]
Channel_loadC = [a*b*c*d*e for a,b,c,d,e in zip(Channel_concC,Channel_flowC,conv_cfs_cms,conv_mgs_kgs,timestep)]

# Calculate cumulative load
Ellsworth_cumloadC = np.cumsum(Ellsworth_loadC)
DBasin_cumloadC = np.cumsum(DBasin_loadC)
Wetland_cumloadC = np.cumsum(Wetland_loadC)
Channel_cumloadC = np.cumsum(Channel_loadC)

# Calculate cumulative flooding
#Ellsworth_cumvolC = np.cumsum(Ellsworth_flooding_mC)
#DBasin_cumvolC = np.cumsum(DBasin_flooding_mC)
#Wetland_cumvolC = np.cumsum(Wetland_flooding_mC)
#Channel_cumvolC = np.cumsum(Channel_flooding_mC)

#----------------------------------------------------------------------#

# Print final load released
print("Ellsworth:", Ellsworth_cumload[-1])
print("Doyle Basin:", DBasin_cumload[-1])
print("Wetland:", Wetland_cumload[-1])
print("Channel to Outfall:", Channel_cumload[-1]) 
print("Ellsworth Controlled:", Ellsworth_cumloadC[-1])
print("Doyle Basin Controlled:", DBasin_cumloadC[-1])
print("Wetland Controlled:", Wetland_cumloadC[-1])
print("Channel Controlled:", Channel_cumloadC[-1])

#----------------------------------------------------------------------#

# Data for flooding line
Ell_flood = [6.0960]*len(Ellsworth_inflowC)
Wt_bypass = [2.8956]*len(Ellsworth_inflowC)
Wt_flood  = [2.7432]*len(Ellsworth_inflowC)

# Plot Result
fig, ax = plt.subplots(8, 4, sharex=True)
ax[0,0].plot(Ellsworth_inflow_m, 'k--')
ax[0,0].plot(Ellsworth_inflow_mC, 'b')
ax[0,0].set_ylabel("Inflow")
ax[0,0].set_title("Ellsworth")
ax[1,0].plot(Ellsworth_conc, 'k--')
ax[1,0].plot(Ellsworth_concC, 'b')
ax[1,0].set_ylabel("NO (mg/L)")
ax[2,0].set_ylabel("DO (mg/L")
ax[3,0].plot(Ell_flood, 'r')
ax[3,0].plot(Ellsworth_depth_m, 'k--')
ax[3,0].plot(Ellsworth_depth_mC, 'b')
ax[3,0].set_ylabel("Depth (m)")
ax[4,0].plot(Ellsworth_valveC, 'b')
ax[4,0].set_ylabel("Valve Position")
ax[5,0].plot(Ellsworth_outflow_m, 'k--')
ax[5,0].plot(Ellsworth_outflow_mC, 'b')
ax[5,0].set_ylabel("Outflow (m³/s)")
ax[6,0].plot(Ellsworth_cumload, 'k--')
ax[6,0].plot(Ellsworth_cumloadC, 'b')
ax[6,0].set_ylabel("Cum. Load (kg)")
ax[7,0].plot(Ellsworth_flooding_m, 'k--')
ax[7,0].plot(Ellsworth_flooding_mC, 'b')
ax[7,0].set_ylabel("Flooding (m³/s)")
ax[7,0].set_xlabel("Time")
ax[0,1].plot(DBasin_inflow_m, "k--")
ax[0,1].plot(DBasin_inflow_mC, "b")
ax[0,1].set_title("Basin")
ax[1,1].plot(DBasin_conc, "k--")
ax[1,1].plot(DBasin_concC, "b")
ax[3,1].plot(Wt_bypass, 'r')
ax[3,1].plot(DBasin_depth_m, "k--")
ax[3,1].plot(DBasin_depth_mC, "b")
ax[5,1].plot(DBasin_outflow_m, "k--")
ax[5,1].plot(DBasin_outflow_mC, "b")
ax[6,1].plot(DBasin_cumload, "k--")
ax[6,1].plot(DBasin_cumloadC, "b")
ax[7,1].plot(Wtlnd_bypass_m, 'k--')
ax[7,1].plot(Wtlnd_bypass_mC, "b")
ax[7,1].set_xlabel("Time")
ax[0,2].plot(Wetland_inflow_m, "k--")
ax[0,2].plot(Wetland_inflow_mC, "b")
ax[0,2].set_title("Wetland")
ax[1,2].plot(Wetland_conc, "k--")
ax[1,2].plot(Wetland_concC, "b")
ax[2,2].plot(Wetland_DO1, "m--")
ax[2,2].plot(Wetland_DO2, "g--")
ax[2,2].plot(Wetland_DO3, "c--")
ax[2,2].plot(Wetland_DO1C, "m")
ax[2,2].plot(Wetland_DO2C, "g")
ax[2,2].plot(Wetland_DO3C, "c")
ax[3,2].plot(Wt_flood, 'r')
ax[3,2].plot(Wetland_depth_m, "k--")
ax[3,2].plot(Wetland_depth_mC, "b")
ax[4,2].plot(Wetland_valveC, "b")
ax[5,2].plot(Wetland_outflow_m, "k--")
ax[5,2].plot(Wetland_outflow_mC, "b")
ax[6,2].plot(Wetland_cumload, "k--")
ax[6,2].plot(Wetland_cumloadC, "b")
ax[7,2].plot(Wetland_flooding_m, 'k--')
ax[7,2].plot(Wetland_flooding_mC, 'b')
ax[7,2].set_xlabel("Time")
ax[0,3].plot(Channel_flow_m, "k--")
ax[0,3].plot(Channel_flow_mC, "b")
ax[0,3].set_title("Channel")
ax[1,3].plot(Channel_conc, "k--")
ax[1,3].plot(Channel_concC, "b")
ax[3,3].plot(Channel_depth_m, "k--")
ax[3,3].plot(Channel_depth_mC, "b")
ax[5,3].plot(Channel_flow_m, "k--")
ax[5,3].plot(Channel_flow_mC, "b")
ax[6,3].plot(Channel_cumload, "k--")
ax[6,3].plot(Channel_cumloadC, "b")
ax[7,3].set_xlabel("Time")
plt.show()
