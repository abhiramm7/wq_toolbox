from pyswmm import Simulation, Nodes
import numpy as np
import matplotlib.pyplot as plt
import faulthandler; faulthandler.enable()

# Single Tank, Constant Inflow, Percent Removal

# PySWMM Toolbox
# Create simulation
conc1 = []
flow1 = [] 
with Simulation("./tank_variableinflow_notreatment.inp") as sim:
    Tank = Nodes(sim)["Tank"]

    # Step through the simulation    
    for step in sim:
        # Get influent concentration
        Cin = sim._model.getNodeCin("Tank", 0)
        # Calculate treatment
        Cnew = Cin*(1-0.5)
        # Set concentration each time step
        sim._model.setNodePollutant("Tank", 0, Cnew)
        # Get newQual for Tank
        c0 = Tank.pollut_quality
        conc1.append(c0['P1'])
        # Get flow for Tank
        flow1.append(sim._model.getNodeResult("Tank", 0))

# SWMM Comparision
# Create simulation
conc2 = []
flow2 = [] 
with Simulation("./tank_variableinflow_percentremoval.inp") as sim:
    Tank = Nodes(sim)["Tank"]

    # Step through the simulation    
    for step in sim:
        # Get newQual for Tank
        c0 = Tank.pollut_quality
        conc2.append(c0['P1'])
        # Get flow for Tank
        flow2.append(sim._model.getNodeResult("Tank", 0))


# Plot Results
# Concentration Results
plt.subplot(211)
plt.plot(conc1, 'r--', label='toolbox')
plt.plot(conc2, 'b:', label='swmm')
plt.ylabel("Concentration")
plt.xlabel("Time (s)")
plt.legend()

# Flow Results
plt.subplot(212)
plt.plot(flow1, 'r--', label='toolbox')
plt.plot(flow2, 'b:', label='swmm')
plt.xlabel("Time (s)")
plt.ylabel("Flow")
plt.legend()
plt.show()
