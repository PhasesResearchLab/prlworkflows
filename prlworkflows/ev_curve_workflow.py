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
from prlworkflows.input_sets import PRLStaticSet, PRLRelaxSet
from pymatgen import Structure, Lattice
import numpy as np
import os
from prlworkflows.tools import run_vasp_custodian

# Setup

structure = Structure.from_spacegroup('Fm-3m', Lattice.cubic(4), ['Al'], [[0,0,0]])
num_deformations = 1
deformation_fraction = 0.05  # 5 percent
name = 'Al-EV-curve'

## Script

os.mkdir(name)
os.chdir(name)

deformations = np.linspace(1--deformation_fraction, 1+deformation_fraction, num_deformations)

# follow a scheme of
# 1. ISIF 2
# 2. ISIF 4
# 3. Static
final_dirs = []
for i, deformation in enumerate(deformations):
    struct = structure.copy()
    struct.scale_lattice(struct.volume*deformation)
    vis = PRLRelaxSet(struct, user_incar_settings={'ISIF': 2})
    run_dir = 'structure_{}-0-isif_2'.format(i)
    run_vasp_custodian(vis, run_dir)

    struct = Structure.from_file(os.path.join(run_dir, 'CONTCAR'))
    vis = PRLRelaxSet(struct, user_incar_settings={'ISIF': 4})
    run_dir = 'structure_{}-1-isif_4'.format(i)
    run_vasp_custodian(vis, run_dir)

    struct = Structure.from_file(os.path.join(run_dir, 'CONTCAR'))
    vis = PRLStaticSet(struct)
    run_dir = 'structure_{}-2-static'.format(i)
    run_vasp_custodian(vis, run_dir)

    final_dirs.append(run_dir)

# do any analysis here, e.g. an E-V curve fit and putting results in a Database with metadata
