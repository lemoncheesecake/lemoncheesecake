from lemoncheesecake.testsuite import *
from lemoncheesecake.runtime import *
from lemoncheesecake.checkers import *
from lemoncheesecake.worker import Worker

worker = None
def set_worker(wrk):
    global worker
    worker = wrk