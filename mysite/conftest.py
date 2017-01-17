import pytest


def pytest_addoption(parser):
    parser.addoption('--run-slow', action='store_true',
                     default=False,
                     help="Run slow tests")


def pytest_runtest_setup(item):
    if ('slowtest' in item.keywords and
            (not item.config.getoption('--run-slow'))):
        pytest.skip('Need --run-slow to run')
