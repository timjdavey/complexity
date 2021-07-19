import numpy as np
from functools import cached_property

from .entropy import shannon_entropy, complexity, sigmoid_complexity


class BinError(ValueError):
    """ When checking good bin structure """
    pass


class ErgodicEnsemble:
    """
    A simple model to help calculate the 

    Contains some simple performance boosts, but also stores
    some helpful data to make visualisation simpler
    (hence why it's a class rather than just a function).
    
    intialization
    :observations: either takes a list or dict of the observations grouped by ensemble
    e.g. [[0,0,1,0], [0,1,0]] or {'UK':[0,0,1,0], 'US':[0,1,0]}
    if pass a dict, the keys will be used as a legend in the ensemble plots
    
    :bins: the bins to be used for the data e.g. np.linspace(data.min(), data.max(), 20)
    :ensemble_name: the name of the ensemble to be used plots
    :dist_name: the name of the distribution variable

    properties
    :ensemble: the average ensemble entropy
    :ergodic: the entropy of the ergodic distribution
    :complexity: the simple ergodic complexity metric
    :sigmoid: the complexity metric passed through a sigmoid function, to amplify & stable the results

    functions
    :plot: plots the ensemble & ergodic histograms
    :ridge: plots a ridge plot of the ensemble histograms
    :stats: prints all the stats in an easy to read format
    """
    def __init__(self, observations, bins, ensemble_name='ensemble', dist_name='value'):

        # naming for plots
        self.ensemble_name = ensemble_name
        self.dist_name = dist_name

        # observations by dict or list
        if isinstance(observations, (list, np.ndarray)):
            self.observations = observations
            self.labels = None
            self.raw = None
        elif isinstance(observations, dict):
            self.observations = list(observations.values())
            self.labels = observations.keys()
            self.raw = observations
        else:
            raise TypeError(
                "observations is of type %s not list or dict" % type(observations))
        
        # all of the observations
        self.ergodic_observations = np.concatenate(self.observations)

        # store data about observation counts across ensembles
        # can't use shape, as different lengths, hence doing this
        obs_counts = []
        for o in self.observations:
            obs_counts.append(len(o))
        self.obs_counts = (np.amin(obs_counts), np.mean(obs_counts), np.amax(obs_counts))

        # error check bins must be constructed correctly
        emin = self.ergodic_observations.min()
        emax = self.ergodic_observations.max()
        lbin = len(bins)-1
        leo = len(self.ergodic_observations)
        if lbin < 2:
            raise BinError("%s bins is too small" % bins)
        elif bins[0] > emin:
            raise BinError("%s lower bin value less than ergodic min" % emin)
        elif bins[-1] < emax:
            raise BinError("%s higher bin value less than ergodic max" % emax)
        elif leo/lbin < 10:
            raise BinError("There are only %s observations for %s bins,\
recommend at least 10-100+ observations per bin not %s" % (leo, lbin, int(leo/lbin)))
        else:
            self.bins = bins



    """
    Data processing
    
    """
    @cached_property
    def histograms(self):
        histograms = []
        for obs in self.observations:
            # ignore erroroneous ensembles with no observations
            if len(obs) > 0:
                hist, nbins = np.histogram(obs, bins=self.bins)
                histograms.append(hist)
        return np.array(histograms)

    @cached_property
    def ergodic_histogram(self):
        return np.histogram(self.ergodic_observations, bins=self.bins)[0]

    @cached_property
    def entropies(self):
        """ Array of entropies for each ensemble """
        entropies = []
        for hist in self.histograms:
            entropies.append(shannon_entropy(hist, True))
        return np.array(entropies)

    @cached_property
    def ensemble_melt(self):
        """ Dataframe of ensemble data prepared """
        import pandas as pd
        return pd.melt(pd.DataFrame(self.observations, index=self.labels).T,
            var_name=self.ensemble_name, value_name=self.dist_name)

    @cached_property
    def ergodic_melt(self):
        import pandas as pd
        return pd.DataFrame({
            self.dist_name:self.ergodic_observations,
            self.ensemble_name:'h',})
    
    """
    Calculations & metrics
    
    """
    @cached_property
    def ensemble_count(self):
        return len(self.entropies)

    @cached_property
    def ensemble(self):
        """ The average (mean) ensemble entropy """
        return np.mean(self.entropies)

    @cached_property
    def ergodic(self):
        """ The entropy of the ergodic distribution """
        return shannon_entropy(self.ergodic_histogram, True)

    @cached_property
    def complexity(self):
        """ A simplier version of the formula """
        return complexity(self.ensemble, self.ergodic)

    @cached_property
    def complexity2(self):
        return sum([(self.ensemble - e)**2 for e in self.entropies])

    @cached_property
    def complexity4(self):
        return sum([(self.ensemble - e)**4 for e in self.entropies])

    @cached_property
    def sigmoid(self):
        """ The sigmoid ergodic complexity to be used by default """
        return sigmoid_complexity(self.complexity)

    @cached_property
    def chisquare_p(self):
        from scipy.stats import chi2_contingency
        try:
            chi2, p, dof, expected = chi2_contingency(self.histograms)
        except ValueError: # if a bin is zero
            return None
        else:
            return p

    @cached_property
    def significance_bool(self):
        """
        returns bool values of whether obversations meet null hypothesis.

        Put explicitly, returns true (1.0) if there's no evidence to
        that the ensembles show ergodic complexity. That is, the distributions
        of each ensemble are independant of how the observations were grouped
        into ensemebles.
        """
        return {
            'p > 0.05': 1.0 if self.chisquare[1] > 0.05 else 0.0,
            'p > 0.01': 1.0 if self.chisquare[1] > 0.01 else 0.0,
            'c < ~0.05': 1.0 if self.complexity < 2**0.5/self.obs_counts[1] else 0.0,
            'c < ~0.01': 1.0 if self.complexity < 1/self.obs_counts[1] else 0.0,
        }


    """
    Plots & displays
    
    """

    def plot(self):
        # in function import so doesn't require
        # pandas or seaborn to use above
        from .plots import dual
        dual(self.ensemble_melt, self.ergodic_melt, self.bins, self.labels,
            tidy_variable=self.ensemble_name, tidy_value=self.dist_name)

    def ridge(self):
        from .plots import ridge
        ridge(self.ensemble_melt, self.bins, self.labels,
            tidy_variable=self.ensemble_name, tidy_value=self.dist_name)
        
    def scatter(self):
        from .plots import scatter
        scatter(self.ensemble_melt, self.bins,
            tidy_variable=self.ensemble_name, tidy_value=self.dist_name)
    
    def stats(self):
        msg = ""
        if self.ensemble_name is not None:
            msg += "%s\n" % self.ensemble_name
        msg += "%.1f%% ergodic complexity\n" % (self.complexity*100)
        msg += "%.1f%% sigmoid complexity\n" % (self.sigmoid*100)
        msg += "%.3f (%.3f) average ensemble (ergodic)\n" % (self.ensemble, self.ergodic)
        msg += "From %s ensembles\n" % self.ensemble_count
        msg += "With bins %s from %s to %s.\n" % (len(self.bins)-1, self.bins[0], self.bins[-1])
        print(msg)
