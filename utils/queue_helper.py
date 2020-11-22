import queue
import multiprocessing as mp

from utils.common import BaseNode

class QueueHelper(BaseNode):
    def __init__(self, maxsize=64):
        BaseNode.__init__(self)
        self.work_queue = queue.Queue(maxsize=maxsize)

    def put(self, entry):
        self.work_queue.put(entry)
    
    def get(self):
        return self.work_queue.get()

    def run(self, entry):
        self.put(entry)

class QueueHelperMp(QueueHelper):
    def __init__(self, maxsize=64):
        QueueHelper.__init__(self)
        self.work_queue = mp.Queue(maxsize=maxsize)