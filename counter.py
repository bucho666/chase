# -*- coding: utf-8 -*-
class Counter(object):
    def __init__(self, end):
        self._end = end
        self._current = 0

    def __str__(self):
        return str(self._current)

    def tick(self):
        self._current += 1
        self._current %= self._end

    def is_over(self):
        return self._current is 0

    def reset(self):
        self._current = 0
