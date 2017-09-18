"""
This module tests the functionality of the sqs module.

The tests are focused on conversion of structures from the ATAT format to
pymatgen Structures and matching those Structure objects to ESPEI-style
sublattice models and symmetry from user-input.
"""

import numpy as np
import pytest
from pymatgen import Lattice

from prlworkflows.sqs import AbstractSQS, enumerate_sqs, SQS
from prlworkflows.sqs_db import lat_in_to_sqs


ATAT_FCC_L12_LATTICE_IN = """1.000000 0.000000 0.000000
0.000000 1.000000 0.000000
0.000000 0.000000 1.000000
-1.000000 1.000000 -1.000000
1.000000 -1.000000 -1.000000
-2.000000 -2.000000 0.000000
-1.000000 -2.000000 -1.000000 a_A
-2.000000 -1.000000 -1.000000 a_A
-1.000000 -1.000000 -1.000000 a_B
-0.000000 -1.000000 -1.000000 a_B
-1.000000 -0.000000 -1.000000 a_B
-2.000000 -2.000000 -1.000000 a_B
-1.000000 -1.000000 -2.000000 a_A
-2.000000 -2.000000 -2.000000 a_A
-1.000000 -1.500000 -0.500000 c_A
-1.000000 -1.500000 -1.500000 c_A
-1.000000 -0.500000 -0.500000 c_A
-0.000000 -0.500000 -0.500000 c_A
-0.000000 -0.500000 -1.500000 c_A
-2.000000 -1.500000 -0.500000 c_A
-1.000000 -0.500000 -1.500000 c_A
-2.000000 -1.500000 -1.500000 c_A
-1.500000 -1.000000 -1.500000 c_A
-1.500000 -1.000000 -0.500000 c_A
-0.500000 -1.000000 -0.500000 c_A
-0.500000 0.000000 -1.500000 c_A
-0.500000 -0.000000 -0.500000 c_A
-1.500000 -2.000000 -0.500000 c_A
-0.500000 -1.000000 -1.500000 c_A
-1.500000 -2.000000 -1.500000 c_A
-0.500000 -1.500000 -1.000000 c_A
-1.500000 -0.500000 -1.000000 c_A
-0.500000 -0.500000 -1.000000 c_A
-1.500000 -2.500000 -1.000000 c_A
-2.500000 -1.500000 -1.000000 c_A
-1.500000 -1.500000 -1.000000 c_A
-0.500000 -0.500000 -2.000000 c_A
-1.500000 -1.500000 -2.000000 c_A"""

ATAT_ROCKSALT_B1_LATTICE_IN = """1.000000 0.000000 0.000000
0.000000 1.000000 0.000000
0.000000 0.000000 1.000000
2.000000 1.000000 1.000000
-2.000000 1.000000 1.000000
-0.000000 -0.500000 0.500000
-0.500000 1.500000 2.000000 a_A
-0.000000 1.000000 2.000000 a_A
-0.000000 1.500000 2.500000 a_A
0.500000 1.000000 1.500000 a_B
0.500000 1.500000 2.000000 a_B
-1.500000 1.000000 1.500000 a_A
1.000000 0.500000 1.500000 a_A
1.000000 1.000000 2.000000 a_A
-1.000000 0.500000 1.500000 a_B
-1.000000 1.000000 2.000000 a_B
1.500000 1.000000 1.500000 a_B
-0.500000 0.500000 1.000000 a_B
-0.500000 1.000000 1.500000 a_A
-0.000000 -0.000000 1.000000 a_B
-0.000000 0.500000 1.500000 a_B
0.500000 0.500000 1.000000 a_A
-1.000000 1.000000 1.500000 b_B
-0.500000 0.500000 1.500000 b_A
-0.500000 1.000000 2.000000 b_A
0.000000 0.500000 1.000000 b_A
0.000000 1.000000 1.500000 b_B
0.000000 1.500000 2.000000 b_B
0.500000 -0.000000 1.000000 b_B
0.500000 0.500000 1.500000 b_A
0.500000 1.000000 2.000000 b_A
-1.500000 0.500000 1.500000 b_B
1.000000 0.500000 1.000000 b_A
1.000000 1.000000 1.500000 b_A
-1.000000 0.500000 1.000000 b_B
1.500000 0.500000 1.500000 b_B
-0.500000 -0.000000 1.000000 b_B
-0.000000 -0.000000 0.500000 b_A"""

ATAT_GA3PT5_LATTICE_IN = """2.000000 0.000000 0.000000
0.000000 2.000000 0.000000
0.000000 0.000000 1.000000
0.500000 -0.500000 0.000000
0.500000 0.500000 0.000000
0.000000 0.000000 1.000000
0.000000 0.000000 0.000000 aej_A
0.250000 0.250000 0.000000 aej_A
0.750000 0.250000 0.000000 aej_A
0.000000 0.250000 0.500000 aej_A
-0.000000 -0.250000 0.500000 aej_A
0.500000 0.000000 0.000000 bh_A
0.250000 0.000000 0.500000 bh_A
-0.250000 0.000000 0.500000 bh_A"""

