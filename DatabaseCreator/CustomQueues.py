from collections import deque


class Deque:
    def __init__(self, length):
        self.deque = deque([None for i in range(length)])

    def put(self, x):
        self.deque.rotate(-1)
        self.deque[-1] = x

    def get(self):
        x = self.deque[-1]
        self.deque[-1] = None
        self.deque.rotate(1)
        return x
