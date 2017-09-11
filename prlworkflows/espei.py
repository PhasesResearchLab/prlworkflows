from fireworks import Workflow, Firework, FiretaskBase

from atomate.common.firetasks.glue_tasks import CopyFiles, PassCalcLocs
class PRLESPEISet():
    """
    Write input files for ESPEI from a dictionary
    """
    pass


class RunEspeiTask(FiretaskBase):
    def run_task(self, fw_spec):
        # actually run the espei executable, passing in the parameters
        pass


class ParseEspeiOutputsTask(FiretaskBase):
    def run_task(self, fw_spec):
        # parse the results and concatenate
        pass



class EspeiFW(Firework):
    def __init__(self, fit_settings, input_set=None, restart_from_prev_run=False, name='Run ESPEI', parents=None, **kwargs):
        tasks = []
        tasks.append(CopyFiles()) ## TODO add settings
        tasks.append(RunEspeiTask())
        tasks.append(ParseEspeiOutputsTask())
        tasks.append(PassCalcLocs())

        super(EspeiFW, self).__init__(tasks, parents=parents,
                                         name='{} - {}'.format('-'.join(fit_settings['components'], name)), **kwargs)


def get_espei_wf(fit_settings, input_set=None, total_steps=1e4, steps_per_run=1e3):
    from math import ceil
    number_fireworks =  ceil(total_steps/steps_per_run)

    input_set = input_set or PRLESPEISet()

    fws = [EspeiFW(fit_settings, input_set=PRLESPEISet)]

    for parent_idx in number_fireworks - 1:
        fws.append(EspeiFW(fit_settings, input_set=PRLESPEISet, restart_from_prev_run=True, parents=fws[parent_idx]))

    return Workflow(fws)