ATAT_GA3PT5_LATTICE_IN_MUTLI_ATOM = """2.000000 0.000000 0.000000
0.000000 2.000000 0.000000
0.000000 0.000000 1.000000
0.500000 -0.500000 0.000000
0.500000 0.500000 0.000000
0.000000 0.000000 1.000000
0.000000 0.000000 0.000000 aej_Af
0.250000 0.250000 0.000000 aej_Af
0.750000 0.250000 0.000000 aej_Af
0.000000 0.250000 0.500000 aej_Af
-0.000000 -0.250000 0.500000 aej_Af
0.500000 0.000000 0.000000 bh_Aqwerty
0.250000 0.000000 0.500000 bh_Aqwerty
-0.250000 0.000000 0.500000 bh_Aqwerty"""


# noinspection PyProtectedMember,PyProtectedMember
def test_atat_bestsqs_is_correctly_parsed_to_sqs():
    """lattice.in files in the ATAT format should be converted to SQS correctly."""
    structure = lat_in_to_sqs(ATAT_FCC_L12_LATTICE_IN)
    specie_types = {specie.symbol for specie in structure.types_of_specie}
    assert specie_types == {'Xaa', 'Xab', 'Xca'}
    assert np.all(structure.sublattice_model == [['a', 'b'], ['a']])
    assert structure.normalized_sublattice_site_ratios == [[0.125, 0.125], [0.75]]
    assert structure.sublattice_site_ratios == [[1, 1], [6]]
    assert np.all(structure._sublattice_names == ['a', 'c'])

    structure = lat_in_to_sqs(ATAT_ROCKSALT_B1_LATTICE_IN)
    specie_types = {specie.symbol for specie in structure.types_of_specie}
    assert specie_types == {'Xaa', 'Xab', 'Xba', 'Xbb'}
    assert np.all(structure.sublattice_model == [['a', 'b'], ['a', 'b']])
    assert structure.normalized_sublattice_site_ratios == [[0.25, 0.25], [0.25, 0.25]]
    assert structure.sublattice_site_ratios == [[1, 1], [1, 1]]
    assert np.all(structure._sublattice_names == ['a', 'b'])


def test_atat_bestsqs_is_correctly_parsed_to_sqs_with_multicharacter_sublattice():
    """lattice.in files in the ATAT format should be converted to SQS correctly."""
    structure = lat_in_to_sqs(ATAT_GA3PT5_LATTICE_IN)
    specie_types = {specie.symbol for specie in structure.types_of_specie}
    assert specie_types == {'Xaeja', 'Xbha'}
    assert np.all(structure.sublattice_model == [['a'], ['a']])
    assert structure.normalized_sublattice_site_ratios == [[0.625], [0.375]]
    assert structure.sublattice_site_ratios == [[5], [3]]
    assert np.all(structure._sublattice_names == ['aej', 'bh'])
    concrete_structure = structure.get_concrete_sqs([['Fe'], ['Ni']])
    assert np.all(concrete_structure.sublattice_configuration == [['Fe'], ['Ni']])


def test_atat_bestsqs_is_correctly_parsed_to_sqs_with_multicharacter_atom():
    """lattice.in files in the ATAT format should be converted to SQS correctly."""
    structure = lat_in_to_sqs(ATAT_GA3PT5_LATTICE_IN_MUTLI_ATOM)
    specie_types = {specie.symbol for specie in structure.types_of_specie}
    assert specie_types == {'Xaejaf', 'Xbhaqwerty'}
    assert np.all(structure.sublattice_model == [['af'], ['aqwerty']])
    assert structure.normalized_sublattice_site_ratios == [[0.625], [0.375]]
    assert structure.sublattice_site_ratios == [[5], [3]]
    assert np.all(structure._sublattice_names == ['aej', 'bh'])
    concrete_structure = structure.get_concrete_sqs([['Fe'], ['Ni']])
    assert np.all(concrete_structure.sublattice_configuration == [['Fe'], ['Ni']])
    assert np.all(concrete_structure.sublattice_site_ratios == [5, 3])


def test_sqs_obj_correctly_serialized():
    """Tests that the as_dict method of the SQS object correctly includes metadata and is able to be seralized/unserialized."""
    sqs = AbstractSQS(Lattice.cubic(5), ['Xaa', 'Xab'], [[0,0,0],[0.5,0.5,0.5]],
              sublattice_model=[['a', 'b']],
              sublattice_names=['a'])

    # first seralization
    s1 = AbstractSQS.from_dict(sqs.as_dict())
    assert sqs == s1
    assert s1.sublattice_model == [['a', 'b']]
    assert s1._sublattice_names == ['a']
    assert s1.normalized_sublattice_site_ratios == [[0.5, 0.5]]

    # second serialization
    s2 = AbstractSQS.from_dict(sqs.as_dict())
    assert sqs == s2
    assert s2.sublattice_model == [['a', 'b']]
    assert s2._sublattice_names == ['a']
    assert s2.normalized_sublattice_site_ratios == [[0.5, 0.5]]

    # test that we can make it concrete
    concrete_structure = s2.get_concrete_sqs([['Fe', 'Ni']])
    assert {s.symbol for s in concrete_structure.types_of_specie} == {'Fe', 'Ni'}


