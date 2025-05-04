import numpy as np
import scipy as sp
from methods.packages.yafem.nodes import nodes
from methods.packages.yafem.elem.core_elem import core_elem
from methods.packages.yafem.elem.tri6_func import *
from mpl_toolkits.mplot3d.art3d import Line3DCollection

#%% element_MCK class
class tri6(core_elem):

#%% class constructor
    def __init__(self, my_nodes, pars):

        # superclass constructor
        super().__init__(my_nodes,pars)

        # link the nodes to the element
        self.my_nodes = my_nodes

        # extract parameters and assign default values
        self.extract_pars(pars)

        # element dofs
        self.element_dofs(5)

        # Defining the gauss points and the respective weights
        self.gp, self.gw = self.gl_quadrature_tri(self.gauss_order)

        # Get Lobatto quadrature points and weights for thickness integration
        self.lp, self.lw = self.lobatto_quadrature(self.gauss_order)

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
        n_coords_T = self.nodal_coords[:3,:] @ self.T.T

        # Nodal coordinates for the triangle (in global coordinates)
        x1, y1 = n_coords_T[0,:2]
        x2, y2 = n_coords_T[1,:2]
        x3, y3 = n_coords_T[2,:2]

        # Construct the Jacobian matrix J from the global coordinates
        jac = np.array([[x2 - x1, x3 - x1],
                        [y2 - y1, y3 - y1]])
        
        # Inverse of the Jacobian matrix
        detJ = np.linalg.det(jac)  # Compute determinant
        invJ = np.linalg.inv(jac)  # Compute inverse
        
        # Global coordinates for the three nodes
        global_coords = np.array([
            [x1, y1],  # Node 1
            [x2, y2],  # Node 2
            [x3, y3]   # Node 3
        ])

        # Subtract the first node's global coordinates (x1, y1) from each node
        # to translate the triangle's global coordinates to the local reference system
        global_coords_translated = global_coords - np.array([x1, y1])

        # Vectorized operation: multiply the inverse Jacobian with each translated global coordinate
        n_coords_T = np.dot(global_coords_translated, invJ.T)

        # Adding side-nodes to the local coordinates
        n_coords_T = np.vstack((n_coords_T,
                               (n_coords_T[0,:] + n_coords_T[1,:]) * 0.5,
                               (n_coords_T[1,:] + n_coords_T[2,:]) * 0.5,
                               (n_coords_T[2,:] + n_coords_T[0,:]) * 0.5))

        print('n_coords_T: ',n_coords_T)

        # Variable function
        variables = lambda r, s:  [
                     self.E,
                     self.nu, 
                     r, s, 
                     n_coords_T[0,0], 
                     n_coords_T[1,0], 
                     n_coords_T[2,0], 
                     n_coords_T[3,0], 
                     n_coords_T[4,0], 
                     n_coords_T[5,0], 
                     n_coords_T[0,1], 
                     n_coords_T[1,1], 
                     n_coords_T[2,1], 
                     n_coords_T[3,1], 
                     n_coords_T[4,1], 
                     n_coords_T[5,1], 
                    ]

        # Variables for the B matrices
        variables_b_matrices =  lambda r, s, t, jac_inv: [
                     jac_inv[0,0], 
                     jac_inv[0,1], 
                     jac_inv[1,0], 
                     jac_inv[1,1], 
                     r, s, t
                     ]

        # allocating K and M
        result = 0
        self.Kl = np.zeros([30,30])
        self.Ml = np.zeros([30,30])
        M_dens = self.rho * np.diag(np.array([self.h,self.h,self.h,self.h**3/12,self.h**3/12]))

        self.area = np.sum(self.gw * abs(detJ) * 0.5)

        for i, gp in enumerate(self.gp):

            r = gp[0]
            s = gp[1]

            # variables
            variables_val = variables(r,s)

            # inverse jacobian
            if np.abs(detJ) < 1e-8:
                raise ValueError("Jacobian determinant is too close to zero, possible element distortion!")

            # area value along with N and B matrix
            area_val = area(*variables_val)
            N_mat    = N(*variables_val)

            # J = jac(*variables_val)

            # Print the intermediate area_val for debugging
            area_val = area(*variables_val)

            # Loop over Lobatto quadrature points for thickness integration
            for j, lp in enumerate(self.lp):

                # Compute the real thickness coordinate
                t = self.h * 0.5 * lp  # Maps Lobatto points to physical thickness

                # Compute weight contribution for thickness integration
                dV = self.lw[j] * (self.h / 2)  # Thickness scaling factor

                # variables for the B matrices
                variables_b_val = variables_b_matrices(r,s,t,invJ)
                B_mat = B(*variables_b_val)

                # Compute integral contribution
                integrand = B_mat.T @ D(*variables_val) @ B_mat

                # Adjust weight by det(J)
                weight = self.gw[i] * self.lw[j] 
            
                # Compute volume element contribution (including thickness)
                print(detJ * 0.5)
                volume_element = (self.h / 2) * abs(detJ) * 0.5

                # Accumulate stiffness matrix (Mindlin-Reissner formulation)
                self.Kl += integrand * weight * volume_element

                # Accumulate Mass matrix
                self.Ml += N_mat.T @ M_dens @ N_mat * self.area * self.gw[i] * dV

            # # Stiffness matrix
            # self.Kl = B_mat.T @ Dpe(*variables_val) @ B_mat * area_val * self.gw[i]

            # # Mass matrix
            # self.Ml += N_mat.T @ M_dens @ N_mat * area_val * self.gw[i]

        # Stiffness matrix in global coordinate system
        self.K = self.G.T @ self.Kl @ self.G
        self.M = self.G.T @ self.Ml @ self.G


        # Stiffness matrix in global coordinate system
        # self.K = self.G.T @ self.Kl @ self.G
        # self.M = self.G.T @ self.Ml @ self.G

        # damping matrix in global coordinates
        self.C = np.zeros_like(self.K)

