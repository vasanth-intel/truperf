import subprocess
import yaml
import shutil
import re
import uuid
from datetime import datetime as dt
import collections
from collections import defaultdict
import pandas as pd
from data.constants import *
from vmm_libs.vmguest import VMGuestFactory
from vmm_libs.vmguest import VirshSSH
from vmm_libs.vmparam import VMSpec
from vmm_libs.vmparam import (
    VM_TYPE_LEGACY,
    VM_TYPE_TD,
)

def exec_shell_cmd(cmd, stdout_val=subprocess.PIPE):
    """
    Execute a shell command and return the output.
    """
    try:
        cmd_stdout = subprocess.run([cmd], shell=True, check=True, stdout=stdout_val, stderr=subprocess.STDOUT, universal_newlines=True)

        if stdout_val is not None and cmd_stdout.stdout is not None:
            return cmd_stdout.stdout.strip()

        return cmd_stdout

    except subprocess.CalledProcessError as e:
        print(e.output)

def read_config_yaml(config_file_path):
    """
    Read a YAML configuration file and return the contents as a dictionary.
    """
    with open(config_file_path, "r") as config_fd:
        try:
            config_dict = yaml.safe_load(config_fd)
        except yaml.YAMLError as exc:
            raise Exception(exc)
    return config_dict

def create_vm_factory(test_config_dict, vm_e_mode):
    """
    Create a VM factory based on the execution mode (TD or LEGACY).
    """
    if vm_e_mode == "TD":
        assert test_config_dict['td_vm_image'] != '', "TD VM Image is not defined in workload yaml file.."
        vm_factory = VMGuestFactory(test_config_dict['td_vm_image'], test_config_dict['td_kernel'])
    elif vm_e_mode == "LEGACY":
        assert test_config_dict['legacy_vm_image'] != '', "Legacy VM Image is not defined in workload yaml file.."
        vm_factory = VMGuestFactory(test_config_dict['legacy_vm_image'], test_config_dict['legacy_kernel'])
    else:
        raise Exception(f"\n-- Unsupported VM type: {vm_e_mode}. Update the workload yaml with supported VM type.")

    return vm_factory

def create_vm(tcd, vm_factory, vm_e_mode):
    """
    Create and start a VM based on the execution mode (TD or LEGACY).
    """
    vm_memory = tcd['vm_memory'] * 1024 * 1024
    vm_spec_obj = VMSpec(sockets=1, cores = 2, threads=1, memsize=vm_memory)
    if vm_e_mode == "TD":
        vm_inst = vm_factory.new_vm(VM_TYPE_TD, vm_spec_obj)
    elif vm_e_mode == "LEGACY":
        vm_inst = vm_factory.new_vm(VM_TYPE_LEGACY, vm_spec_obj)
    else:
        raise Exception(f"\n-- Unsupported VM type: {vm_e_mode}. Update the workload yaml with supported VM type.")

    vm_inst.create()
    vm_inst.start()
    qm = VirshSSH(vm_inst)
    print("\n-- VM IP is: ", qm.vm_ip)
    return qm

def search_text_and_return_line_in_file(file_name, search_str):
    """
    Search for a text string in a file and return the lines containing the string.
    """
    with open(file_name, "r") as fp:
        return [line for line in fp if search_str.lower() in line or search_str.upper() in line or search_str.capitalize() in line]

def percent_degradation(tcd, baseline, testapp, throughput = False):
    """
    Calculate the percent degradation between baseline and test application results.
    """
    if float(baseline) == 0:
        return 0
    if 'throughput' in tcd['test_name'] or throughput:
        return '{:0.3f}'.format(100 * (float(baseline) - float(testapp)) / float(baseline))
    else:
        return '{:0.3f}'.format(100 * (float(testapp) - float(baseline)) / float(baseline))

def search_and_replace_in_file(file_path, vm_list):
    """
    Search and replace patterns in a file based on a list of patterns and replacements.
    """
    with open(file_path, 'r') as file:
        content = file.read()

    for xml_tag in vm_list:
        content = re.sub(xml_tag['pattern'], xml_tag['replace'], content)
    
    with open(file_path, 'w') as file:
        file.write(content)

