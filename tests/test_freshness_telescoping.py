"""Show why lagged Brier improvements are endpoint identities, not information alpha."""
import unittest


def old_minus_current(losses,lag=1):
    return sum(losses[t-lag]-losses[t] for t in range(lag,len(losses)))


def endpoints(losses,lag=1):
    return sum(losses[:lag])-sum(losses[-lag:])


class TelescopingContract(unittest.TestCase):
    def test_same_endpoints_different_middle_but_same_lag_one(self):
        a=[.9,.7,.2,.45,.05]
        b=[.9,.05,.88,.01,.05]
        self.assertAlmostEqual(old_minus_current(a),.85)
        self.assertAlmostEqual(old_minus_current(b),.85)
        self.assertNotEqual(a[1:-1],b[1:-1])

    def test_all_original_lag_sizes_telescope(self):
        losses=[.9,.8,.7,.6,.5,.4,.3,.2,.1]
        for lag in (1,2,5):
            self.assertAlmostEqual(old_minus_current(losses,lag),endpoints(losses,lag))

    def test_phase_sums_are_phase_boundary_loss(self):
        l=[.5,.38,.27,.22,.33,.2]
        first=sum(l[t-1]-l[t] for t in (1,2))
        last=sum(l[t-1]-l[t] for t in (3,4,5))
        self.assertAlmostEqual(first,l[0]-l[2])
        self.assertAlmostEqual(last,l[2]-l[5])
        self.assertAlmostEqual(first+last,l[0]-l[-1])

    def test_per_minute_mean_only_depends_on_game_boundaries(self):
        cases=[[.92,.55,.22,.12],[.85,.99,.31]]
        n=sum(len(x)-1 for x in cases)
        self.assertAlmostEqual(sum(old_minus_current(x) for x in cases)/n,
                               sum(x[0]-x[-1] for x in cases)/n)


if __name__=="__main__":
    unittest.main()
