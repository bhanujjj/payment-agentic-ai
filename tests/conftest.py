import pytest
from simulation.routing_config import reset_routing

@pytest.fixture(autouse=True)
def run_around_tests():
    # Reset before test runs
    reset_routing()
    yield
    # Reset after test runs
    reset_routing()
