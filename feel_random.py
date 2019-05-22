#!/usr/bin/env python3

# Want:
# * Initially, uniform random distribution
# * If new elements appear, they are likely to be picked
# * If an element is picked, it is unlikely to be picked again soon
# * Long-ago-elements are roughly of the same probability (prevent permutation-lock)

# So:
# - Among new elements, pick uniform.
# - If no new elements, construct LRU-sorted list
# - From the list, pick "towards bottom"
#   * Distribution must be monotonically increasing
#   * So the last must be >= 1/n, and < 1.
# How about 2/n, and going inductive from there?
# That gives a nice parabola as the CDF, which looks good.

import random


class ChoiceMemory:
    def __init__(self):
        self.lastseen = dict()
        self.counter = 0

    def choose(self, available):
        available = list(available)
        new = []
        assert available
        lru_order = []
        for e in available:
            if e not in self.lastseen:
                new.append(e)
                continue
            lru_order.append((self.lastseen[e], e))
        if new:
            e = random.choice(new)
            self._update(e)
            return e            
        lru_order.sort()
        for (i, (_, e)) in enumerate(lru_order):
            remaining_n = len(lru_order) - i
            prob = 1.8 / remaining_n
            if random.random() <= prob:
                self._update(e)
                return e
        raise AssertionError

    def _update(self, element):
        self.lastseen[element] = self.counter
        self.counter += 1


def run_test(n, samples):
    mem = ChoiceMemory()
    choices = list(range(n))
    for _ in range(samples):
        print(mem.choose(choices))


if __name__ == '__main__':
    run_test(9, 100)
