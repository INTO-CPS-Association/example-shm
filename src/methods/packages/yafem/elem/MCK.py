import numpy as np
from methods.packages.yafem.nodes import nodes
from methods.packages.yafem.elem.core_elem import core_elem

#%% element_MCK class
class MCK(core_elem):

    # class constructor
    def __init__(self, my_nodes, pars):

        # superclass constructor
        super().__init__(my_nodes,pars)

        # extract parameters and assign default values
        self.extract_pars(pars)

    #%% extract parameters and assign default values
    def extract_pars(self,pars):

        # this is the element class used in packing/unpacking
        self.my_pars['elem'] = 'MCK'

        # stiffness matrix
        if 'K' in pars:
            self.K = pars['K'].astype(np.float64)
        else:
            raise Exception('the stiffness parameter must be defined')

        self.M = pars.get('M', np.zeros(self.K.shape).astype(np.float64)) # mass matrix
        self.C = pars.get('C', np.zeros(self.K.shape).astype(np.float64)) # damping matrix

        # list of dofs
        self.dofs = pars.get('dofs', np.transpose([np.arange(0, self.K.shape[0], dtype=np.int32), 
                                     np.zeros(self.K.shape[0], dtype=np.int32)])).astype(np.int32)

        # temperature controlled dofs
        self.dofs_q = pars.get('dofs_q', np.zeros((0, 2), dtype=np.int32)).astype(np.int32)
