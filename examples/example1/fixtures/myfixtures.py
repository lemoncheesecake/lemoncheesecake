import lemoncheesecake.api as lcc

@lcc.fixture(scope="session_prerun")
def fixt0():
    pass 

@lcc.fixture(scope="session")
def fixt1(fixture_name, fixt0):
    return 1

@lcc.fixture(scope="session")
def fixt2():
    return 2

@lcc.fixture(scope="session")
def fixt3(fixt1, fixt2):
    """Some really usefull
    fixture
    """
    return fixt1 * fixt2

@lcc.fixture(scope="testsuite")
def fixt4():
    return 4

@lcc.fixture(scope="testsuite")
def fixt5(fixt4):
    return fixt4 + 1

@lcc.fixture(scope="testsuite")
def fixt6(fixt5, fixt1):
    return fixt5 * fixt1

@lcc.fixture(scope="test")
def fixt7():
    return 7

@lcc.fixture(scope="test")
def fixt8(fixt7, fixt6):
    return fixt7 * fixt6

@lcc.fixture(scope="test")
def fixt9(fixt8, fixt1):
    return fixt8 * fixt1

