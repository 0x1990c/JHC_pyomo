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


# import libraries
from pyomo.common.dependencies import (
    numpy as np, numpy_available,
    pandas as pd, pandas_available,
)

import pyomo.common.unittest as unittest
from pyomo.contrib.doe.fim_doe import Measurements, DesignOfExperiments

from pyomo.opt import SolverFactory
ipopt_available = SolverFactory('ipopt').available()

class doe_object_Tester(unittest.TestCase):
    """ Test the kinetics example with both the sequential_finite mode and the direct_kaug mode
    """
    @unittest.skipIf(not ipopt_available, "The 'ipopt' command is not available")
    def setUP(self):
        from pyomo.contrib.doe.example import reactor_kinetics as reactor
        
        # define create model function 
        createmod = reactor.create_model
        
        # discretizer 
        disc = reactor.disc_for_measure
        
        # design variable and its control time set
        t_control = [0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1]
        dv_pass = {'CA0': [0],'T': t_control}

        # Define measurement time points
        t_measure = [0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1]
        measure_pass = {'C':{'CA': t_measure, 'CB': t_measure, 'CC': t_measure}}
        measure_class =  Measurements(measure_pass)
        
        # Define parameter nominal value 
        parameter_dict = {'A1': 84.79085853498033, 'A2': 371.71773413976416, 'E1': 7.777032028026428, 'E2': 15.047135137500822}

        def generate_exp(t_set, CA0, T):  
            """Generate experiments. 
            t_set: time control set for T.
            CA0: CA0 value
            T: A list of T 
            """
            assert(len(t_set)==len(T)), 'T should have the same length as t_set'

            T_con_initial = {}
            for t, tim in enumerate(t_set):
                T_con_initial[tim] = T[t]

            dv_dict_overall = {'CA0': {0: CA0},'T': T_con_initial}
            return dv_dict_overall
        
        # empty prior
        prior_all = np.zeros((4,4))

        prior_pass=np.asarray(prior_all)
        
        ### Test sequential_finite mode
        exp1 = generate_exp(t_control, 5, [300, 300, 300, 300, 300, 300, 300, 300, 300])

        doe_object = DesignOfExperiments(parameter_dict, dv_pass,
                             measure_class, createmod,
                            prior_FIM=prior_pass, discretize_model=disc, args=[True])

    
        result = doe_object.compute_FIM(exp1,mode='sequential_finite', FIM_store_name = 'dynamic.csv', 
                                        store_output = 'store_output', read_output=None,
                                        scale_nominal_param_value=True, formula='central')


        result.calculate_FIM(doe_object.design_values)

        self.assertAlmostEqual(np.log10(result.trace), 2.962954, places=3)
        self.assertAlmostEqual(result.FIM[0][1], 1.840604, places=3)
        self.assertAlmostEqual(result.FIM[0][2], -70.238140, places=3)
        
        ### Test direct_kaug mode
        exp2 = generate_exp(t_control, 5, [570, 300, 300, 300, 300, 300, 300, 300, 300])
        
        doe_object2 = DesignOfExperiments(parameter_dict, dv_pass,
                             measure_class, createmod,
                            prior_FIM=prior_pass, discretize_model=disc, args=[False])
        result2 = doe_object2.compute_FIM(exp2,mode='direct_kaug', FIM_store_name = 'dynamic.csv', 
                                        store_output = 'store_output', read_output=None,
                                        scale_nominal_param_value=True, formula='central')
        
        result2.calculate_FIM(doe_object2.design_values)

        self.assertAlmostEqual(np.log10(result2.trace), 2.788587, places=3)
        self.assertAlmostEqual(np.log10(result2.det), 2.821840, places=3)
        self.assertAlmostEqual(np.log10(result2.min_eig), -1.012346, places=3)
        
            
        square_result, optimize_result= doe_object.optimize_doe(exp1, if_optimize=True, if_Cholesky=True,                                          scale_nominal_param_value=True, objective_option='det', 
                                                         L_initial=None)
        
        self.assertAlmostEqual(optimize_result.model.T[0], 477.134504, places=3)
        self.assertAlmostEqual(optimize_result.model.T[1], 300.000207, places=3)
        self.assertAlmostEqual(np.log10(optimize_result.trace), 2.982298, places=3)
        self.assertAlmostEqual(np.log10(optimize_result.det), 3.303190, places=3)
        

if __name__ == '__main__':
    unittest.main()
