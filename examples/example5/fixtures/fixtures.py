import lemoncheesecake.api as lcc

@lcc.fixture(scope="pre_run")
def fixt_1():
    pass

@lcc.fixture(scope="session")
def fixt_2(fixt_1):
    pass

@lcc.fixture(scope="session")
def fixt_3():
    pass

@lcc.fixture(scope="suite")
def fixt_4(fixt_3):
    pass

@lcc.fixture(scope="suite")
def fixt_5():
    pass

@lcc.fixture(scope="suite")
def fixt_6(fixt_3):
    pass

@lcc.fixture(scope="test")
def fixt_7(fixt_6, fixt_2):
    pass

@lcc.fixture(scope="test")
def fixt_8():
    pass

@lcc.fixture(scope="test")
def fixt_9():
    pass

