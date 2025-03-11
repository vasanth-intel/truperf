import os
import time
import glob
import statistics
from data.constants import *
from common_libs import utils
from conftest import trd


class RedisWorkload:
    def __init__(self, test_config_dict):
        """
        Initialize the RedisWorkload class with the test configuration dictionary.
        """
        # Initializing the class variables to None. They will be initialized later,
        # during workload setup once we would have the SSH connection handle of the VM.
        # Redis home dir => "/root/redis"
        #self.workload_home_dir = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['workload_home_dir'])
        self.workload_home_dir = None
        # Redis build dir => "/root/redis/redis-7.0.0"
        #self.workload_bld_dir = os.path.join(self.workload_home_dir, "redis-7.0.0")
        self.workload_bld_dir = None
        #self.server_ip_addr = utils.determine_host_ip_addr()
        self.server_ip_addr = None
        # Memtier benchmark dir => "/root/redis/memtier_benchmark"
        self.benchmark_dir = None
        self.command = None

    def get_workload_home_dir(self):
        """
        Return the workload home directory.
        """
        return self.workload_home_dir

    def download_workload(self, vm_ssh_conn):
        """
        Download and extract the Redis workload from the source.
        """
        # We would not install if the installation dir already exists.
        # if os.path.exists(self.workload_bld_dir):
        #     print("\n-- Redis already downloaded. Not fetching from source..")
        #     return True
        print("\n###### In download_workload #####\n")
        tar_file_name = os.path.basename(REDIS_DOWNLOAD_CMD.split()[5])
        untar_cmd = "tar xzf " + self.workload_home_dir + "/" + tar_file_name + " -C " + self.workload_home_dir

        print("\n-- Fetching and extracting Redis workload from source..")
        stdout, stderr = vm_ssh_conn.check_exec('printenv')
        print(stdout)
        vm_ssh_conn.check_exec(REDIS_DOWNLOAD_CMD)
        vm_ssh_conn.check_exec(untar_cmd)
        time.sleep(2)

    def build_and_install_workload(self, vm_ssh_conn, test_config_dict):
        """
        Build and install the Redis workload.
        """
        print("\n###### In build_and_install_workload #####\n")

        redis_bld_cmd = f"make -C {self.workload_bld_dir}"
        print(f"\n-- Building redis workload..\n", redis_bld_cmd)
        stdout, stderr = vm_ssh_conn.check_exec(redis_bld_cmd)
        redis_make_log_file = FRAMEWORK_LOG_DIR + "/redis_" + test_config_dict['test_name'] + '_make.log'
        utils.exec_shell_cmd(f"echo \"{stdout}\" > {redis_make_log_file}")
        utils.exec_shell_cmd(f"echo \"stderr logs start from here..\" >> {redis_make_log_file}")
        utils.exec_shell_cmd(f"echo \"{stderr}\" >> {redis_make_log_file}")
        failure_line = utils.search_text_and_return_line_in_file(redis_make_log_file, 'fail')
        if failure_line:
            raise Exception("\n-- Failure during building of workload as shown below..", failure_line)
        time.sleep(2)
            
    def copy_server_binary(self, vm_ssh_conn):
        """
        Copy the Redis server binary to the workload home directory.
        """
        redis_binary = os.path.join(self.workload_bld_dir, "src", "redis-server")
        stdout, stderr = vm_ssh_conn.check_exec(f"cp {redis_binary} {self.workload_home_dir}")

    def update_server_details_in_benchmark(self, vm_ssh_conn, tcd):
        """
        Update the server details in the benchmark script.
        """
        home_dir = os.path.expanduser("~")
        benchmark_file_path = os.path.join(FRAMEWORK_HOME_DIR, "benchmark_libs", "instance_benchmark.sh")

        # Updating Server IP.
        host_sed_cmd = f"sed -i 's/^export HOST.*/export HOST=\"{vm_ssh_conn.vm_ip}\"/' {benchmark_file_path}"
        print("\n-- Updating server IP within redis client script..")
        utils.exec_shell_cmd(host_sed_cmd, None)

        # Updating Server Port.
        # Client scripts are incrementing the port value and then using the result as server port.
        # Hence decreasing the port value by one to replace within the client script.
        port = tcd['server_port'] - 1
        port_sed_cmd = f"sed -i 's/^export MASTER_START_PORT.*/export MASTER_START_PORT=\"{str(port)}\"/' {benchmark_file_path}"
        print("\n-- Updating server Port within redis client script..")
        utils.exec_shell_cmd(port_sed_cmd, None)
        benchmark_wrapper_path = os.path.join(FRAMEWORK_HOME_DIR, "benchmark_libs", "start_benchmark.sh")
        print("\n-- Copying benchmarking libs within VM..")
        utils.exec_shell_cmd(f"sshpass -p '123456' scp -T -o StrictHostKeyChecking=no {benchmark_file_path} root@{vm_ssh_conn.vm_ip}:{self.workload_home_dir}", None)
        utils.exec_shell_cmd(f"sshpass -p '123456' scp -T -o StrictHostKeyChecking=no {benchmark_wrapper_path} root@{vm_ssh_conn.vm_ip}:{self.workload_home_dir}", None)
        # Make the benchmark shell scripts to be executable within the VM.
        benchmark_file = os.path.join(self.workload_home_dir, "instance_benchmark.sh")
        benchmark_wrapper = os.path.join(self.workload_home_dir, "start_benchmark.sh")
        vm_ssh_conn.check_exec(f"chmod +x {benchmark_file}")
        vm_ssh_conn.check_exec(f"chmod +x {benchmark_wrapper}")

    def setup_redis_server(self, vm_ssh_conn):
        """
        Set up the Redis server with the necessary OS parameters.
        """
        print("\n###### In setup_redis_server #####\n")
        print("\n-- Setting up server OS parameters ...")
        stdout, stderr = vm_ssh_conn.check_exec('which echo')
        echo_cmd_path = stdout.rstrip()
        
        print("\n-- Setting Huge pages - Never..")
        vm_ssh_conn.check_exec(f"sudo sh -c '{echo_cmd_path} never > /sys/kernel/mm/transparent_hugepage/enabled'")
        print("\n-- Setting Overcommit_memory -> 1..")
        vm_ssh_conn.check_exec(f"sudo sh -c '{echo_cmd_path} 1 -> /proc/sys/vm/overcommit_memory'")
        print("\n-- Clearing cache -> 3..")
        vm_ssh_conn.check_exec(f"sudo sh -c '{echo_cmd_path} 3 -> /proc/sys/vm/drop_caches'")
        print("\n-- Setting max number of connections -> 65K..")
        vm_ssh_conn.check_exec("sudo sysctl -w net.core.somaxconn=65535 > /dev/null")
        print("\n-- Disabling swap memory..")
        vm_ssh_conn.check_exec("sudo swapoff -a")
        
        time.sleep(2)

    # Setting the proxy is not working across vm exec calls.
    # But keeping it now, to make modifications later once working
    # solution is found.
    # Note that git proxy is working across vm exec calls. Hence,
    # not commenting out the function.
    def set_http_proxy(self, vm_ssh_conn):
        """
        Set the HTTP and HTTPS proxies for the VM.
        """
        print("\n-- Setting http and https proxies..")
        vm_ssh_conn.check_exec(f"echo http_proxy={HTTP_PROXY} >> /etc/environment")
        vm_ssh_conn.check_exec(f"echo https_proxy={HTTPS_PROXY} >> /etc/environment")
        vm_ssh_conn.check_exec('source /etc/environment')
        vm_ssh_conn.check_exec(f"echo -e 'Acquire::http::proxy \"{HTTP_PROXY}\";\nAcquire::https::proxy \"{HTTPS_PROXY}\";' > /etc/apt/apt.conf.d/tdx_proxy")
        vm_ssh_conn.check_exec(f"export http_proxy={HTTP_PROXY}")
        vm_ssh_conn.check_exec(f"export https_proxy={HTTPS_PROXY}")
        vm_ssh_conn.check_exec(f"git config --global http.proxy http://proxy-dmz.intel.com:911")
        vm_ssh_conn.check_exec(f"git config --global https.proxy http://proxy-dmz.intel.com:912")

    def download_and_build_benchmark(self, vm_ssh_conn, tcd):
        """
        Download and build the Memtier benchmark.
        """
        print("\n###### In download_and_build_benchmark #####\n")
        print("\n-- Downloading memtier benchmark..")
        memtier_tag_cmd = "git -c 'versionsort.suffix=-' ls-remote --exit-code --refs --sort='version:refname' --tags \
            https://github.com/RedisLabs/memtier_benchmark.git '*.*.*' | tail --lines=1 | cut --delimiter='/' --fields=3"
        memtier_latest_tag = utils.exec_shell_cmd(memtier_tag_cmd)
        memtier_clone_cmd = f"git clone --depth 1 --branch {memtier_latest_tag} https://github.com/RedisLabs/memtier_benchmark.git {self.benchmark_dir}"
        vm_ssh_conn.check_exec(memtier_clone_cmd)

        # Below update is necessary for Memtier benchmark pre-requisites to get installed successfully.
        print("\n-- Running apt-get update..")
        vm_ssh_conn.check_exec("sudo apt-get update")
        print("\n-- Installing memtier benchmark pre-requisites..")
        vm_ssh_conn.check_exec("sudo apt-get install -y build-essential autoconf automake libpcre3-dev  libevent-dev pkg-config zlib1g-dev libssl-dev rename")
        print("\n-- Building memtier benchmark..")
        vm_ssh_conn.check_exec(f"cd {self.benchmark_dir} && autoreconf -ivf")
        vm_ssh_conn.check_exec(f"cd {self.benchmark_dir} && ./configure")
        stdout, stderr = vm_ssh_conn.check_exec(f"cd {self.benchmark_dir} && make")
        benchmark_make_log_file = FRAMEWORK_LOG_DIR + "/memtier_benchmark_" + tcd['test_name'] + '_make.log'
        utils.exec_shell_cmd(f"echo \"{stdout}\" > {benchmark_make_log_file}")
        utils.exec_shell_cmd(f"echo \"stderr logs start from here..\" >> {benchmark_make_log_file}")
        utils.exec_shell_cmd(f"echo \"{stderr}\" >> {benchmark_make_log_file}")
        failure_line = utils.search_text_and_return_line_in_file(benchmark_make_log_file, 'fail')
        if failure_line:
            raise Exception("\n-- Failure during building of benchmark as shown below..", failure_line)
        time.sleep(2)

    def pre_actions(self, vm_ssh_conn, test_config_dict):
        """
        Perform pre-actions before setting up the workload.
        """
        stdout, stderr = vm_ssh_conn.check_exec('pwd')
        self.workload_home_dir = os.path.join(stdout.rstrip(), "redis")
        self.workload_bld_dir = os.path.join(self.workload_home_dir, "redis-7.0.0")
        self.benchmark_dir = os.path.join(self.workload_home_dir, "memtier_benchmark")
        print("\n-- Workload home directory: ", self.workload_home_dir)
        print("\n-- Workload build directory: ", self.workload_bld_dir)
        print("\n-- Benchmark directory: ", self.benchmark_dir)
        vm_ssh_conn.check_exec(f"mkdir -p {self.workload_home_dir}")
        vm_ssh_conn.check_exec(f"mkdir -p {self.benchmark_dir}")
        self.set_http_proxy(vm_ssh_conn)
        self.setup_redis_server(vm_ssh_conn)
        self.update_server_details_in_benchmark(vm_ssh_conn, test_config_dict)

    def setup_workload(self, vm_ssh_conn, test_config_dict):
        """
        Set up the Redis workload by downloading, building, and installing it.
        """
        self.download_workload(vm_ssh_conn)
        self.build_and_install_workload(vm_ssh_conn, test_config_dict)
        self.copy_server_binary(vm_ssh_conn)
        self.download_and_build_benchmark(vm_ssh_conn, test_config_dict)

    def construct_server_workload_exec_cmd(self, test_config_dict):
        """
        Construct the command to execute the Redis server workload.
        """
        redis_exec_cmd = None

        server_size = test_config_dict['server_size'] * 1024 * 1024 * 1024
        server_binary = os.path.join(self.workload_home_dir, 'redis-server')

        redis_exec_cmd = f"{server_binary} --daemonize yes --port {test_config_dict['server_port']} --maxmemory {server_size} --maxmemory-policy allkeys-lru --appendonly no --protected-mode no --save ''"
        
        return redis_exec_cmd

    def free_redis_server_port(self, vm_ssh_conn, tcd):
        """
        Free the Redis server port by killing the process running on it.
        """
        lsof_cmd = f"lsof -t -i:{tcd['server_port']}"
        stdout, stderr = vm_ssh_conn.check_exec(lsof_cmd)
        process_id = stdout.rstrip()
        print(f"\n-- Killing server process {process_id} running on port {tcd['server_port']}")
        if process_id is not None:
            kill_cmd = f"kill -9 {process_id}"
            print(kill_cmd)
            vm_ssh_conn.check_exec(kill_cmd)

    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, vm_ssh_conn, tcd, e_mode):
        """
        Execute the Redis server workload and run the Memtier benchmark.
        """
        print("\n##### In execute_workload #####\n")

        print(f"\n-- Executing {tcd['test_name']} in {e_mode} mode")

        self.command = self.construct_server_workload_exec_cmd(tcd)
        print("\n-- Launching Redis server with below command..\n", self.command)

        # Bring up the redis server.
        stdout, stderr = vm_ssh_conn.check_exec(self.command)
        if 'fail' in stdout or 'Fail' in stdout:
            raise Exception("\n-- Failed to launch redis server within the VM!! Exiting.. ")
        time.sleep(5)

        # Construct and execute memtier benchmark command within client.
        benchmark_exec_cmd = f"cd {self.workload_home_dir} && ./start_benchmark.sh {e_mode} {tcd['test_name']} {tcd['data_size']} {tcd['rw_ratio']} {tcd['iterations']}"
        print("\n-- Invoking Memtier benchmarkas below..\n", benchmark_exec_cmd)

        stdout, stderr = vm_ssh_conn.check_exec(benchmark_exec_cmd)
        print(stdout)
        time.sleep(5)

        self.free_redis_server_port(vm_ssh_conn, tcd)

        csv_res_folder = os.path.join(PERF_RESULTS_DIR, tcd['workload_name'], tcd['test_name'])
        os.makedirs(csv_res_folder, exist_ok=True)

        # Copy test results folder from client to local server results folder.
        client_res_folder = os.path.join(tcd['client_results_path'], tcd['test_name'])
        utils.exec_shell_cmd(f"sshpass -p '123456' scp -T -o StrictHostKeyChecking=no root@{vm_ssh_conn.vm_ip}:{client_res_folder}/* {csv_res_folder}", None)

    def process_results(self, tcd):
        """
        Process the results of the Redis workload and update the global test results dictionary.
        """
        # Parse the individual csv result files and update the global test results dict.
        csv_test_res_folder = os.path.join(PERF_RESULTS_DIR, tcd['workload_name'], tcd['test_name'])
        os.chdir(csv_test_res_folder)
        csv_files = glob.glob1(csv_test_res_folder, "*.csv")
        
        if len(csv_files) != (len(tcd['vm_exec_modes']) * tcd['iterations']):
            raise Exception(f"\n-- Number of test result files - {len(csv_files)} is not equal to the expected number - {len(tcd['vm_exec_modes']) * tcd['iterations']}.\n")

        global trd
        test_dict_throughput = {}
        test_dict_latency = {}
        for e_mode in tcd['vm_exec_modes']:
            test_dict_throughput[e_mode] = []
            test_dict_latency[e_mode] = []
        
        avg_latency = 0
        avg_throughput = 0
        for filename in csv_files:
            with open(filename, "r") as f:
                for row in f.readlines():
                    row = row.split()
                    if row:
                        if "Totals" in row[0]:
                            avg_latency = row[4]
                            avg_throughput = row[-1]
                            break

                if "LEGACY" in filename:
                    test_dict_latency['LEGACY'].append(float(avg_latency))
                    test_dict_throughput['LEGACY'].append(float(avg_throughput))
                elif "TD" in filename:
                    test_dict_latency['TD'].append(float(avg_latency))
                    test_dict_throughput['TD'].append(float(avg_throughput))
                else:
                    raise Exception("\n-- Invalid VM execution mode found in result files. Exiting and not generating any report!!")

        if 'LEGACY' in tcd['vm_exec_modes']:
            test_dict_latency['LEGACY-MED'] = '{:0.3f}'.format(statistics.median(test_dict_latency['LEGACY']))
            test_dict_throughput['LEGACY-MED'] = '{:0.3f}'.format(statistics.median(test_dict_throughput['LEGACY']))

        if 'TD' in tcd['vm_exec_modes']:
            test_dict_latency['TD-MED'] = '{:0.3f}'.format(statistics.median(test_dict_latency['TD']))
            test_dict_throughput['TD-MED'] = '{:0.3f}'.format(statistics.median(test_dict_throughput['TD']))
            if 'LEGACY' in tcd['vm_exec_modes']:
                test_dict_latency['TD-DEG'] = utils.percent_degradation(tcd, test_dict_latency['LEGACY-MED'], test_dict_latency['TD-MED'])
                test_dict_throughput['TD-DEG'] = utils.percent_degradation(tcd, test_dict_throughput['LEGACY-MED'], test_dict_throughput['TD-MED'], True)

        trd[tcd['workload_name']] = trd.get(tcd['workload_name'], {})
        trd[tcd['workload_name']].update({tcd['test_name']+'_latency': test_dict_latency})
        trd[tcd['workload_name']].update({tcd['test_name']+'_throughput': test_dict_throughput})

        os.chdir(FRAMEWORK_HOME_DIR)
