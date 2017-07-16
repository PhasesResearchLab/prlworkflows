"""
The sqs_db module handles creating and interacting with an SQS database of pymatgen-serialized SQS.

There are helper functions for converting SQS generated by mcsqs in ATAT to pymatgen Structure
objects that  serialization.

The sublattice and types are the same as used in ATAT, where `a_B` corresponds to atom `B` in
sublattice `a`. Due to the way dummy species are implemented in pymatgen, these species in pymatgen
Structures are renamed to `Xab`, which similarly corresponds to atom `B` in sublattice `a`.

In general, the workflow to create a database is to use the helper functions to
1. convert the lattice.in ATAT files to CIFs with renaming
2. create Structure objects from those CIFs, removing oxidation states (no helper function)
3. write those Structures to the database
4. persist the database to a path (no helper function)

Later, the database can be constructed again from the path, added to (steps 1-3) and persisted again.

To use the database, the user calls the `structures_from_database` helper function to generate a list
of all the SQS that match the endmember symmetry, sublattice model (and site ratios) that define a
phase. This is intentionally designed to match the syntax used to describe phases in ESPEI. Each of
the resulting Structure objects can be made concrete using functions in `prlworkflows.sqs`.
"""

import json

import numpy as np
from tinydb import TinyDB
from tinydb.storages import MemoryStorage
from pyparsing import Regex, Word, alphas, OneOrMore, LineEnd, Suppress, Group
from pymatgen import Lattice

from prlworkflows.sqs import SQS
from prlworkflows.utils import recursive_glob

def _parse_atat_lattice(lattice_in):
    """Parse an ATAT-style `lat.in` string.

    The parsed string will be in three groups: (Coordinate system) (lattice) (atoms)
    where the atom group is split up into subgroups, each describing the position and atom name
    """
    float_number = Regex(r'[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?').setParseAction(lambda t: [float(t[0])])
    vector = Group(float_number + float_number + float_number)
    angles = vector
    vector_line = vector + Suppress(LineEnd())
    coord_sys = Group((vector_line + vector_line + vector_line) | (vector + angles + Suppress(LineEnd())))
    lattice = Group(vector + vector + vector)
    atom = Group(vector + Group(OneOrMore(Word(alphas + '_'))))
    atat_lattice_grammer = coord_sys + lattice + Group(OneOrMore(atom))
    # parse the input string and convert it to a POSCAR string
    return atat_lattice_grammer.parseString(lattice_in)

def lat_in_to_sqs(atat_lattice_in, rename=True):
    """
    Convert a string-like ATAT-style lattice.in to an abstract SQS.

    Parameters
    ----------
    atat_lattice_in : str
        String-like of a lattice.in in the ATAT format.
    rename : bool
        If True, SQS format element names will be renamed, e.g. `a_B` -> `Xab`. Default is True.

    Returns
    -------
    SQS
        Abstract SQS.
    """
    # TODO: handle numeric species, e.g. 'g1'.
    # Problems: parser has trouble with matching next line and we have to rename it so pymatgen
    # doesn't think it's a charge.
    # parse the data
    parsed_data = _parse_atat_lattice(atat_lattice_in)
    atat_coord_system = parsed_data[0]
    atat_lattice = parsed_data[1]
    atat_atoms = parsed_data[2]
    # create the lattice
    if len(atat_coord_system) == 3:
        # we have a coordinate system matrix
        coord_system = Lattice(list(atat_coord_system)).matrix
    else:
        # we have length and angles
        coord_system = Lattice.from_lengths_and_angles(list(atat_coord_system[0]), list(atat_coord_system[1])).matrix
    direct_lattice = Lattice(list(atat_lattice))
    lattice = coord_system.dot(direct_lattice.matrix)
    # create the list of atoms, converted to the right coordinate system
    species_list = []
    species_positions = []
    subl_model = {} # format {'subl_name': 'atoms_found_in_subl, e.g. "aaabbbb"'}
    for position, atoms in atat_atoms:
        # atoms can be a list of atoms, e.g. for not abstract SQS
        if len(atoms) > 1:
            raise NotImplementedError('Cannot parse atom list {} because the sublattice is unclear.\nParsed data: {}'.format(atoms, atat_atoms))
        atom = atoms[0]
        if rename:
            # change from `a_B` style to `Xab`

            atom = atom.lower().split('_')
        else:
            raise NotImplementedError('Cannot rename because the atom name and sublattice name may be ambigous.')
        # add the abstract atom to the sublattice model
        subl = atom[0]
        subl_atom = atom[1]
        subl_model[subl] = subl_model.get(subl, set()).union({subl_atom})
        # add the species and position to the lists
        species_list.append('X'+subl+subl_atom)
        species_positions.append(list(position))
    # create the structure
    sublattice_model = [[e for e in sorted(list(set(subl_model[s])))] for s in sorted(subl_model.keys())]
    sublattice_names = [s for s in sorted(subl_model.keys())]
    sqs = SQS(direct_lattice, species_list, species_positions, coords_are_cartesian=True,
              sublattice_model=sublattice_model,
              sublattice_names=sublattice_names)
    sqs.modify_lattice(Lattice(lattice))

    return sqs


def SQSDatabase(path):
    """
    Convienence function to create a TinyDB for the SQS database found at `path`.

    Parameters
    ----------
    path : path-like of the folder containing the SQS database.

    Returns
    -------
    TinyDB
        Database of abstract SQS.
    """
    db = TinyDB(storage=MemoryStorage)
    dataset_filenames = recursive_glob(path, '*.json')
    for fname in dataset_filenames:
        with open(fname) as file_:
            try:
                db.insert(json.load(file_))
            except ValueError as e:
                raise ValueError('JSON Error in {}: {}'.format(fname, e))
    return db


def structures_from_database(db, subl_model, subl_site_ratios):
    """Returns a list of Structure objects from the db that match the criteria.

    The returned list format supports matching SQS to phases that have multiple solution sublattices
    and the inclusion of higher and lower ordered SQS that match the criteria.

    Parameters
    ----------
    db : TinyDB
        TinyDB database of the SQS database
    symmetry : str
        Spacegroup symbol for a non-mixing endmember as in pymatgen, e.g. 'Pm-3m'.
    subl_model : [[str]]
        List of strings of species names, in the style of ESPEI `input.json`. This sublattice model
        can be of higher dimension than the SQS. Outer dimension should be the same length as subl_site_ratios.
    subl_site_ratios : [[float]]
        Site ratios of each sublattice. Outer dimension should be the same length as subl_model.

    Returns
    -------
    [SQS]
        Abstract SQSs that match the symmetry and sublattice model.
    """
    pass
