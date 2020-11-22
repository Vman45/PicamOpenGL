class ResultMsg():
    def __init__(self, buf, result):
        self.buf = buf
        self.result = result
    
    def get_buf(self):
        return self.buf
    
    def get_result(self):
        return self.result