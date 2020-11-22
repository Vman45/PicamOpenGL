import time

class FPSCounter:
    def __init__(self, sec_interval=2.0, render_func=None):
        self.sec_interval = sec_interval
        self.render_func = render_func
        self._reset()

    def _reset(self):
        self.prev_time = time.time()
        self.count = 0

    def add(self):
        self.count += 1

    def render_fps(self):
        diff = time.time() - self.prev_time
        if (diff >= self.sec_interval):
            fps = self.count / diff
            self._reset()
            # None check
            if self.render_func:
                self.render_func(fps)

    def update_render(self, render_func):
        self.render_func = render_func