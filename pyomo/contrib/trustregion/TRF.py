#  ___________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright 2017 National Technology and Engineering Solutions of Sandia, LLC
#  Under the terms of Contract DE-NA0003525 with National Technology and 
#  Engineering Solutions of Sandia, LLC, the U.S. Government retains certain 
#  rights in this software.
#  This software is distributed under the 3-clause BSD License.
#  ___________________________________________________________________________

import logging

from pyomo.core.base.range import NumericRange
from pyomo.core import Var
from pyomo.common.config import (ConfigDict, ConfigValue,
                                 Bool, PositiveInt,
                                 PositiveFloat, In)
from pyomo.contrib.trustregion.filter import Filter, FilterElement
from pyomo.contrib.trustregion.interface import TRFInterface
from pyomo.contrib.trustregion.util import IterationLogger
from pyomo.opt import SolverFactory

logger = logging.getLogger('pyomo.contrib.trustregion')

__version__ = '0.2.0'


def trust_region_method(model, decision_variables,
                        ext_fcn_surrogate_map_rule, config):
    """
    Main driver of the Trust Region algorithm.
    """

    # Initialize necessary TRF methods
    TRFLogger = IterationLogger()
    TRFilter = Filter()
    interface = TRFInterface(model, decision_variables,
                             ext_fcn_surrogate_map_rule, config)

    # Initialize the problem
    rebuildSM = False
    obj_val, feasibility = interface.initializeProblem()
    quit()
    # Initialize first iteration feasibility/objective value to enable
    # termination check
    feasibility_k = feasibility
    obj_val_k = obj_val
    # Initialize step_norm_k to a bogus value to enable termination check
    step_norm_k = 1
    # Initialize trust region radius
    trust_radius = config.trust_radius

    iteration = 0
    while iteration < config.maximum_iterations:
        iteration += 1

        for var in interface.model.component_data_objects(Var):
            var.pprint()
        quit()

        # Check termination conditions
        if ((feasibility_k <= 1e-5)
            and (step_norm_k <= 1e-5)):
            print('EXIT: Optimal solution found.')
            break

        # If trust region very small and no progress is being made,
        # terminate. The following condition must hold for two
        # consecutive iterations.
        if ((trust_radius <= config.minimum_radius) and
            (feasibility_k < config.feasibility_termination)):
            if subopt_flag:
                print('WARNING: Insufficient progress.')
                print('EXIT: Feasible solution found.')
                break
            else:
                subopt_flag = True
        else:
            # This condition holds for iteration 0, which will declare
            # the boolean subopt_flag
            subopt_flag = False

        # Set bounds to enforce the trust region
        interface.updateDecisionVariableBounds(trust_radius)
        # Generate suggorate model r_k(w)
        if rebuildSM:
            interface.updateSurrogateModel()

        # Solve the Trust Region Subproblem (TRSP)
        obj_val_k, step_norm_k, feasibility_k = interface.solveModel()

        TRFLogger.newIteration(iteration, feasibility_k, obj_val_k,
                               trust_radius, step_norm_k)
        # print(200*'*')
        # interface.model.pprint()
        print(100*'*')
        print('Feasibility:', feasibility_k)
        print('Objective:', obj_val_k)
        print('Step norm:', step_norm_k)
        print(100*'*')

        # Check filter acceptance
        filterElement = FilterElement(feasibility_k, obj_val_k)
        if not TRFilter.isAcceptable(filterElement, config.maximum_feasibility):
            # Reject the step
            TRFLogger.iterrecord.rejected = True
            trust_radius = max(config.minimum_radius,
                               step_norm_k*config.radius_update_param_gamma_c)
            rebuildSM = False
            interface.rejectStep()
            continue

        # Switching condition: Eq. (7) in Yoshio/Biegler (2020)
        if ((obj_val - obj_val_k >=
             config.switch_condition_kappa_theta
             * pow(feasibility, config.switch_condition_gamma_s))
            and (feasibility <= config.minimum_feasibility)):
            # f-type step
            TRFLogger.iterrecord.fStep = True
            trust_radius = min(max(step_norm_k*config.radius_update_param_gamma_e,
                                   trust_radius),
                               config.maximum_radius)
        else:
            # theta-type step
            TRFLogger.iterrecord.thetaStep = True
            filterElement = FilterElement(obj_val_k - config.filter_param_gamma_f*feasibility_k,
                                          (1 - config.filter_param_gamma_theta)*feasibility_k)
            TRFilter.addToFilter(filterElement)
            # Calculate ratio: Eq. (10) in Yoshio/Biegler (2020)
            rho_k = ((feasibility - feasibility_k + config.feasibility_termination) /
                     max(feasibility, config.feasibility_termination))
            # Ratio tests: Eq. (8) in Yoshio/Biegler (2020)
            # If rho_k is between eta_1 and eta_2, trust radius stays same
            if ((rho_k < config.ratio_test_param_eta_1) or
                (feasibility > config.minimum_feasibility)):
                trust_radius = max(config.minimum_radius,
                                   config.radius_update_param_gamma_c
                                   * step_norm_k)
            elif ((rho_k >= config.ratio_test_param_eta_2) and
                  (feasibility <= config.minimum_feasibility)):
                trust_radius = max(trust_radius,
                                   config.maximum_radius,
                                   config.radius_update_param_gamma_e
                                   * step_norm_k)

        # Log iteration information
        TRFLogger.logIteration()

        # Accept step and reset for next iteration
        rebuildSM = True
        feasibility = feasibility_k
        obj_val = obj_val_k

    interface.model.display()
    if iteration >= config.maximum_iterations:
        print('EXIT: Maximum iterations reached: {}.'.format(config.maximum_iterations))


