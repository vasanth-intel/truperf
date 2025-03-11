import time
import inspect
from common_libs.workload import Workload
from conftest import trd
from data.constants import *
from common_libs import utils

def read_perf_suite_config(test_instance, test_yaml_file, test_name):
    """
    Read the performance suite configuration from a YAML file and return it as a dictionary.
    """
    # Reading workload specific data.
    test_config_dict = {}
    yaml_test_config = utils.read_config_yaml(test_yaml_file)
    test_config_dict.update(yaml_test_config['Default'])

    # Updating config for test specific data.
    if yaml_test_config.get(test_name):
        test_config_dict.update(yaml_test_config[test_name])
        test_config_dict['test_name'] = test_name

    test_config_dict['vm_exec_modes'] = test_config_dict['vm_exec_modes'].split(",")

    print("\n-- Read the following Test Configuration Data : \n\n", test_config_dict)

    return test_config_dict

def run_test(test_instance, test_yaml_file):
    """
    Run a performance test based on the configuration provided in the YAML file.
    """
    global trd
    test_name = inspect.stack()[1].function
    print(f"\n********** Executing {test_name} **********\n")
    test_config_dict = read_perf_suite_config(test_instance, test_yaml_file, test_name)

    test_obj = Workload(test_config_dict)

    time_dict = {}
    trd[test_config_dict['workload_name']] = trd.get(test_config_dict['workload_name'], {})

    utils.copy_and_dump_vm_xml(test_config_dict)

    for vm_e_mode in test_config_dict['vm_exec_modes']:
        print(f"\n-- Executing {test_config_dict['test_name']} in {vm_e_mode} mode")
        
        vm_factory = utils.create_vm_factory(test_config_dict, vm_e_mode)
        vm_ssh_conn = utils.create_vm(test_config_dict, vm_factory, vm_e_mode)
        
        test_obj.pre_actions(vm_ssh_conn, test_config_dict)
        test_obj.setup_workload(vm_ssh_conn, test_config_dict)
 
        start_time = time.time()
        test_obj.execute_workload(vm_ssh_conn, test_config_dict, vm_e_mode)
        time_dict[vm_e_mode] = (time.time() - start_time) / 60
        trd[test_config_dict['workload_name']].update({test_config_dict['test_name']+'_time': time_dict})

        #vm_ssh_conn.close()
        #vm_factory.removeall()
        #del vm_factory

    test_obj.process_results(test_config_dict)

    os.chdir(FRAMEWORK_HOME_DIR)

    return True
