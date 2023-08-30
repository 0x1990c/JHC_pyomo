#  ___________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright (c) 2008-2022
#  National Technology and Engineering Solutions of Sandia, LLC
#  Under the terms of Contract DE-NA0003525 with National Technology and
#  Engineering Solutions of Sandia, LLC, the U.S. Government retains certain
#  rights in this software.
#  This software is distributed under the 3-clause BSD License.
#  ___________________________________________________________________________

from pyomo.core.base.objective import Objective
from pyomo.core.expr.visitor import ExpressionValueVisitor, nonpyomo_leaf_types
import pyomo.core.expr as EXPR


def get_objective(block):
    obj = None
    for o in block.component_data_objects(
        Objective, descend_into=True, active=True, sort=True
    ):
        if obj is not None:
            raise ValueError('Multiple active objectives found')
        obj = o
    return obj


class _VarAndNamedExprCollector(ExpressionValueVisitor):
    def __init__(self):
        self.named_expressions = {}
        self.variables = {}
        self.fixed_vars = {}
        self._external_functions = {}

    def visit(self, node, values):
        pass

    def visiting_potential_leaf(self, node):
        if type(node) in nonpyomo_leaf_types:
            return True, None

        if node.is_variable_type():
            self.variables[id(node)] = node
            if node.is_fixed():
                self.fixed_vars[id(node)] = node
            return True, None

        if node.is_named_expression_type():
            self.named_expressions[id(node)] = node
            return False, None

        if type(node) is EXPR.ExternalFunctionExpression:
            self._external_functions[id(node)] = node
            return False, None

        if node.is_expression_type():
            return False, None

        return True, None


_visitor = _VarAndNamedExprCollector()


def collect_vars_and_named_exprs(expr):
    _visitor.__init__()
    _visitor.dfs_postorder_stack(expr)
    return (
        list(_visitor.named_expressions.values()),
        list(_visitor.variables.values()),
        list(_visitor.fixed_vars.values()),
        list(_visitor._external_functions.values()),
    )


class SolverUtils:
    pass

class SubprocessSolverUtils:
    pass

class DirectSolverUtils:
    pass

class PersistentSolverUtils:
    pass