def _trf_config():
    CONFIG = ConfigDict('TrustRegion')

    ### Solver options
    CONFIG.declare('solver', ConfigValue(
        default='ipopt',
        description='Solver to use. Default = ipopt.'
    ))
    CONFIG.declare('keepfiles', ConfigValue(
        default=False,
        domain=Bool,
        description="Optional. Default = False. Whether or not to "
                    "write files of sub-problems for use in debugging. "
                    "Must be paired with a writable directory "
                    "supplied via ``subproblem_file_directory``."
    ))
    CONFIG.declare('tee', ConfigValue(
        default=False,
        domain=Bool,
        description="Optional. Default = False. Sets the ``tee`` "
                    "for sub-solver(s) utilized."
    ))

    ### Trust Region specific options
    CONFIG.declare('trust radius', ConfigValue(
        default=1.0,
        domain=PositiveFloat,
        description="Initial trust region radius (delta_0). "
                    "Default = 1.0."
    ))
    CONFIG.declare('minimum radius', ConfigValue(
        default=1e-6,
        domain=PositiveFloat,
        description="Minimum allowed trust region radius (delta_min). "
                    "Default = 1e-6."
    ))
    CONFIG.declare('maximum radius', ConfigValue(
        default=CONFIG.trust_radius * 100,
        domain=PositiveFloat,
        description="Maximum allowed trust region radius. If trust region "
                    "radius reaches maximum allowed, solver will exit. "
                    "Default = 100 * trust_radius."
    ))
    CONFIG.declare('maximum iterations', ConfigValue(
        default=50,
        domain=PositiveInt,
        description="Maximum allowed number of iterations. "
                    "Default = 50."
    ))
    ### Termination options
    CONFIG.declare('feasibility termination', ConfigValue(
        default=1e-5,
        domain=PositiveFloat,
        description="Feasibility measure termination tolerance (epsilon_theta). "
                    "Default = 1e-5."
    ))
    CONFIG.declare('step size termination', ConfigValue(
        default=CONFIG.feasibility_termination,
        domain=PositiveFloat,
        description="Step size termination tolerance (epsilon_s). "
                    "Matches the feasibility termination tolerance by default."
    ))
    ### Switching Condition options
    CONFIG.declare('minimum feasibility', ConfigValue(
        default=1e-4,
        domain=PositiveFloat,
        description="Minimum feasibility measure (theta_min). "
                    "Default = 1e-4."
    ))
    CONFIG.declare('switch condition kappa theta', ConfigValue(
        default=0.1,
        domain=In(NumericRange(0, 1, 0, (False, False))),
        description="Switching condition parameter (kappa_theta). "
                    "Contained in open set (0, 1). "
                    "Default = 0.1."
    ))
    CONFIG.declare('switch condition gamma s', ConfigValue(
        default=2.0,
        domain=PositiveFloat,
        description="Switching condition parameter (gamma_s). "
                    "Must satisfy: gamma_s > 1/(1+mu) where mu "
                    "is contained in set (0, 1]. "
                    "Default = 2.0."
    ))
    ### Trust region update/ratio test parameters
    CONFIG.declare('radius update param gamma c', ConfigValue(
        default=0.5,
        domain=In(NumericRange(0, 1, 0, (False, False))),
        description="Lower trust region update parameter (gamma_c). "
                    "Default = 0.5."
    ))
    CONFIG.declare('radius update param gamma e', ConfigValue(
        default=2.5,
        domain=In(NumericRange(1, None, 0)),
        description="Upper trust region update parameter (gamma_e). "
                    "Default = 2.5."
    ))
    CONFIG.declare('ratio test param eta_1', ConfigValue(
        default = 0.05,
        domain=In(NumericRange(0, 1, 0, (False, False))),
        description="Lower ratio test parameter (eta_1). "
                    "Must satisfy: 0 < eta_1 <= eta_2 < 1. "
                    "Default = 0.05."
    ))
    CONFIG.declare('ratio test param eta_2', ConfigValue(
        default = 0.2,
        domain=In(NumericRange(0, 1, 0, (False, False))),
        description="Lower ratio test parameter (eta_2). "
                    "Must satisfy: 0 < eta_1 <= eta_2 < 1. "
                    "Default = 0.2."
    ))
    ### Filter
    CONFIG.declare('maximum feasibility', ConfigValue(
        default=50.0,
        domain=PositiveFloat,
        description="Maximum allowable feasibility measure (theta_max). "
                    "Parameter for use in filter method."
                    "Default = 50.0."
    ))
    CONFIG.declare('filter param gamma theta', ConfigValue(
        default=0.01,
        domain=In(NumericRange(0, 1, 0, (False, False))),
        description="Fixed filter parameter (gamma_theta) within (0, 1). "
                    "Default = 0.01"
    ))
    CONFIG.declare('filter param gamma f', ConfigValue(
        default=0.01,
        domain=In(NumericRange(0, 1, 0, (False, False))),
        description="Fixed filter parameter (gamma_f) within (0, 1). "
                    "Default = 0.01"
    ))

    return CONFIG


