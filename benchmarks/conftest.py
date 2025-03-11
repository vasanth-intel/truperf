import os
import sys
import shutil
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from collections import defaultdict
from data.constants import *

print(sys.path)

# Global dictionary to hold the results of all the tests in the following format.
# Tests_results_dictionary (trd)
# {
#   Workload_name1:
#       { test_name1: {native:[], direct:[], sgx:[], native-avg, direct-avg, sgx-avg, direct_degradation, sgx_degradation} }
#       { test_name2: {native:[], direct:[], sgx:[], native-avg, direct-avg, sgx-avg, direct_degradation, sgx_degradation} }
#   Workload_name2:
#       { test_name1: {native:[], direct:[], sgx:[], native-avg, direct-avg, sgx-avg, direct_degradation, sgx_degradation} }
#       { test_name2: {native:[], direct:[], sgx:[], native-avg, direct-avg, sgx-avg, direct_degradation, sgx_degradation} }
#  }
trd = defaultdict(dict)

if os.path.exists(FRAMEWORK_LOG_DIR):
    shutil.rmtree(FRAMEWORK_LOG_DIR)
os.makedirs(FRAMEWORK_LOG_DIR)
if os.path.exists(PERF_RESULTS_DIR):
    shutil.rmtree(PERF_RESULTS_DIR)
os.makedirs(PERF_RESULTS_DIR)
