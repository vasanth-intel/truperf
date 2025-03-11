import os
import pytest
from data.constants import *
from common_libs.truperf_runner import run_test
from common_libs import utils
from conftest import trd

# Define the YAML file name and path for the test inputs
yaml_file_name = "redis_perf_inputs.yaml"
tests_yaml_path = os.path.join(FRAMEWORK_HOME_DIR, 'data', yaml_file_name)

@pytest.fixture(scope="session")
def pytest_report_gen(request):
    """
    Pytest fixture to generate a performance report at the end of the test session.
    """
    global trd
    print("\n-- In pytest_report_gen\n")
    yield
    # Generate the report using the global results dict.
    utils.generate_performance_report(trd)

@pytest.mark.usefixtures("pytest_report_gen")
class TestClass:
    """
    Test class containing Redis performance test cases with different data sizes and read/write ratios.
    """
    # The return statements returning value of '5' in all below tests is for ASV purpose
    # where the track function needs to return a value for ASV to track. This return value
    # should ideally be the degradation percentage. Parsing the degradation percentage from
    # the results is not implemented yet. Hence, returning some dummy value here.
    @pytest.mark.redis_perf
    @pytest.mark.redis_perf_1024_data_size
    def track_redis_perf_1024_data_size_1_1_rw_ratio(self):
        """
        Test Redis performance with 1024 data size and 1:1 read/write ratio.
        """
        test_result = run_test(self, tests_yaml_path)
        assert test_result
        # Return a dummy value for ASV tracking purposes.
        return 5

    @pytest.mark.redis_perf
    @pytest.mark.redis_perf_1024_data_size
    def track_redis_perf_1024_data_size_1_9_rw_ratio(self):
        """
        Test Redis performance with 1024 data size and 1:9 read/write ratio.
        """
        test_result = run_test(self, tests_yaml_path)
        assert test_result
        # Return a dummy value for ASV tracking purposes.
        return 5

    @pytest.mark.redis_perf
    @pytest.mark.redis_perf_8192_data_size
    def track_redis_perf_8192_data_size_1_1_rw_ratio(self):
        """
        Test Redis performance with 8192 data size and 1:1 read/write ratio.
        """
        test_result = run_test(self, tests_yaml_path)
        assert test_result
        # Return a dummy value for ASV tracking purposes.
        return 5

    @pytest.mark.redis_perf
    @pytest.mark.redis_perf_8192_data_size
    def track_redis_perf_8192_data_size_1_9_rw_ratio(self):
        """
        Test Redis performance with 8192 data size and 1:9 read/write ratio.
        """
        test_result = run_test(self, tests_yaml_path)
        assert test_result
        # Return a dummy value for ASV tracking purposes.
        return 5