@SolverFactory.register(
    'trustregion',
    doc='Trust region algorithm "solver" for black box/glass box optimization')
class TrustRegionSolver(object):
    """
    The Trust Region Solver is a 'solver' based on the 2016/2018/2020 AiChE
    papers by Eason (2016/2018), Yoshio (2020), and Biegler.
    """

    def __init__(self, **kwds):
        self._CONFIG = _trf_config()
        self._CONFIG.set_value(kwds)

    def available(self, exception_flag=True):
        """
        Check if solver is available.
        """
        return True

    def version(self):
        """
        Return a 3-tuple describing the solver version.
        """
        return __version__

    def license_is_valid(self):
        """
        License for using Trust Region solver.
        """
        return True

    def __enter__(self):
        return self

    def __exit__(self, et, ev, tb):
        pass

    def solve(self, model, degrees_of_freedom_variables,
              ext_fcn_surrogate_map_rule=None, **kwds):
        """
        ext_fcn_surrogate_map_rule - Documentation needed
        degrees_of_freedom_variables : List of var datas that represent u_k from
                             2020 Yoshio/Biegler paper (we assume that the user has scaled all of the values appropriately in order to remove the E^{-1} and S^{-1} scaling values.)
        """
        self.config = self._CONFIG(kwds.pop('options', {}))
        self.config.set_value(kwds)
        if ext_fcn_surrogate_map_rule is None:
            # If the user does not pass us a "basis" function,
            # we default to 0.
            ext_fcn_surrogate_map_rule = lambda comp,ef: 0
        
        trust_region_method(model, degrees_of_freedom_variables,
                            ext_fcn_surrogate_map_rule, self.config)
