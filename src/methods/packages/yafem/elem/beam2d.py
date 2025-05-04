import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.linalg import block_diag
from methods.packages.yafem.nodes import nodes
from methods.packages.yafem.elem.core_elem import core_elem
from methods.packages.yafem.elem.beam2d_gen_func import *

#%% element_beam2d class
class beam2d(core_elem):

    # class constructor
    def __init__(self, my_nodes, pars):

        # superclass constructor
        super().__init__(my_nodes,pars)

        # extract parameters and assign default values
        self.extract_pars(pars)

        # element dofs
        self.dofs = np.array([[self.nodal_labels[0],1],   
                              [self.nodal_labels[0],2],   
                              [self.nodal_labels[0],3],   
                              [self.nodal_labels[1],1],
                              [self.nodal_labels[1],2],
                              [self.nodal_labels[1],3]],dtype=np.int32)
        
        # # rotation matrix in the xy plane
        r = (self.nodal_coords[1,:2] - self.nodal_coords[0,:2])/self.L
        s = np.array([-r[1],r[0]])

        # Local reference system
        self.T = np.array([r, s])

        # global to local transformation matrix in the xy plane
        self.G = np.zeros((6, 6))
        self.G[0:2, 0:2] = self.T
        self.G[2:3, 2:3] = 1
        self.G[3:5, 3:5] = self.T
        self.G[5:6, 5:6] = 1

        # Variables
        variables = [self.A, 
                     self.E, 
                     self.I, 
                     self.L, 
                     self.alpha, 
                     self.fa, 
                     self.fb, 
                     self.k0a, 
                     self.k0b, 
                     self.rho, 
                     self.theta]

        # Axial components
        Ka  = beam2d_gen_Ka(*variables)
        Kwa = beam2d_gen_Kwa(*variables)
        Ma  = beam2d_gen_Ma(*variables)
        fca = beam2d_gen_fca(*variables)
        fta = beam2d_gen_fta(*variables)
        
        # Lateral components
        Kb  = beam2d_gen_Kb(*variables)  
        Kwb = beam2d_gen_Kwb(*variables)    
        Mb  = beam2d_gen_Mb(*variables)  
        fcb = beam2d_gen_fcb(*variables)   
                
        # Displacement interpolation matrices
        Na  = beam2d_gen_Na_mid(*variables)
        Nb  = beam2d_gen_Nb_mid(*variables)

        # strain interpolation matrices
        Ba  = beam2d_gen_Ba_mid(*variables)
        Bb  = beam2d_gen_Bb_mid(*variables)

        # cross-section stiffness matrix
        self.D = beam2d_gen_Dcs_mid(*variables)

        # Indexes for stiffness assembly
        inda = [0, 3]       # Indices for axial properties    
        indb = [1, 2, 4, 5] # Indices for lateral properties y

        # Stiffness matrix in local coordinate system
        self.Kl = np.zeros((6, 6))
        self.Ml = self.Kl.copy()
        self.rl = np.zeros((6, 1))

        #%% Axial properties
        # Combined axial rod + winkler
        self.Kl[np.ix_(inda, inda)] += Ka + Kwa

        # Axial mass matrix
        self.Ml[np.ix_(inda, inda)] += Ma

        # Mechanical and Thermal load vector
        self.rl[inda] += (fca + fta)

        #%% Lateral properties
        # Lateral stiffness
        self.Kl[np.ix_(indb, indb)] += Kb + Kwb

        # Lateral mass matrix
        self.Ml[np.ix_(indb, indb)] += Mb

        # Mechanical and Thermal load vector
        self.rl[indb] += fcb

        # displacement and strain interpolation matrix allocation
        self.Nl = np.zeros((3, 6))
        self.Bl = self.Nl.copy()

        # Displacement interpolation matrix in the mid point
        self.Nl[np.ix_([0], inda)] += Na.squeeze()  # axial displacement
        self.Nl[np.ix_([1], indb)] += Nb.squeeze() # lateral displacement y

        # Strain interpolation matrix in the mid point
        self.Bl[np.ix_([0], inda)] += Ba.squeeze()  # axial strain
        self.Bl[np.ix_([1], indb)] += Bb.squeeze() # curvature in y

        #%% Global reference

        # Stiffness matrix in global coordinate system
        self.K = self.G.T @ self.Kl @ self.G
        self.M = self.G.T @ self.Ml @ self.G

        # damping matrix in global coordinates
        self.C = np.zeros_like(self.K)

        # strain interpolation matrix in global coordinates
        self.B = self.Bl @ self.G

        # displacement interpolation matrix in global coordinates
        self.N = self.Nl @ self.G

        # local to global coordinate transformation
        self.r = self.G.T @ self.rl     
 
        self.Ka  = Ka
        self.Kwa = Kwa
        self.Ma  = Ma
        self.fca = fca
        self.fta = fta
        self.Kby = Kb
        self.Kwb = Kwb
        self.Mb  = Mb
        self.fcb = fcb

        #%% extract parameters
    def extract_pars(self, pars):
        
        # this is the element class used in packing/unpacking
        self.my_pars['elem'] = 'beam2d'

        self.A     = pars.get("A", 200.0) # Cross-sectional areal
        self.I     = pars.get("I", 1000.0) # second area moment
        self.E     = pars.get("E", 210e3) # Youngs modulus
        self.G1    = pars.get("G", 81e3) # Shear modulus
        self.k0a   = pars.get("k0a", 0.0) # Axial Winkler stiffness
        self.k0b   = pars.get("k0b", 0.0) # Lateral Winkler stiffness
        self.rho   = pars.get("rho", 7850/1e9) # Density
        self.fa    = pars.get("fa", 0.0) # Axial element destributed force
        self.fb    = pars.get("fb", 0.0) # Lateral element destributed force in y-direction
        self.alpha = pars.get("alpha", 0.0) # coefficient of thermal expansion 
        self.theta = pars.get("theta", 0.0) # Thermal loading
        self.nodal_labels = pars.get("nodal_labels", [1, 2])
        
        # extract nodal coordinates
        self.nodal_coords = self.my_nodes.find_coords(self.nodal_labels)
        self.L = np.linalg.norm(self.nodal_coords[1] - self.nodal_coords[0])
    
        # temperature controlled dofs
        self.dofs_q = np.array(pars.get("dofs_q", []), dtype=np.int32).reshape(-1, 2) if "dofs_q" in pars else np.zeros((0, 2), dtype=np.int32)


    #%% plot the element       
    def plot(self, ax, x=None, y=None, z=None, color='k-'):
        if x is None: x = self.nodal_coords[:, 0]
        if y is None: y = self.nodal_coords[:, 1]
        if z is None: z = self.nodal_coords[:, 2]

        # Collect lines
        lines = [[[x[0], y[0], 0],[x[1], y[1], 0]]]

        return lines, None


