import signal

class GracefulExiter():
    def __init__(self):
        self.state = False
        signal.signal(signal.SIGINT, self.change_state)

    def change_state(self, signum, frame):
        print("Exit Flag set to True (repeat to exit now)")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.state = True

    def exit(self):
        return self.state