from openmdao.main.api import set_as_top


from openmdao.main.api import Assembly
from openmdao.lib.drivers.api import SLSQPdriver

from openmdao.examples.simple.paraboloid import Paraboloid

from openmdao.lib.casehandlers.api import JSONCaseRecorder, BSONCaseRecorder

class OptimizationUnconstrained(Assembly):
    """Unconstrained optimization of the Paraboloid Component."""
    
    def configure(self):
        """ Creates a new Assembly containing a Paraboloid and an optimizer"""
        
        # pylint: disable-msg=E1101

        # Create Optimizer instance
        self.add('driver', SLSQPdriver())
        
        # Create Paraboloid component instances
        self.add('paraboloid', Paraboloid())

        # Driver process definition
        self.driver.workflow.add('paraboloid')
        
        # SQLSQP Flags
        self.driver.iprint = 0
        
        # Objective 
        self.driver.add_objective('paraboloid.f_xy')
        
        # Design Variables 
        self.driver.add_parameter('paraboloid.x', low=-50., high=50.)
        self.driver.add_parameter('paraboloid.y', low=-50., high=50.)


model = OptimizationUnconstrained()
model.recorders = [JSONCaseRecorder('unconstrained.json'), BSONCaseRecorder('unconstrained.bson')]
set_as_top(model)

model.run()