@pytest.mark.skip
def test_higher_order_sqs_list_from_database():
    """List of SQS objects that match the criteria should be extracted from the database.

    This tests that phases with multicomponent (3+) sublattices are matched with SQS for the lower order subsystems.
    """
    raise NotImplementedError

@pytest.mark.skip
def test_multiple_sqs_list_from_database():
    """List of SQS objects that match the criteria should be extracted from the database.

    This tests that phases with multiple solution sublattices can match different SQS that describe
    each sublattice.
    """
    raise NotImplementedError


def test_abstract_sqs_is_properly_substituted_with_sublattice_model():
    """Test that an abstract SQS can correctly be make concrete."""
    structure = lat_in_to_sqs(ATAT_FCC_L12_LATTICE_IN)

    concrete_structure = structure.get_concrete_sqs([['Fe', 'Ni'], ['Al']])
    assert {s.symbol for s in concrete_structure.types_of_specie} == {'Al', 'Fe', 'Ni'}
    assert np.all(concrete_structure.espei_sublattice_occupancies == [[0.5, 0.5] ,1])
    assert np.all(concrete_structure.sublattice_site_ratios == [2, 6])

    structure = lat_in_to_sqs(ATAT_FCC_L12_LATTICE_IN)
    concrete_structure = structure.get_concrete_sqs([['Al', 'Al'], ['Al']])
    assert np.all(concrete_structure.sublattice_configuration == [['Al'], ['Al']])
    assert np.all(concrete_structure.espei_sublattice_configuration == ['Al', 'Al'])
    assert np.all(concrete_structure.espei_sublattice_occupancies == [1 ,1])
    assert {s.symbol for s in concrete_structure.types_of_specie} == {'Al'}


def test_abstract_sqs_scales_volume_when_made_concrete():
    """SQS should scale in volume by default, but optionally not when made concrete"""

    structure = lat_in_to_sqs(ATAT_FCC_L12_LATTICE_IN)
    concrete_structure = structure.get_concrete_sqs([['Fe', 'Ni'], ['Al']])
    concrete_structure = structure.get_concrete_sqs([['Fe', 'Ni'], ['Al']])
    assert np.isclose(concrete_structure.volume, 445.35213050176463)
    assert np.isclose(concrete_structure.density, 4.122750000000001)

    structure = lat_in_to_sqs(ATAT_FCC_L12_LATTICE_IN)
    concrete_structure = structure.get_concrete_sqs([['Fe', 'Ni'], ['Al']], scale_volume=False)
    assert np.isclose(concrete_structure.volume, 8.0)


def test_sqs_is_properly_enumerated_for_a_higher_order_sublattice_model():
    """Tests that a sublattice model of higher order than an SQS properly enumerated"""
    structure = lat_in_to_sqs(ATAT_FCC_L12_LATTICE_IN)
    structures = enumerate_sqs(structure, [['Al', 'Ni'], ['Fe', 'Cr']], endmembers=False)
    assert len(structures) == 4

    structure = lat_in_to_sqs(ATAT_ROCKSALT_B1_LATTICE_IN)
    structures = enumerate_sqs(structure, [['Al', 'Ni'], ['Fe', 'Cr']], endmembers=True)
    assert len(structures) == 16

def test_sqs_is_properly_enumerated_for_a_multiple_solution_sublattice_model():
    """Tests that a sublattice model with multiple solution sublattices is properly enumerated"""
    structure = lat_in_to_sqs(ATAT_ROCKSALT_B1_LATTICE_IN)
    structures = enumerate_sqs(structure, [['Al', 'Ni'], ['Fe', 'Cr']], endmembers=False)
    assert len(structures) == 4

    structure = lat_in_to_sqs(ATAT_ROCKSALT_B1_LATTICE_IN)
    structures = enumerate_sqs(structure, [['Al', 'Ni'], ['Fe', 'Cr']], endmembers=True)
    assert len(structures) == 16
    assert all([isinstance(s, SQS) for s in structures])


def test_enumerating_sqs_with_lower_order_subl_raises():
    """If a lower order sublattice model is passed be enumerated in an SQS, it should raise."""
    structure = lat_in_to_sqs(ATAT_FCC_L12_LATTICE_IN)
    with pytest.raises(ValueError):
        enumerate_sqs(structure, [['Fe'], ['Al']])


def test_sqs_finds_correct_endmember_symmetry():
    """SQS shouldd correctly find endmember symmetry."""
    fcc_l12 = lat_in_to_sqs(ATAT_FCC_L12_LATTICE_IN)
    assert fcc_l12.get_endmember_space_group_info()[0] == 'Pm-3m'

    rocksalt_b1 = lat_in_to_sqs(ATAT_ROCKSALT_B1_LATTICE_IN)
    assert rocksalt_b1.get_endmember_space_group_info()[0] == 'Fm-3m'
