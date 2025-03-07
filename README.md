
# Truperf Framework

Truperf framework is a performance benchmarking automation framework for legacy and customized virtual machines (VMs) with a focus on running workloads and generating performance reports.

## Description:
This project is designed to automate the process of setting up VMs, running workloads, and generating performance reports, making it easier to benchmark and analyze the performance of different configurations and workloads. The project is structured into several directories and files, each serving a specific purpose. Down below is an overview of the key components.

## Infrastructure:

- System: `Intel Xeon Processor with TME and SGX BIOS knobs enabled`
- Operating System: `Ubuntu 24.04`
- Architecture: `x86_64`

## Pre-requisites:
- Following system dependencies would also be required:

    `python3-pip` `python3-pytest` `python3-virtualenv` `python3-psutil` `python3-paramiko` `python3-cpuinfo` `python3-pandas`

## Installation:

This is a pytest based project which can be executed using ASV (AirSpeed Velocity) as well, to track the performance degradations. The performance benchmarking is performed under python virtual environment. So, python virtual environment must be created and activated before starting the performance benchmarking process. Further, the framework takes inputs from a YAML file present within data folder as seen in below directory structure. We need to ensure that the YAML file is populated with right paths and values for the successful end-to-end execution of the framework.

## Project Structure:

```
├── asv.conf.json
└── benchmarks
    ├── benchmark_libs
    │   ├── instance_benchmark.sh
    │   └── start_benchmark.sh
    ├── common_libs
    │   ├── truperf_runner.py
    │   ├── utils.py
    │   └── workload.py
    ├── conftest.py
    ├── data
    │   ├── constants.py
    │   ├── legacy-base.xml.template
    │   ├── redis_perf_inputs.yaml
    │   └── tdx-base.xml.template
    ├── __init__.py
	├── logs
    ├── pytest.ini
    ├── README.md
	├── results
    ├── test_redis_perf.py
    ├── vmm_libs
    │   ├── cmdrunner.py
    │   ├── dut.py
    │   ├── templates
    │   ├── virtxml.py
    │   ├── vmguest.py
    │   ├── vmimg.py
    │   ├── vmm.py
    │   └── vmparam.py
    └── workloads
        ├── __init__.py
        └── redis_workload.py
```

## Project Structure Description:

benchmark_libs/: Contains scripts for benchmarking.
 - instance_benchmark.sh
 - start_benchmark.sh

common_libs/: Contains common libraries and utilities used across the project.
 - truperf_runner.py: Framework wrapper that manages the execution of performance tests.
 - utils.py: Provides utility functions for executing shell commands, reading YAML configurations, creating VMs, and generating performance reports.
 - workload.py: Defines the base Workload class and its methods.

conftest.py: Standard pytest file updating the system path ensuring the framework can be executed with both pytest and ASV.

data/: Contains configuration files and templates.
 - constants.py: Defines constants used throughout the project.
 - legacy-base.xml.template: This file will be used to generate an xml file needed for VM creation. It will be copied to 'vmm_libs/templates' folder after updating the user inputs present in YAML file.
 - redis_perf_inputs.yaml: This is the file where the framework reads the user/workload inputs from.
 - tdx-base.xml.template: This file will be used to generate an xml file needed for VM creation. It will be copied to 'vmm_libs/templates' folder after updating the user inputs present in YAML file.

logs/: Contains workload and framework logs.

results/: Contains the individual workload results along with the summarized workload's performance report.

vmm_libs/: Contains libraries related to VM creation, destruction and other management functions.
 - cmdrunner.py: Run native command which managed by standalone thread.
 - dut.py: Manange DUT (Device Under Test) device.
 - virtxml.py: Virt XML class to manage the setting via XML dom.
 - vmguest.py: VM Guest instance with VM customization.
 - vmimg.py: Manage/Customize the VM image via virt-customize tools.
 - vmm.py: Virtual Machine Manager implementation defining common interfacts like create/destroy/suspend/resume.
 - vmparam.py: VM params package manages the several parameters' class for guest VM.

workloads/: Contains workload-specific implementations.
 - redis_workload.py: Implements the RedisWorkload class for setting up and running Redis workload.

test_redis_perf.py: Contains test cases for Redis performance benchmarking.

## Quick Start

Truperf framework is built such that we can get the performance data either using Pytest or via ASV framework. Before execution, please ensure teh dependencies of the framework are installed as mentioned within the `Pre-requisites` and `Installation` sections. Following are few quick steps to execute a workload using Pytest and ASV.

Execution via Pytest:

1. Clone Truperf framework repository.
`git clone https://github.com/vasanth-intel/truperf.git`

2. Change directory to the 'benchmarks' directory within the above cloned framework directory.
`cd truperf/benchmarks`
	
3. Execute the framework using the following command.
`python3 -m pytest -s -v -m workload_name_or_test_name --disable-warnings`
		
`workload_name_or_test_name` is the marker of workload or the test as specified in the respective workload test script.

Execution via ASV:

1. Install ASV within the python virtual environment via pip: `pip install asv`.

2. Clone Truperf framework repository.
`git clone https://github.com/vasanth-intel/truperf.git`

3. Change directory to the above cloned framework directory.
`cd truperf`

4. Set up the benchmarking project by referring the section `Setting up a new benchmarking project` present in https://asv.readthedocs.io/en/latest/using.html.

5. Run the benchmark using the command `asv run` or `asv run -e`.

