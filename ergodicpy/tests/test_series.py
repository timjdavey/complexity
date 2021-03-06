import numpy as np
import unittest

from ..bins import binobs
from ..ergodic import ErgodicEnsemble
from ..series import ErgodicSeries

class TestSeries(unittest.TestCase):

    def test_random(self):
        for ensembles in (2, 10):
            for samples in (10, 100):
                for steps in (1, 5):
                    obs = [[np.random.power(5,samples)*10 for _ in range(ensembles)] for _ in range(steps)]
                    ees = ErgodicSeries(x=range(steps), observations=obs)
                    self.assertEqual(ees.entropies.shape, (steps, ensembles))

                    # measures
                    for k, v in ees.measures.items():
                        self.assertEqual(len(v), steps)
                    
                    # just does it run
                    ees.dataframe()

                    # max / trends
                    for key, value in ees.max().items():
                        self.assertTrue(value >= ees.trend()[key])

    def test_fixed(self):
        np.random.seed(1283947)

        measures = {'ensemble': ([0.93514933, 0.70948397]), 'ergodic': ([0.97179239, 0.76638377]), 'divergence': ([0.03664307, 0.0568998 ]), 'complexity': ([0.10545047, 0.24092971]), 'tau2': ([ 4.31628893, 22.53171307]), 'tau2p': ([3.77491632e-02, 2.06702846e-06])}

        mmax = {'ensemble': 0.30951977140256587, 'ergodic': 0.3250829733914482, 'divergence': 0.04485226313012047, 'complexity': 0.3859157617880867}
        mtrend = {'ensemble': 0.2087866837915709, 'ergodic': 0.25363894692169137, 'divergence': 0.04485226313012047, 'complexity': 0.3859157617880867}

        x_label = 'tester'
        steps = 2
        ensembles = 5
        x = range(steps)

        # generate from obs vs ensembles
        observations = [[np.random.power(5,20)*10 for _ in range(ensembles)] for _ in x]
        
        # default x is range
        ees1 = ErgodicSeries(observations=observations)
        
        # create from y
        bins = binobs(observations=observations)
        ees2 = ErgodicSeries(y=[ErgodicEnsemble(obs, bins) for obs in observations])

        for ees in [ees1, ees2]:
            # test default x gets assigned
            np.testing.assert_array_equal(ees.x, x)

            # are measures created properly
            for k, v in ees.measures.items():
                np.testing.assert_array_almost_equal(list(v), list(measures[k]))
            
            # max min values
            np.testing.assert_array_almost_equal(list(ees.max().values()), list(mmax.values()))
            np.testing.assert_array_almost_equal(list(ees.trend().values()), list(mtrend.values()))
            np.testing.assert_array_almost_equal(ees.peaks, [1])


if __name__ == '__main__':
    unittest.main()