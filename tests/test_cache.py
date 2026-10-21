import unittest
from assignfs.cache import Cache


class CacheTests(unittest.TestCase):
    def test_expiration(self):
        now = [0]
        cache = Cache(clock=lambda: now[0])
        cache.put('x', None)
        self.assertEqual(cache.get('x'), (True, None))
        now[0] = 1
        self.assertEqual(cache.get('x'), (False, None))
        self.assertEqual(cache.weight, 0)

    def test_bounds_and_lru(self):
        cache = Cache(capacity=3)
        cache.put('a', 1); cache.put('b', 2)
        cache.get('a'); cache.put('c', 3, weight=2)
        self.assertFalse(cache.get('b')[0])
        self.assertTrue(cache.get('a')[0])
        self.assertEqual(cache.weight, 3)
        cache.put('huge', [], weight=4)
        self.assertFalse(cache.get('huge')[0])
