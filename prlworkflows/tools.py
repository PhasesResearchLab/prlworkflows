import os

from custodian.custodian import Custodian
from custodian.vasp.jobs import VaspJob
from custodian.vasp.handlers import VaspErrorHandler, MeshSymmetryErrorHandler, UnconvergedErrorHandler, \
     NonConvergingErrorHandler, PotimErrorHandler, \
     PositiveEnergyErrorHandler, FrozenJobErrorHandler, StdErrHandler
from custodian.vasp.validators import VasprunXMLValidator, VaspFilesValidator

def run_vasp_custodian(input_set, dir=None):
    """
    Runs VASP for a given input set.

    Parameters
    ----------
    input_set : pymatgen.io.vasp.sets.VaspInputSet
        A single input set or a list of inputs
    dir :

    Returns
    -------

    """
    # use `dir` or make a temporary directory
    input_set.write_input(dir, make_dir_if_not_present=True)
    start_dir = os.path.abspath(os.curdir)
    os.chdir(dir)
    error_handlers = [VaspErrorHandler(), MeshSymmetryErrorHandler(), UnconvergedErrorHandler(),
                      NonConvergingErrorHandler(), PotimErrorHandler(),
                      PositiveEnergyErrorHandler(), FrozenJobErrorHandler(), StdErrHandler()]
    validators = [VasprunXMLValidator(), VaspFilesValidator()]
    vasp_job = [VaspJob(['vasp_std'], backup=False)]
    custodian = Custodian(error_handlers, vasp_job, validators=validators)
    custodian.run()
    os.chdir(start_dir)