# #%% element_beam2d class
# class beam2d(core_elem):

#     # all element parameters are hidden
#     _A : float # cross-section area
#     _I : float # cross-section inertia
#     _L : float # beam2d length
#     _E : float # elastic modulus
#     _Rho : float # density

#     # class constructor
#     def __init__(self, my_nodes, pars):

#         # superclass constructor
#         super().__init__(my_nodes,pars)

#         # extract parameters and assign default values
#         self.extract_pars(pars)

#         # element dofs
#         self.dofs = np.array([[self.nodal_labels[0],0],   #dof 0 = axial load
#                               [self.nodal_labels[0],1],   #dof 1 = bending 
#                               [self.nodal_labels[0],2],   #dof 2 = moment 
#                               [self.nodal_labels[1],0],
#                               [self.nodal_labels[1],1],
#                               [self.nodal_labels[1],2]],dtype=np.int32)
        
#         # no temperature dofs
#         self.dofs_q = np.zeros((0,2))
        
#         # rotation matrix in the xy plane
#         s = (self.nodal_coords[1,:2] - self.nodal_coords[0,:2])/self._L
#         t = np.array([-s[1],s[0]])
#         R = np.array([s,t])

#         # global to local transformation matrix in the xy plane
#         self.G = sp.linalg.block_diag(R,[[1]],R,[[1]])

