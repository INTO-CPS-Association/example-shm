import numpy as np
import scipy as sp
from scipy.sparse import coo_array, csr_array
from methods.packages.yafem.nodes import nodes
from scipy.linalg import block_diag
from methods.packages.yafem.elem.core_elem import core_elem
from methods.packages.yafem.elem.tet10_func import *
from mpl_toolkits.mplot3d.art3d import Line3DCollection


#%% element_MCK class
class tet10(core_elem):

#%% class constructor
    def __init__(self, my_nodes, pars):

        # superclass constructor
        super().__init__(my_nodes,pars)

        # extract parameters and assign default values
        self.extract_pars(pars)

        # element dofs
        self.element_dofs(5)

        # Defining the gauss points and the respective weights
        self.gp, self.gw = self.gl_quadrature_tri(self.gauss_order)

        # vector to corners node 1 to 2 and node 1 to 3
        nodal_corners = self.nodal_coords
        v12 = nodal_corners[1,:] - nodal_corners[0,:]
        v13 = nodal_corners[2,:] - nodal_corners[0,:]

        # normal vector to the plane
        zp = np.linalg.cross(v12,v13)

        # unit vector in the x-direction
        xp = np.array([abs(zp[2]), 0, -abs(zp[0])])
        if 0 < np.dot(xp, zp):
            xp[2] = -xp[2]

        # unit vector in the y-direction
        yp = np.cross(zp, xp)

        # Reciprocal basis vectors
        dx = 1 / np.linalg.norm(xp)
        dy = 1 / np.linalg.norm(yp)
        dz = 1 / np.linalg.norm(zp)

        # Normalize the basis vectors
        xp = xp * dx
        yp = yp * dy
        zp = zp * dz

        self.T = np.array([xp, yp, zp])

        # Transformation matrix for the displacement vector of a single node
        self.G = np.kron(np.eye(10), self.T)

        # Local coordinates
        n_coords_T = self.nodal_coords[:4,:] @ self.T.T

        # Nodal coordinates for the triangle (in global coordinates)
        x1, y1, z1 = n_coords_T[0,:3]
        x2, y2, z2 = n_coords_T[1,:3]
        x3, y3, z3 = n_coords_T[2,:3]
        x4, y4, z4 = n_coords_T[3,:3]

        # Construct the Jacobian matrix J from the global coordinates
        Jac = np.array([[x2 - x1, x3 - x1, x4 - x1],
                        [y2 - y1, y3 - y1, y4 - y1],
                        [z2 - z1, z3 - z1, z4 - z1]])

        # Inverse of the Jacobian matrix
        detJ = np.linalg.det(Jac)  # Compute determinant
        invJ = np.linalg.inv(Jac)  # Compute inverse
        
        # Global coordinates for the four nodes
        global_coords = np.array([[x1, y1, z1],  # Node 1
                                  [x2, y2, z2],  # Node 2
                                  [x3, y3, z3],  # Node 3
                                  [x4, y4, z4],  # Node 4
                                  ])

        # Subtract the first node's global coordinates (x1, y1) from each node
        # to translate the triangle's global coordinates to the local reference system
        global_coords_translated = global_coords - np.array([x1, y1, z1])

        # Vectorized operation: multiply the inverse Jacobian with each translated global coordinate
        n_coords_T = np.dot(global_coords_translated, invJ.T)

        # Adding side-nodes to the local coordinates
        n_coords_T = np.vstack((n_coords_T,
                               (n_coords_T[0,:] + n_coords_T[1,:]) * 0.5,   # Node 5
                               (n_coords_T[0,:] + n_coords_T[2,:]) * 0.5,   # Node 6
                               (n_coords_T[0,:] + n_coords_T[3,:]) * 0.5,   # Node 7
                               (n_coords_T[1,:] + n_coords_T[2,:]) * 0.5,   # Node 8
                               (n_coords_T[2,:] + n_coords_T[3,:]) * 0.5,   # Node 9
                               (n_coords_T[1,:] + n_coords_T[3,:]) * 0.5,   # Node 10
                               ))  

        # Variable function
        variables = lambda r, s, t:  [
                     self.E,
                     self.nu, 
                     r, s, t,
                     n_coords_T[0,0],
                     n_coords_T[1,0],
                     n_coords_T[2,0],
                     n_coords_T[3,0],
                     n_coords_T[4,0],
                     n_coords_T[5,0],
                     n_coords_T[6,0],
                     n_coords_T[7,0],
                     n_coords_T[8,0],
                     n_coords_T[9,0],
                     n_coords_T[0,1],
                     n_coords_T[1,1],
                     n_coords_T[2,1],
                     n_coords_T[3,1],
                     n_coords_T[4,1],
                     n_coords_T[5,1],
                     n_coords_T[6,1],
                     n_coords_T[7,1],
                     n_coords_T[8,1],
                     n_coords_T[9,1],
                     n_coords_T[0,2],
                     n_coords_T[1,2],
                     n_coords_T[2,2],
                     n_coords_T[3,2],
                     n_coords_T[4,2],
                     n_coords_T[5,2],
                     n_coords_T[6,2],
                     n_coords_T[7,2],
                     n_coords_T[8,2],
                     n_coords_T[9,2]
                    ]

        # Variables for the B matrices
        variables_b_matrices =  lambda r, s, t, jac_inv: [
                     jac_inv[0,0], 
                     jac_inv[0,1], 
                     jac_inv[0,2], 
                     jac_inv[1,0], 
                     jac_inv[1,1], 
                     jac_inv[1,2], 
                     jac_inv[2,0], 
                     jac_inv[2,1], 
                     jac_inv[2,2], 
                     r, s, t
                     ]

        # allocating K and M
        Kgs = np.zeros([30,30])
        Mgs = np.zeros([30,30])
        # M_dens = self.rho * np.diag(np.array([self.h,self.h,self.h,self.h**3/12,self.h**3/12]))
        # self.volume = np.sum(self.gw * abs(detJ) / 6)

        for i, gp in enumerate(self.gp):

            r = gp[0]
            s = gp[1]
            t = gp[2]

            # variables
            var = variables(r,s,t)

            # jacobian
            Jac = jac(*var)
            inv_Jac = np.linalg.inv(Jac)

            # variables for strain interpolation matrix B
            var_b = variables_b_matrices(r,s,t,inv_Jac)

            # Strain interpolation matrix
            B_mat = block_diag(inv_Jac, inv_Jac) @ B(*var_b)

            # displacement interpolation matrix N and stiffness matrix D
            N_mat = N(*var)
            D_mat = D(*var)

            # determinant of the jacobian
            dJ = np.linalg.det(Jac)/6 * self.gw[i]

            # inverse jacobian
            if dJ < 0:
                raise ValueError("negative determinant of the jacobian")

            # Gauss-Legendre sum for stiffness
            Kgs += B_mat.T @ D_mat @ B_mat * dJ

            # Gauss-Legendre sum for mass
            Mgs += N_mat.T @ N_mat * self.rho * dJ

            print('determinant jac: ', dJ)

        self.Z = self.fun_mapping(np.array([1, 2, 3, 5, 4, 6]))

        # Local mass and stiffness matrix
        self.Kl = self.Z.T @ Kgs @ self.Z
        self.Ml = self.Z.T @ Mgs @ self.Z

        # Stiffness matrix in global coordinate system
        self.K = self.G.T @ self.Kl @ self.G
        self.M = self.G.T @ self.Ml @ self.G

    def fun_mapping(self, ind):
        Z = np.zeros((len(ind), 6))

        Z[range(len(ind)), abs(ind) - 1] = np.sign(ind)
        Z = block_diag(Z,Z,Z,Z,Z)
                    
        return coo_array(Z,dtype=np.int8).tocsr()




        #     # Loop over Lobatto quadrature points for thickness integration
        #     for j, lp in enumerate(self.lp):

        #         # Compute the real thickness coordinate
        #         t = self.h * 0.5 * lp  # Maps Lobatto points to physical thickness

        #         # Compute weight contribution for thickness integration
        #         dV = self.lw[j] * (self.h / 2)  # Thickness scaling factor

        #         # variables for the B matrices
        #         variables_b_val = variables_b_matrices(r,s,t,invJ)
        #         B_mat = B(*variables_b_val)

        #         # Compute integral contribution
        #         integrand = B_mat.T @ Dpe(*variables_val) @ B_mat

        #         # Adjust weight by det(J)
        #         weight = self.gw[i] * self.lw[j] 
            
        #         # Compute volume element contribution (including thickness)
        #         print(detJ * 0.5)
        #         volume_element = (self.h / 2) * abs(detJ) * 0.5

        #         # Accumulate stiffness matrix (Mindlin-Reissner formulation)
        #         self.Kl += integrand * weight * volume_element

        #         # Accumulate Mass matrix
        #         self.Ml += N_mat.T @ M_dens @ N_mat * self.area * self.gw[i] * dV

        #     # # Stiffness matrix
        #     # self.Kl = B_mat.T @ Dpe(*variables_val) @ B_mat * area_val * self.gw[i]

        #     # # Mass matrix
        #     # self.Ml += N_mat.T @ M_dens @ N_mat * area_val * self.gw[i]

        # # Stiffness matrix in global coordinate system
        # self.K = self.G.T @ self.Kl @ self.G
        # self.M = self.G.T @ self.Ml @ self.G


        # # Stiffness matrix in global coordinate system
        # # self.K = self.G.T @ self.Kl @ self.G
        # # self.M = self.G.T @ self.Ml @ self.G

        # # damping matrix in global coordinates
        # self.C = np.zeros_like(self.K)

