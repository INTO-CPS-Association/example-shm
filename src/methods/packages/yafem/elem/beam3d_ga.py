import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.linalg import block_diag
from methods.packages.yafem.nodes import nodes
#from yafem.elem.core_elem import core_elem
from core_elem_ga import core_elem # get customized version (GA)
#from yafem.elem.beam3d_circ_func import *
#from yafem.elem.beam3d_gen_func import *
from beam3d_circ_func import * # get customized version (GA)
from beam3d_gen_func import * # get customized version (GA)

class beam3d(core_elem):
    #%% class constructor
    def __init__(self, my_nodes, pars):

        # superclass constructor
        super().__init__(my_nodes,pars)

        # link the nodes to the element
        self.my_nodes = my_nodes
        
        # extract parameters and assign default values
        self.extract_pars(pars)

        # set the number of dofs per node
        self.element_dofs(6)

        # Coordinate transformation matrix calculation
        r = self.nodal_coords[1] - self.nodal_coords[0]

        # Find indices of non-zero elements
        x_ind = np.nonzero(r)[0]

        # Check the value of x_ind[0] and calculate s accordingly
        if x_ind[0] == 0:
            s = np.array([-r[1], r[0], 0])
        elif x_ind[0] == 1:
            s = np.array([-r[1], r[0], 0])
        elif x_ind[0] == 2:
            s = np.array([0, 1, 0])

        # Calculate t as the cross product of r and s
        t = np.cross(r, s)

        # Normalize r, s, and t
        r = r / np.linalg.norm(r)
        s = s / np.linalg.norm(s)
        t = t / np.linalg.norm(t)

        # Local reference system
        self.T = np.array([r, s, t])
        
        # Transformation matrix for the displacement vector of a single node
        # Assuming BlockDiagonal is a placeholder for an actual block diagonal matrix construction
        # For simplicity, using np.kron (Kronecker product) to simulate block diagonal behavior
        self.G = np.kron(np.eye(4), self.T)  # Adjust based on actual BlockDiagonal implementation

        if self.shape == 'circular':

            # Variables
            variables = [self.D1, self.D2, self.E, self.G1, self.H, self.L, self.alpha, self.fa, self.fby, self.fbz, self.k0a, self.k0b, self.rho, self.theta]

            # Axial components
            Ka   = beam3d_circ_Ka(*variables)
            Kwa  = beam3d_circ_Kwa(*variables)
            Ma   = beam3d_circ_Ma(*variables)
            fca  = beam3d_circ_fca(*variables)
            fta  = beam3d_circ_fta(*variables)
            
            # Lateral components y
            Kby  = beam3d_circ_Kby(*variables)  
            Kwby = beam3d_circ_Kwby(*variables)    
            Mby  = beam3d_circ_Mby(*variables)  
            fcby = beam3d_circ_fcby(*variables)   
            
            # Lateral components z
            Kbz  = beam3d_circ_Kbz(*variables)  
            Kwbz = beam3d_circ_Kwbz(*variables)
            Mbz  = beam3d_circ_Mbz(*variables)  
            fcbz = beam3d_circ_fcbz(*variables)
            
            # Torsional components
            Kt   = beam3d_circ_Kt(*variables) 
            Mt   = beam3d_circ_Mt(*variables)

            # Displacement interpolation matrices
            Na = beam3d_circ_Na_mid(*variables)
            Nby = beam3d_circ_Nby_mid(*variables)
            Nbz = beam3d_circ_Nbz_mid(*variables)

            # Strain interpolation matrices
            Ba = beam3d_circ_Ba_mid(*variables)
            Bby = beam3d_circ_Bby_mid(*variables)
            Bbz = beam3d_circ_Bbz_mid(*variables)

            # cross-section stiffness matrix
            self.D = beam3d_circ_Dcs_mid(*variables)

        elif self.shape == 'generic':
            
            # Variables
            variables = [self.A, self.E, self.G1, self.Ixx, self.Iyy, self.Jv, self.L, self.alpha, self.fa, self.fby, self.fbz, self.k0a, self.k0b, self.rho, self.theta]

            # Axial components
            Ka   = beam3d_gen_Ka(*variables)
            Kwa  = beam3d_gen_Kwa(*variables)
            Ma   = beam3d_gen_Ma(*variables)
            fca  = beam3d_gen_fca(*variables)
            fta  = beam3d_gen_fta(*variables)
            
            # Lateral components y
            Kby  = beam3d_gen_Kby(*variables)  
            Kwby = beam3d_gen_Kwby(*variables)    
            Mby  = beam3d_gen_Mby(*variables)  
            fcby = beam3d_gen_fcby(*variables)   
            
            # Lateral components z
            Kbz  = beam3d_gen_Kbz(*variables)  
            Kwbz = beam3d_gen_Kwbz(*variables)
            Mbz  = beam3d_gen_Mbz(*variables)  
            fcbz = beam3d_gen_fcbz(*variables)
            
            # Torsional components
            Kt   = beam3d_gen_Kt(*variables) 
            Mt   = beam3d_gen_Mt(*variables)

            # Displacement interpolation matrices
            Na = beam3d_gen_Na_mid(*variables)
            Nby = beam3d_gen_Nby_mid(*variables)
            Nbz = beam3d_gen_Nbz_mid(*variables)

            # strain interpolation matrices
            Ba = beam3d_gen_Ba_mid(*variables)
            Bby = beam3d_gen_Bby_mid(*variables)
            Bbz = beam3d_gen_Bbz_mid(*variables)

            # cross-section stiffness matrix
            self.D = beam3d_gen_Dcs_mid(*variables)
        
        # Indexes for stiffness assembly
        inda  = [0, 6]  # Indices for axial properties, adjusted for Python indexing
        indbz = [2, 4, 8, 10]  # Indices for lateral properties z, adjusted for Python indexing
        indby = [1, 5, 7, 11]  # Indices for lateral properties y, adjusted for Python indexing
        indt  = [3, 9]  # Indices for torsional properties, adjusted for Python indexing

        # Stiffness matrix in local coordinate system
        self.Kl = np.zeros((12, 12))
        self.Ml = self.Kl.copy()
        self.rl = np.zeros((12, 1))

        #%% Axial properties
        # Combined axial rod + winkler
        self.Kl[np.ix_(inda, inda)] += Ka + Kwa

        # Axial mass matrix
        self.Ml[np.ix_(inda, inda)] += Ma

        # Mechanical and Thermal load vector
        self.rl[inda] += (fca + fta)

        #%% Lateral properties
        # Lateral stiffness
        self.Kl[np.ix_(indby, indby)] += Kby + Kwby
        self.Kl[np.ix_(indbz, indbz)] += Kbz + Kwbz

        # Lateral mass matrix
        self.Ml[np.ix_(indby, indby)] += Mby
        self.Ml[np.ix_(indbz, indbz)] += Mbz

        # Mechanical and Thermal load vector
        self.rl[indby] += fcby
        self.rl[indbz] += fcbz

        #%% Torsional properties
        # Stiffness
        self.Kl[np.ix_(indt, indt)] += Kt

        # Mass
        self.Ml[np.ix_(indt, indt)] += Mt

        # Displacement interpolation matrix in the mid point
        self.Nl = np.zeros((3, 12))
        self.Nl[np.ix_(np.array([0]), inda)]  += Na.squeeze() # axial displacement
        self.Nl[np.ix_(np.array([1]), indby)] += Nby.squeeze() # lateral displacement y
        self.Nl[np.ix_(np.array([2]), indbz)] += Nbz.squeeze() # lateral displacement z

        # Strain interpolation matrix in the mid point
        self.Bl = np.zeros((3, 12))
        self.Bl[np.ix_(np.array([0]), inda)]  += Ba.squeeze() # axial strain
        self.Bl[np.ix_(np.array([1]), indby)] += Bby.squeeze() # curvature in y
        self.Bl[np.ix_(np.array([2]), indbz)] += Bbz.squeeze() # curvature in z

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
 
        self.Ka   = Ka
        self.Kwa  = Kwa
        self.Ma   = Ma
        self.fca  = fca
        self.fta  = fta
        self.Kby  = Kby
        self.Kbz  = Kbz
        self.Kwby = Kwby
        self.Kwbz = Kwbz
        self.Mby  = Mby
        self.Mbz  = Mbz
        self.fcby = fcby
        self.fcbz = fcbz
        self.Kt   = Kt
        self.Mt   = Mt

    #%% extract parameters
    def extract_pars(self, pars):

        self.shape    = pars.get("shape", 'circular') # Youngs modulus

        if self.shape == 'circular':
            self.D1   = pars.get("D1", 20.0) # Outer diameter of pipe in firste node
            self.D2   = pars.get("D2", 20.0) # Outer diameter of pipe in second node
            self.H    = pars.get("H", 2) # thickness of pipe in both ends
        
        elif self.shape == 'generic':
            self.A    = pars.get("A", 200.0) # Cross-sectional areal
            self.Ixx  = pars.get("Ixx", 1000.0) # second area moment about xx
            self.Iyy  = pars.get("Iyy", 1000.0) # second area moment about yy
            self.Jv   = pars.get("Jv", 10000.0) # Torsional constant
 
        self.E     = pars.get("E", 210e3) # Youngs modulus
        self.G1    = pars.get("G", 81e3) # Shear modulus
        self.k0a   = pars.get("k0a", 0.0) # Axial Winkler stiffness
        self.k0b   = pars.get("k0b", 0.0) # Lateral Winkler stiffness
        self.rho   = pars.get("rho", 7850/1e9) # Density
        self.fa    = pars.get("fa", 0.0) # Axial element destributed force
        self.fby   = pars.get("fby", 0.0) # Lateral element destributed force in y-direction
        self.fbz   = pars.get("fbz", 0.0) # Lateral element destributed force in z-direction
        self.alpha = pars.get("alpha", 0.0) # coefficient of thermal expansion 
        self.theta = pars.get("theta", 0.0) # Thermal loading
        self.nodal_labels = pars.get("nodal_labels", [1, 2])
        
        # extract nodal coordinates
        self.nodal_coords = self.my_nodes.find_coords(self.nodal_labels)
        self.L = np.linalg.norm(self.nodal_coords[1] - self.nodal_coords[0])
    
        # temperature controlled dofs
        self.dofs_q = np.array(pars.get("dofs_q", []), dtype=np.int32).reshape(-1, 2) if "dofs_q" in pars else np.zeros((0, 2), dtype=np.int32)

    #    self.nu    = pars.get("nu", 0.3)
    #    self.J     = pars.get("J", 1.0)
    
    #%% Computing element dofs
    def element_dofs(self, dofs_per_node):

        self.dofs = np.empty([dofs_per_node*2,2],dtype=int)

        self.dofs[0:dofs_per_node,0] = self.nodal_labels[0] # Label of first node
        self.dofs[dofs_per_node:,0]  = self.nodal_labels[1] # Label of second node
        self.dofs[:,1] = np.tile(np.arange(0,dofs_per_node), 2) + 1 # Dofs of both nodes
    
        return self.dofs

    #%% Plot 3d elements
    def plot(self, ax, x=None, y=None, z=None, color='k-'):
        if x is None: x = self.nodal_coords[:, 0]
        if y is None: y = self.nodal_coords[:, 1]
        if z is None: z = self.nodal_coords[:, 2]

        ax.plot(x, y, z, color, linewidth=1)
        
        return ax  # Return the same axis object
    
    def dump_to_paraview(self):
        # here it goes the dump_to_paraview implementation for the beam3d element
        pass
