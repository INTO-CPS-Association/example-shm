import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.linalg import block_diag
from methods.packages.yafem.nodes import nodes
from methods.packages.yafem.elem.core_elem import core_elem
from methods.packages.yafem.elem.beam3d_circ_func import *
from methods.packages.yafem.elem.beam3d_gen_func import *
import functools

def disabled_method(method):
    """Decorator to disable a method in a subclass so that the superclass method is used."""
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        raise NotImplementedError("This method is disabled and should not be used.")
    
    wrapper._disabled = True  # Custom attribute to mark as disabled
    return wrapper

class userdef(core_elem):
    #%% class constructor
    def __init__(self, my_nodes, pars):

        # superclass constructor
        super().__init__(my_nodes,pars)

        # link the nodes to the element
        self.my_nodes = my_nodes
        
        # extract parameters and assign default values
        self.extract_pars(pars)

        # Stiffness matrix in global coordinate system
        self.K = np.zeros((1,1))
        
        # Mass matrix
        self.M = np.zeros((1,1))

        # damping matrix in global coordinates
        self.C = np.zeros((1,1))

        # local to global coordinate transformation
        self.r = np.zeros((1))
        
    #%% extract parameters
    def extract_pars(self, pars):
        
        # this is an example of how to extract a parameter and assign a default value
        self.example = pars.get("example",0)
 
    #%% compute the mass matrix
    @disabled_method # this is already defined like this in core_elem; so keep it only if you need to edit it
    def compute_M(self):
        return self.M

    #%% compute the damping matrix
    @disabled_method # this is already defined like this in core_elem; so keep it only if you need to edit it
    def compute_C(self,u,v,q,t,i):
        return self.C

    #%% compute the stiffness matrix
    @disabled_method # this is already defined like this in core_elem; so keep it only if you need to edit it
    def compute_K(self,u,v,q,t,i):
        return self.K

    #%% compute the restoring force
    @disabled_method # this is already defined like this in core_elem; so keep it only if you need to edit it
    def compute_r(self,u,v,q,t,i):

        # compute the restoring force
        r = self.K @ u + self.C @ v

        # store the state variables
        self.u = u
        self.v = v
        self.r = r
        self.t = t 
        self.i = i

        # return the restoring force
        return r
     
    #%% add the element plot to the axis ax
    @disabled_method # this is already defined like this in core_elem; so keep it only if you need to edit it
    def plot(self, ax, x=None, y=None, z=None, color='k-'):
        pass
    
    #%% damp the element results to paraview file
    @disabled_method # this is already defined like this in core_elem; so keep it only if you need to edit it
    def dump_to_paraview(self):
        # here it goes the dump_to_paraview implementation for the beam3d element
        pass
