import copy

import pytest

from cgwn.config import load_config


@pytest.fixture(scope="session")
def cfg():
    return load_config("configs/default.yaml")


@pytest.fixture()
def cfg_copy(cfg):
    return copy.deepcopy(cfg)
