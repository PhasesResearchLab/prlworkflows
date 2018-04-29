"""
E-V curve workflow

Inputs
------

structure : Structure
num_deformations : int
deformation_fraction : float

"""
# Imports
import logging
logging.basicConfig(level=logging.DEBUG)
from prlworkflows.input_sets import PRLStaticSet
from pymatgen import Structure, Lattice
import numpy as np
import os
from prlworkflows.tools import run_vasp_custodian

# Setup

structure = Structure.from_spacegroup('Fm-3m', Lattice.cubic(4), ['Al'], [[0,0,0]])
num_deformations = 1
deformation_fraction = 0.05  # 5 percent
CalculationInputSet = PRLStaticSet
name = 'Al-EV-curve'

## Script

os.mkdir(name)
os.chdir(name)

deformations = np.linspace(1--deformation_fraction, 1+deformation_fraction, num_deformations)

deformed_structures = []
for defo in deformations:
    deformed_struct = structure.copy()
    deformed_struct.scale_lattice(structure.volume*defo)
    deformed_structures.append(deformed_struct)


for i, struct in enumerate(deformed_structures):
    vis = CalculationInputSet(struct, grid_density=4000)
    run_vasp_custodian(vis, 'run_0-vol_{}'.format(i))