#%% extract parameters and assign default values
    def extract_pars(self,pars):

        # this is the element class used in packing/unpacking
        self.my_pars['elem'] = 'tet10'


        self.E   = pars.get('E', 210e9) # young's modulus
        self.nu  = pars.get('nu', 0.3) # poisson's ratio
        self.rho = pars.get('rho', 7850) # material density
        self.h   = pars.get('h', 5e-3) # element thickness
        self.k   = pars.get('k', 5/6)  # shear factor
        self.nodal_labels = pars.get("nodal_labels", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.nodal_coords = self.my_nodes.find_coords(self.nodal_labels) # extract nodal coordinates
        self.gauss_order  = pars.get("gauss_order", 2)  # number of Gauss points
        self.type    = pars.get("type", "ps")  # type of analysis (ps = plane stress, pe = plane strain, ax = axisymmetric)

        # temperature controlled dofs
        self.dofs_q = pars.get('dofs_q', np.zeros((0, 2), dtype=np.int32)).astype(np.int32)

#%% element dofs
    def element_dofs(self, dofs_per_node):
        self.dofs = np.empty([dofs_per_node*6,2],dtype=int)

        self.dofs[0:dofs_per_node,0]                  = self.nodal_labels[0] # Label of first node
        self.dofs[dofs_per_node*1:dofs_per_node*2,0]  = self.nodal_labels[1] # Label of second node
        self.dofs[dofs_per_node*2:dofs_per_node*3,0]  = self.nodal_labels[2] # Label of third node
        self.dofs[dofs_per_node*3:dofs_per_node*4,0]  = self.nodal_labels[3] # Label of fourth node
        self.dofs[dofs_per_node*4:dofs_per_node*5,0]  = self.nodal_labels[4] # Label of fifth node
        self.dofs[dofs_per_node*5:dofs_per_node*6,0]  = self.nodal_labels[5] # Label of sixth node
        self.dofs[dofs_per_node*6:dofs_per_node*7,0]  = self.nodal_labels[6] # Label of sevetnth node
        self.dofs[dofs_per_node*7:dofs_per_node*8,0]  = self.nodal_labels[7] # Label of eigthth node
        self.dofs[dofs_per_node*8:dofs_per_node*9,0]  = self.nodal_labels[8] # Label of ninthth node
        self.dofs[dofs_per_node*9:dofs_per_node*10,0] = self.nodal_labels[9] # Label of tenth node
        self.dofs[:,1] = np.tile(np.arange(0,dofs_per_node), 6) + 1 # Dofs of all nodes
    
        return self.dofs

#%% Gauss quadrature for triangular elements
    def gl_quadrature_tri(self, order):
        if order == 1:
            x = np.array([[1, 1]]) * 1/3
            w = np.array([1.0])

        elif order == 2:
            x = np.array([[1/6, 1/6, 1/6], 
                          [2/3, 1/6, 1/6], 
                          [1/6, 2/3, 1/6], 
                          [1/6, 1/6, 2/3]])
            w = np.array([1, 1, 1, 1]) * 0.25

        elif order == 3:
            gamma_1 = -27/48
            gamma_2 =  25/48
            x = np.array([[1/3, 1/3], [0.6, 0.2], [0.2, 0.6], [0.2, 0.2]])
            w = np.array([gamma_1, gamma_2, gamma_2, gamma_2])

        elif order == 4:
            alpha_1 = 0.8168475730
            alpha_2 = 0.1081030182
            beta_1  = 0.0915762135
            beta_2  = 0.4459484909
            gamma_3 = 0.2199034874 / 2
            gamma_4 = 0.4467631794 / 2
            x = np.array([[beta_1,  beta_1], 
                          [alpha_1, beta_1], 
                          [beta_1, alpha_1], 
                          [alpha_2, beta_2], 
                          [beta_2, alpha_2], 
                          [beta_2, beta_2]])

            w = np.array([gamma_3, gamma_3, gamma_3, gamma_4, gamma_4, gamma_4])
            
        else:
            raise ValueError("Unsupported order")
        return x, w

#%% Plot 3d elements
    def plot(self, ax, x=None, y=None, z=None, color='cyan'):
        if x is None: x = self.nodal_coords[:, 0]
        if y is None: y = self.nodal_coords[:, 1]
        if z is None: z = self.nodal_coords[:, 2]
            
        # Subdivide 6-node triangle into 4 smaller 3-node triangles
        triangles = np.array([[0, 4, 5],    # Node 1 5 6 # xy triangle
                              [4, 1, 7],    # Node 5 2 8
                              [5, 7, 2],    # Node 6 8 3
                              [4, 7, 5],    # Node 5 8 6

                              [0, 4, 6],    # Node 1 5  7 # xz triangle
                              [4, 1, 9],    # Node 5 2  10
                              [6, 9, 3],    # Node 7 10 4
                              [6, 4, 9],    # Node 7 5  10

                              [0, 5, 6],    # Node 1 6 7 # yz triangle
                              [5, 2, 8],    # Node 6 3 9
                              [6, 8, 3],    # Node 7 9 4
                              [6, 5, 8],    # Node 7 6 9

                              [1, 7, 9],    # Node 2  8 10 # incline triangle
                              [9, 8, 3],    # Node 10 9 4
                              [7, 2, 8],    # Node 8  3 9
                              [9, 7, 8],    # Node 10 8 9
                              ]) 

         # Collect surface triangles using a lambda function
        surfaces_func = lambda row: \
            [[x[triangles[row, 0]], y[triangles[row, 0]], z[triangles[row, 0]]],
             [x[triangles[row, 1]], y[triangles[row, 1]], z[triangles[row, 1]]],
             [x[triangles[row, 2]], y[triangles[row, 2]], z[triangles[row, 2]]]]

        surfaces = [surfaces_func(0), # xy triangle
                    surfaces_func(1),
                    surfaces_func(2),
                    surfaces_func(3),

                    surfaces_func(4), # xz triangle
                    surfaces_func(5),
                    surfaces_func(6),
                    surfaces_func(7),

                    surfaces_func(8), # yz triangle
                    surfaces_func(9),
                    surfaces_func(10),
                    surfaces_func(11),

                    surfaces_func(12), # incline triangle
                    surfaces_func(13),
                    surfaces_func(14),
                    surfaces_func(15),
                    ]

        line_func = lambda N1,N2: [[x[N1], y[N1], z[N1]], [x[N2], y[N2], z[N2]]]

        # Convert edges to line segments in the correct format
        lines = [line_func(0,4), # xy triangle
                 line_func(4,1),
                 line_func(1,7),
                 line_func(7,2),
                 line_func(2,5),
                 line_func(5,0),

                 line_func(1,9), # xz triangle
                 line_func(9,3),
                 line_func(3,6),
                 line_func(6,0),

                 line_func(2,8), # xz triangle
                 line_func(8,3),
                ]

        return lines, surfaces
