#  ___________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright 2017 National Technology and Engineering Solutions of Sandia, LLC
#  Under the terms of Contract DE-NA0003525 with National Technology and
#  Engineering Solutions of Sandia, LLC, the U.S. Government retains certain
#  rights in this software.
#  This software is distributed under the 3-clause BSD License.
#  ___________________________________________________________________________

from io import StringIO
import sys
import logging

import pyomo.common.unittest as unittest

from pyomo.contrib.trustregion.util import (
    IterationLogger, minIgnoreNone, maxIgnoreNone
)
from pyomo.common.log import LoggingIntercept


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.iterLogger = IterationLogger()
        self.iteration = 0
        self.thetak = 10.0
        self.objk = 5.0
        self.radius = 1.0
        self.stepNorm = 0.25

    def tearDown(self):
        pass

    def test_minIgnoreNone(self):
        a = 1
        b = 2
        self.assertEqual(minIgnoreNone(a, b), a)
        a = None
        self.assertEqual(minIgnoreNone(a, b), b)
        a = 1
        b = None
        self.assertEqual(minIgnoreNone(a, b), a)
        a = None
        self.assertEqual(minIgnoreNone(a, b), None)

    def test_maxIgnoreNone(self):
        a = 1
        b = 2
        self.assertEqual(maxIgnoreNone(a, b), b)
        a = None
        self.assertEqual(maxIgnoreNone(a, b), b)
        a = 1
        b = None
        self.assertEqual(maxIgnoreNone(a, b), a)
        a = None
        self.assertEqual(maxIgnoreNone(a, b), None)

    def test_IterationRecord(self):
        self.iterLogger.newIteration(self.iteration, self.thetak, self.objk,
                                 self.radius, self.stepNorm)
        self.assertEqual(len(self.iterLogger.iterations), 1)
        self.assertEqual(self.iterLogger.iterations[0].objectiveValue, 5.0)

    def test_logIteration(self):
        self.iterLogger.newIteration(self.iteration, self.thetak, self.objk,
                                 self.radius, self.stepNorm)
        OUTPUT = StringIO()
        with LoggingIntercept(OUTPUT, 'pyomo.contrib.trustregion', logging.INFO):
            self.iterLogger.logIteration()
        self.assertIn('Iteration 0', OUTPUT.getvalue())
        self.assertIn('feasibility =', OUTPUT.getvalue())
        self.assertIn('stepNorm =', OUTPUT.getvalue())

    def test_printIteration(self):
        self.iterLogger.newIteration(self.iteration, self.thetak, self.objk,
                                 self.radius, self.stepNorm)
        OUTPUT = StringIO()
        sys.stdout = OUTPUT
        self.iterLogger.printIteration()
        sys.stdout = sys.__stdout__
        self.assertIn(str(self.radius), OUTPUT.getvalue())
        self.assertIn(str(self.iteration), OUTPUT.getvalue())
        self.assertIn(str(self.thetak), OUTPUT.getvalue())
        self.assertIn(str(self.objk), OUTPUT.getvalue())
        self.assertIn(str(self.stepNorm), OUTPUT.getvalue())
