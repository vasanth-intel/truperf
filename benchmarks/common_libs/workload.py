import os
import workloads as tdx_perf_workloads

class Workload(object):
    """
    Base class for all workloads. Generic actions are taken here.
    All workload specific actions would be implemented in the respective
    derived workload class.
    """
    def __init__(self,
                 test_config_dict):
        self.name = test_config_dict['workload_name']
        self.command = None
        workload_script = test_config_dict['workload_name'] + "Workload"
        self.workload_class = getattr(globals()["tdx_perf_workloads"], workload_script)
        print(self.workload_class)
        self.workload_obj = self.workload_class(test_config_dict)

    def pre_actions(self, vm_ssh_conn, test_config_dict):
        """
        Performs pre-actions for the workload.
        :param test_config_dict: Test config data
        :return:
        """
        self.workload_obj.pre_actions(vm_ssh_conn, test_config_dict)

    # setup_workload - implement in a subclass if needed
    def get_workload_home_dir(self):
        return self.workload_obj.get_workload_home_dir()

    # setup_workload - implement in a subclass if needed
    def setup_workload(self, vm_ssh_conn, test_config_dict):
        return self.workload_obj.setup_workload(vm_ssh_conn, test_config_dict)

    # execute_workload - implement in a subclass if needed
    def execute_workload(self, vm_ssh_conn, test_config_dict, e_mode):
        self.workload_obj.execute_workload(vm_ssh_conn, test_config_dict, e_mode)

    # process_results - implement in a subclass if needed
    def process_results(self, test_config_dict):
        self.workload_obj.process_results(test_config_dict)
