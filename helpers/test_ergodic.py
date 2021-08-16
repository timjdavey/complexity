import numpy as np
import unittest

from .ergodic import ErgodicEnsemble, binr, BinError


class TestEntropy(unittest.TestCase):

    def test_ergodic(self):
        np.random.seed(19680800)

        ensembles = 1000
        samples = 1000

        cases = [
            (2.1697928929727737, 2.1639188572981265,
                [np.random.power(5,samples)*10 for c in range(ensembles)]),
            (3.3219230427487183, 3.3153808928073305,
                [np.random.uniform(0,10,samples) for c in range(ensembles)]),
        ]
        
        for ergodic, ensemble, observations in cases:
            observations = np.array(observations)
            bins = np.arange(observations.max() + 2)
            ee = ErgodicEnsemble(observations, bins)

            # statistics
            self.assertEqual(ee.ergodic, ergodic)
            self.assertEqual(ee.ensemble, ensemble)

            # should be about 0 complexity as they're all power or uniform
            np.testing.assert_almost_equal(ee.complexity, 0.0, 2)

    def test_bins(self):

        # need more than one dimensional observations
        with self.assertRaises(ValueError):
            binr([1,2,3])
        # minimum too high
        with self.assertRaises(BinError):
            binr([[1,2,3],[1,2,3]], minimum=5)
        # maximum too low
        with self.assertRaises(BinError):
            binr([[1,2,3],[1,2,3]], maximum=2)

        cases = [
            # defaults
            (binr([[0,1,3],[0,5]]),
                [0,1,2,3,4,5,6]),
            (binr([[1,3],[5]]),
                [1,2,3,4,5,6]),

            # minimums
            (binr([[1,3],[5]], minimum=0),
                [0,1,2,3,4,5,6]),

            # maximums
            (binr([[1,3],[5]], minimum=0, maximum=8),
                [0,1,2,3,4,5,6,7,8,9]),

            # count
            (binr([[1,10],[10]], count=2),
                [1,6,11])
        ]
        for created, expected in cases:
            self.assertEqual(list(created), expected)


if __name__ == '__main__':
    unittest.main()