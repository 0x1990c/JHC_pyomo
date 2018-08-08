"""Tests the Bounds Tightening module."""
import pyutilib.th as unittest
from pyomo.environ import (ConcreteModel, Constraint, TransformationFactory, Var, value)


class TestIntervalTightener(unittest.TestCase):
    """Tests Bounds Tightening."""

    def test_constraint_bound_tightening(self):

        # Check for no coefficients
        m = ConcreteModel()
        m.v1 = Var(initialize=7, bounds=(7, 10))
        m.v2 = Var(initialize=2, bounds=(2, 5))
        m.v3 = Var(initialize=6, bounds=(6, 9))
        m.v4 = Var(initialize=1, bounds=(1, 1))
        m.c1 = Constraint(expr=m.v1 >= m.v2 + m.v3 + m.v4)

        TransformationFactory('core.tighten_constraints_from_vars').apply_to(m)
        self.assertTrue(value(m.c1.upper) == 0)
        self.assertTrue(value(m.c1.lower) == -1)
        del m

        m = ConcreteModel()
        m.v1 = Var(initialize=7, bounds=(7, 10))
        m.v2 = Var(initialize=2, bounds=(2, 5))
        m.v3 = Var(initialize=6, bounds=(6, 9))
        m.v4 = Var(initialize=1, bounds=(1, 1))
        m.c1 = Constraint(expr=m.v1 <= m.v2 + m.v3 + m.v4)

        TransformationFactory('core.tighten_constraints_from_vars').apply_to(m)
        self.assertTrue(value(m.c1.upper) == 0)
        self.assertTrue(value(m.c1.lower) == -8)
        del m

        # test for coefficients
        m = ConcreteModel()
        m.v1 = Var(initialize=7, bounds=(7, 10))
        m.v2 = Var(initialize=2, bounds=(2, 5))
        m.v3 = Var(initialize=6, bounds=(6, 9))
        m.v4 = Var(initialize=1, bounds=(1, 1))
        m.c1 = Constraint(expr=m.v1 <= 2 * m.v2 + m.v3 + m.v4)

        TransformationFactory('core.tighten_constraints_from_vars').apply_to(m)
        self.assertTrue(value(m.c1.upper) == -1)
        self.assertTrue(value(m.c1.lower) == -13)
        del m

        # test for unbounded variables
        m = ConcreteModel()
        m.v1 = Var(initialize=7)
        m.v2 = Var(initialize=2, bounds=(2, 5))
        m.v3 = Var(initialize=6, bounds=(6, 9))
        m.v4 = Var(initialize=1, bounds=(1, 1))
        m.c1 = Constraint(expr=m.v1 <= 2 * m.v2 + m.v3 + m.v4)

        TransformationFactory('core.tighten_constraints_from_vars').apply_to(m)
        self.assertTrue(value(m.c1.upper) == 0)
        self.assertTrue(not m.c1.has_lb())
        del m

        # test for coefficients
        m = ConcreteModel()
        m.v1 = Var(initialize=7, bounds=(-float('inf'), 10))
        m.v2 = Var(initialize=2, bounds=(2, 5))
        m.v3 = Var(initialize=6, bounds=(6, 9))
        m.v4 = Var(initialize=1, bounds=(1, 1))
        m.c1 = Constraint(expr=m.v1 <= 2 * m.v2 + m.v3 + m.v4)

        TransformationFactory('core.tighten_constraints_from_vars').apply_to(m)
        self.assertTrue(value(m.c1.upper) == -1)
        self.assertTrue(not m.c1.has_lb())
        del m


if __name__ == '__main__':
    unittest.main()