#         # local stiffness matrix
#         self.Kl = np.array([[self._E*self._A/self._L,      0,       0,                   -self._E*self._A/self._L,0,0],
#                             [0,                            12*self._E*self._I/self._L**3,6*self._E*self._I/self._L**2,0, -12*self._E*self._I/self._L**3, 6*self._E*self._I/self._L**2],
#                             [0,                            6*self._E*self._I/self._L**2,4*self._E*self._I/self._L,0,-6*self._E*self._I/self._L**2,2*self._E*self._I/self._L],
#                             [-self._E*self._A/self._L,     0,                   0,self._E*self._A/self._L,0,0],
#                             [0,                            -12*self._E*self._I/self._L**3,-6*self._E*self._I/self._L**2, 0,12*self._E*self._I/self._L**3,-6*self._E*self._I/self._L**2],
#                             [0,                            6*self._E*self._I/self._L**2,   2*self._E*self._I/self._L,0,-6*self._E*self._I/self._L**2,4*self._E*self._I/self._L]],dtype=np.float64)

#         # local mass matrix (TO BE ADDED LATER)
#         Mn = self._A * self._L * self._Rho / 2
#         In = self._A * self._L * self._Rho / 2 * self._L**2 / 3 # TO BE CHECKED !!

#         # mass matrix in local coordinates
#         self.Ml = np.zeros((6,6),dtype=np.float64)       
#         self.Ml = np.diag(np.array([Mn,Mn,In,Mn,Mn,In]))

#         # global stiffness matrix in the xy plane
#         self.K = self.G.transpose() @ self.Kl @ self.G

#         # global mass matrix in the xy plane
#         self.M = self.G.transpose() @ self.Ml @ self.G

#         # damping matrix in global coordinates
#         self.C = np.zeros(self.K.shape).astype(np.float64)

#     #%% extract parameters and assign default values
#     def extract_pars(self,pars):

#         # this is the element class used in packing/unpacking
#         self.my_pars['elem'] = 'beam2d'

#         self._A = float(pars.get('A', 1.0)) # cross-section area
#         self._I = float(pars.get('I', 1.0)) # cross-section inertia
#         self._E = float(pars.get('E', 1.0)) # elastic modulus
#         self._Rho = float(pars.get('Rho', 1.0)) # density

#         # node labels
#         self.nodal_labels = pars.get('nodal_labels', np.array([0, 1], dtype=np.int32)).astype(np.int32)

#         # extract nodal coordinates
#         self.nodal_coords = self.my_nodes.find_coords(self.nodal_labels)

#         # beam2d length
#         self._L = np.linalg.norm(self.nodal_coords[1,:] - self.nodal_coords[0,:])

#     #%% plot the element
#     # def plot(self):#,ax,ue,uscale):

#     #     # plot the beam in 2d
#     #     fig, ax = plt.subplots()
#     #     ax.plot(self.nodal_coords[:, 0], self.nodal_coords[:, 1])
#     #     plt.show()
        
#     def plot(self, ax, x=None, y=None, z=None, color='k-'):
#         if x is None: x = self.nodal_coords[:, 0]
#         if y is None: y = self.nodal_coords[:, 1]
#         if z is None: z = self.nodal_coords[:, 2]

#         # Collect lines
#         lines = [[[x[0], y[0], 0],[x[1], y[1], 0]]]

#         return lines, None
    
#         '''
#         # Add the polygon patch to the axes
#         #ax.add_patch(patches.Polygon(self.node_coord[:,0:2], color='blue', alpha=0.5))
#         ax.plot(self.nodal_coord[:,0],self.nodal_coord[:,1], color='blue')

#         # Update position
#         pos = self.nodal_coord.copy() # be carefull !!!

#         pos[0,0] = pos[0,0] + ue[0] * uscale
#         pos[0,1] = pos[0,1] + ue[1] * uscale
#         pos[1,0] = pos[1,0] + ue[3] * uscale
#         pos[1,1] = pos[1,1] + ue[4] * uscale

#         #ax.add_patch(patches.Polygon(pos[:,0:2], color='red', alpha=0.5))
#         ax.plot(pos[:,0],pos[:,1], color='red')        
#         '''