#%% extract parameters and assign default values
    def extract_pars(self,pars):

        # this is the element class used in packing/unpacking
        self.my_pars['elem'] = 'tri6'

        self.E   = pars.get('E', 210e9) # young's modulus
        self.nu  = pars.get('nu', 0.3) # poisson's ratio
        self.rho = pars.get('rho', 7850) # material density
        self.h   = pars.get('h', 5e-3) # element thickness
        self.k   = pars.get('k', 5/6)  # shear factor
        self.nodal_labels = pars.get("nodal_labels", [1, 2, 3, 4, 5, 6])
        self.nodal_coords = self.my_nodes.find_coords(self.nodal_labels) # extract nodal coordinates
        self.gauss_order  = pars.get("gauss_order", 2)  # number of Gauss points
        self.type    = pars.get("type", "ps")  # type of analysis (ps = plane stress, pe = plane strain, ax = axisymmetric)

        # temperature controlled dofs
        self.dofs_q = pars.get('dofs_q', np.zeros((0, 2), dtype=np.int32)).astype(np.int32)

#%% element dofs
    def element_dofs(self, dofs_per_node):
        self.dofs = np.empty([dofs_per_node*6,2],dtype=int)

        self.dofs[0:dofs_per_node,0]                 = self.nodal_labels[0] # Label of first node
        self.dofs[dofs_per_node*1:dofs_per_node*2,0] = self.nodal_labels[1] # Label of second node
        self.dofs[dofs_per_node*2:dofs_per_node*3,0] = self.nodal_labels[2] # Label of third node
        self.dofs[dofs_per_node*3:dofs_per_node*4,0] = self.nodal_labels[3] # Label of fourth node
        self.dofs[dofs_per_node*4:dofs_per_node*5,0] = self.nodal_labels[4] # Label of fifth node
        self.dofs[dofs_per_node*5:dofs_per_node*6,0] = self.nodal_labels[5] # Label of sixth node
        self.dofs[:,1] = np.tile(np.arange(0,dofs_per_node), 6) + 1 # Dofs of all nodes
    
        return self.dofs

#%% Gauss quadrature for triangular elements
    def gl_quadrature_tri(self, order):
        if order == 1:
            x = np.array([[1, 1]]) * 1/3
            w = np.array([1.0])

        elif order == 2:
            x = np.array([[1/6, 1/6], [2/3, 1/6], [1/6, 2/3]])
            # x = np.array([[1/2,   0], [0, 1/2], [1/2, 1/2]])
            w = np.array([1, 1, 1]) * 1/3

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

    def lobatto_quadrature(self, order):
        """
        Returns Lobatto quadrature points and weights for 1D integration in [-1,1].
        
        Parameters:
        - order: Number of quadrature points.
        
        Returns:
        - z: Array of Lobatto points in [-1,1]
        - w: Corresponding weights
        """
        if order == 2:
            # 2-point Lobatto (same as Trapezoidal Rule)
            z = np.array([-1, 1])
            w = np.array([1, 1])  # Weights sum to 2

        elif order == 3:
            # 3-point Lobatto
            z = np.array([-1, 0, 1])
            w = np.array([1/3, 4/3, 1/3])

        elif order == 4:
            # 4-point Lobatto
            z = np.array([-1, -np.sqrt(5)/5, np.sqrt(5)/5, 1])
            w = np.array([1/6, 5/6, 5/6, 1/6])

        # elif order == 5:
        #     # 5-point Lobatto
        #     z = np.array([-1, -np.sqrt(21)/7, 0, np.sqrt(21)/7, 1])
        #     w = np.array([1/10, 49/90, 32/45, 49/90, 1/10])

        else:
            raise ValueError("Unsupported Lobatto order")
        
        return z, w



#%% Plot 3d elements
    def plot(self, ax, x=None, y=None, z=None, color='cyan'):
        if x is None: x = self.nodal_coords[:, 0]
        if y is None: y = self.nodal_coords[:, 1]
        if z is None: z = self.nodal_coords[:, 2]
            
        # Subdivide 6-node triangle into 4 smaller 3-node triangles
        triangles = np.array([[0, 3, 5],    # Node 1 4 6
                              [3, 1, 4],    # Node 4 2 5
                              [5, 4, 2],    # Node 6 5 3
                              [3, 4, 5]])   # Node 4 5 6

         # Collect surface triangles using a lambda function
        surfaces_func = lambda row: \
            [[x[triangles[row, 0]], y[triangles[row, 0]], z[triangles[row, 0]]],
             [x[triangles[row, 1]], y[triangles[row, 1]], z[triangles[row, 1]]],
             [x[triangles[row, 2]], y[triangles[row, 2]], z[triangles[row, 2]]]]

        surfaces = [surfaces_func(0),
                    surfaces_func(1),
                    surfaces_func(2),
                    surfaces_func(3)]

        # Convert edges to line segments in the correct format
        lines = [[[x[0], y[0], z[0]], [x[3], y[3], z[3]]], # [0, 3]
                 [[x[3], y[3], z[3]], [x[1], y[1], z[1]]], # [3, 1]
                 [[x[1], y[1], z[1]], [x[4], y[4], z[4]]], # [1, 4]
                 [[x[4], y[4], z[4]], [x[2], y[2], z[2]]], # [4, 2]
                 [[x[2], y[2], z[2]], [x[5], y[5], z[5]]], # [2, 5]
                 [[x[5], y[5], z[5]], [x[0], y[0], z[0]]]] # [5, 0]

        return lines, surfaces
