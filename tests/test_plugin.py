import pytest
from pytest_valcov.plugin import pytest_addoption

class DummyParser:
    def __init__(self):
        self.options = []

    def getgroup(self, name, description):
        return self

    def addoption(self, *args, **kwargs):
        self.options.append((args, kwargs))

def test_pytest_addoption():
    parser = DummyParser()
    pytest_addoption(parser)
    
    option_names = []
    for args, kwargs in parser.options:
        option_names.extend(args)
        
    assert "--valcov" in option_names
    assert "--valcov-source" in option_names
    assert "--valcov-report" in option_names