def dump_vm_values_in_xml(tcd, file_path):
    """
    Dump VM values into an XML file based on the execution mode (TD or LEGACY).
    """
    vm_memory = tcd['vm_memory'] * 1024 * 1024
    if "tdx-base.xml" in file_path:
        vm_log_file_name = os.path.join(FRAMEWORK_LOG_DIR, "td_vm.log")
        td_list = [
            {"pattern": "<name>REPLACEME_NAME", "replace": f"<name>{tcd['td_domain_name']}"},
            {"pattern": "<uuid>REPLACEME_UUID", "replace": f"<uuid>{uuid.uuid4()}"},
            {"pattern": "<memory unit='KiB'>REPLACEME_MEMORY", "replace": f"<memory unit='KiB'>{vm_memory}"},
            {"pattern": "<loader>REPLACEME_OVMF_CODE", "replace": f"<loader type='rom' readonly='yes'>{tcd['td_vm_loader']}"},
            {"pattern": "<kernel>REPLACEME_KERNEL", "replace": f"<kernel>{tcd['td_kernel']}"},
            {"pattern": "<emulator>REPLACEME_QEMU", "replace": f"<emulator>/usr/bin/qemu-system-x86_64"},
            {"pattern": "<source file='REPLACEME_IMAGE'/>", "replace": f"<source file='{tcd['td_vm_image']}'/>"},
            {"pattern": "<log file='REPLACEME_LOG'/>", "replace": f"<log file='{vm_log_file_name}'/>"}
        ]
        search_and_replace_in_file(file_path, td_list)
    if "legacy-base.xml" in file_path:
        vm_log_file_name = os.path.join(FRAMEWORK_LOG_DIR, "legacy_vm.log")
        legacy_list = [
            {"pattern": "<name>REPLACEME_NAME", "replace": f"<name>{tcd['legacy_domain_name']}"},
            {"pattern": "<uuid>REPLACEME_UUID", "replace": f"<uuid>{uuid.uuid4()}"},
            {"pattern": "<memory unit='KiB'>REPLACEME_MEMORY", "replace": f"<memory unit='KiB'>{vm_memory}"},
            {"pattern": "<loader>REPLACEME_LOADER", "replace": f"<loader type='rom' readonly='yes'>{tcd['legacy_vm_loader']}"},
            {"pattern": "<kernel>REPLACEME_KERNEL", "replace": f"<kernel>{tcd['legacy_kernel']}"},
            {"pattern": "<emulator>REPLACEME_QEMU", "replace": f"<emulator>/usr/bin/qemu-system-x86_64"},
            {"pattern": "<source file='REPLACEME_IMAGE'/>", "replace": f"<source file='{tcd['legacy_vm_image']}'/>"},
            {"pattern": "<log file='REPLACEME_LOG'/>", "replace": f"<log file='{vm_log_file_name}'/>"}
        ]
        search_and_replace_in_file(file_path, legacy_list)

def copy_and_dump_vm_xml(tcd):
    """
    Copy and dump VM XML templates based on the execution modes defined in the test configuration dictionary.
    """
    if "TD" in tcd['vm_exec_modes']:
        src_file = os.path.join(FRAMEWORK_HOME_DIR, "data", "tdx-base.xml.template")
        dest_file = os.path.join(FRAMEWORK_HOME_DIR, "vmm_libs", "templates", "tdx-base.xml")
        shutil.copy2(src_file, dest_file)
        dump_vm_values_in_xml(tcd, dest_file)
    if "LEGACY" in tcd['vm_exec_modes']:
        src_file = os.path.join(FRAMEWORK_HOME_DIR, "data", "legacy-base.xml.template")
        dest_file = os.path.join(FRAMEWORK_HOME_DIR, "vmm_libs", "templates", "legacy-base.xml")
        shutil.copy2(src_file, dest_file)
        dump_vm_values_in_xml(tcd, dest_file)

def write_to_report(workload_name, test_results):
    """
    Write test results to an Excel report.
    """
    throughput_dict = collections.defaultdict(dict)
    latency_dict = collections.defaultdict(dict)
    time_dict = collections.defaultdict(dict)

    for k in test_results:
        if 'time' in k:
            time_dict[k] = test_results[k]
        elif 'throughput' in k:
            throughput_dict[k] = test_results[k]
        elif 'latency' in k:
            latency_dict[k] = test_results[k]

    now = dt.isoformat(dt.now()).replace(":","-").split('.')[0]
    report_name = os.path.join(PERF_RESULTS_DIR, workload_name.lower() + "_perf_data_" + now + ".xlsx")
    print(f"\n-- Writing Gramine performance results to {report_name}\n")
    if not os.path.exists(PERF_RESULTS_DIR): os.makedirs(PERF_RESULTS_DIR)
    if os.path.exists(report_name):
        writer = pd.ExcelWriter(report_name, engine='openpyxl', mode='a')
    else:
        writer = pd.ExcelWriter(report_name, engine='openpyxl')
    
    cols = ['LEGACY', 'TD', 'LEGACY-MED', 'TD-MED', 'TD-DEG']

    if len(throughput_dict) > 0:
        throughput_df = pd.DataFrame.from_dict(throughput_dict, orient='index', columns=cols).dropna(axis=1)
        throughput_df.columns = throughput_df.columns.str.upper()
        throughput_df.to_excel(writer, sheet_name=workload_name)

    if len(latency_dict) > 0:
        latency_df = pd.DataFrame.from_dict(latency_dict, orient='index', columns=cols).dropna(axis=1)
        latency_df.columns = latency_df.columns.str.upper()
        if len(throughput_dict) > 0:
            latency_df.to_excel(writer, sheet_name=workload_name, startcol=throughput_df.shape[1]+2)
        else:
            latency_df.to_excel(writer, sheet_name=workload_name)

    if len(time_dict) > 0:
        cols = ['LEGACY', 'TD',]
        time_df = pd.DataFrame.from_dict(time_dict, orient='index', columns=cols).dropna(axis=1)
        time_df.columns = time_df.columns.str.upper()
        time_df.to_excel(writer, sheet_name=workload_name+"_Time")

    writer._save()

def generate_performance_report(test_res_dict):
    """
    Generate a performance report for all workloads and tests.
    """
    print("\n###### In generate_performance_report #####\n")

    for workload, tests in test_res_dict.items():
        write_to_report(workload, tests)
