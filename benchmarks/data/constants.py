import os
import psutil

# if "PYTEST_CURRENT_TEST" in os.environ:
#     print("came in if")
#     FRAMEWORK_HOME_DIR = os.getcwd()
# else:
#     print("came in else")
#     FRAMEWORK_HOME_DIR = os.getcwd() + "/benchmarks"

# if "pytest" in sys.modules:
#     print("came in if")
#     FRAMEWORK_HOME_DIR = os.getcwd()
# else:
#     print("came in else")
#     FRAMEWORK_HOME_DIR = os.getcwd() + "/benchmarks"

# FRAMEWORK_HOME_DIR = os.getcwd() + "/benchmarks"
# @pytest.hookimpl()
# def pytest_sessionstart(session):
#     FRAMEWORK_HOME_DIR = os.getcwd()

process = psutil.Process(os.getpid())
process_name = process.name()
print("Process name is", process_name)
if process_name == "pytest":
    FRAMEWORK_HOME_DIR = os.getcwd()
else:
    FRAMEWORK_HOME_DIR = os.getcwd() + "/benchmarks"

FRAMEWORK_LOG_DIR = FRAMEWORK_HOME_DIR + "/logs"

HTTP_PROXY = "http://proxy-dmz.intel.com:911"

HTTPS_PROXY = "http://proxy-dmz.intel.com:912"

PERF_RESULTS_DIR = FRAMEWORK_HOME_DIR + "/results"

REDIS_DOWNLOAD_CMD = "wget -e use_proxy=yes -e https_proxy=proxy-dmz.intel.com:912 https://github.com/antirez/redis/archive/7.0.0.tar.gz -P /root/redis"
#REDIS_DOWNLOAD_CMD = "wget https://github.com/antirez/redis/archive/7.0.0.tar.gz -P /root/redis"
