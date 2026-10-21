# SPDX-License-Identifier: GPL-3.0-only
"""Short-lived bounded metadata cache; never caches errors or open decisions."""
from collections import OrderedDict
import time


class Cache:
    def __init__(self, ttl=1.0, capacity=16000, clock=time.monotonic):
        self.ttl, self.capacity, self.clock = ttl, capacity, clock
        self.items = OrderedDict()
        self.weight = 0

    def get(self, key):
        item = self.items.get(key)
        if item is None:
            return False, None
        expires, value, weight = item
        if self.clock() >= expires:
            del self.items[key]
            self.weight -= weight
            return False, None
        self.items.move_to_end(key)
        return True, value

    def discard(self, key):
        item = self.items.pop(key, None)
        if item is not None:
            self.weight -= item[2]

    def put(self, key, value, weight=1):
        if key in self.items:
            self.weight -= self.items.pop(key)[2]
        if weight > self.capacity:
            return
        while self.weight + weight > self.capacity:
            self.weight -= self.items.popitem(last=False)[1][2]
        self.items[key] = (self.clock() + self.ttl, value, weight)
        self.weight += weight
