import numpy as np
from scipy.sparse import coo_array, csr_array
from scipy.linalg import block_diag
from methods.packages.yafem.nodes import nodes
from methods.packages.yafem.elem.core_elem import core_elem
from methods.packages.yafem.elem.plate_func import *
from methods.packages.yafem.elem.solid_func import *

class shell4(core_elem):

    #%% class constructor
    def __init__(self, my_nodes, pars):

        # superclass constructor
        super().__init__(my_nodes,pars)
        
        # extract parameters and assign default values
        self.extract_pars(pars)

        # element dofs
        self.dofs = self.element_dofs(6)
        
        # Calculate the mean of nodal coordinates
        r0 = np.mean(self.nodal_coords, axis=0)
        
        xp = (self.nodal_coords[1, :] + self.nodal_coords[2, :]) / 2 - r0
        xp = xp / np.linalg.norm(xp)

        yp = (self.nodal_coords[2, :] + self.nodal_coords[3, :]) / 2 - r0
        yp = yp - np.dot(yp, xp)
        yp = yp / np.linalg.norm(yp)

        zp = np.cross(xp, yp)

        self.xe = self.nodal_coords
        self.xe_plot = self.xe

        self.xep = np.dot(self.xe - r0, np.column_stack((xp, yp)))
        self.xe = self.xep

        # Local reference system
        self.T = np.array([xp, yp, zp])

        # Transformation matrix for the displacement vector of a single node
        # Assuming BlockDiagonal is a placeholder for an actual block diagonal matrix construction
        # For simplicity, using np.kron (Kronecker product) to simulate block diagonal behavior
        # self.G = np.kron(np.eye(8), self.T)  # Adjust based on actual BlockDiagonal implementation

        self.G = np.zeros((24, 24))
        self.G[0:3, 0:3] = self.T
        self.G[3:6, 3:6] = self.T
        self.G[6:9, 6:9] = self.T
        self.G[9:12, 9:12] = self.T
        self.G[12:15, 12:15] = self.T
        self.G[15:18, 15:18] = self.T
        self.G[18:21, 18:21] = self.T
        self.G[21:24, 21:24] = self.T


        inds = np.array([1, 2])
        indp = np.array([3, -5, 4])
        indd = np.array([6])

        self.Zs = self.fun_mapping(inds)
        self.Zp = self.fun_mapping(indp)
        self.Zd = self.fun_mapping(indd)
                
        d = np.zeros((24, 1))

        self.ds = self.Zs.dot(self.G.dot(d))
        self.dp = self.Zp.dot(self.G.dot(d))
        self.dd = self.Zd.dot(self.G.dot(d))

        self.compute_solid_pars()
        self.compute_plate_pars()
        self.compute_drilling_pars()

        self.Kl  = np.zeros((24, 24))
        self.Ml  = np.zeros((24, 24))
        self.fcl = np.zeros((24, 1))
        self.ftl = np.zeros((24, 1))

        # Local stiffness matrix of the shell element
        self.Kl += self.Zs.T @ self.Kgs @ self.Zs
        self.Kl += self.Zp.T @ self.Kgp @ self.Zp
        self.Kl += self.Zd.T @ self.Kgd @ self.Zd

        # Local mass matrix of the shell element
        self.Ml += self.Zs.T @ self.Mgs @ self.Zs
        self.Ml += self.Zp.T @ self.Mgp @ self.Zp
        self.Ml += self.Zd.T @ self.Mgd @ self.Zd

        # Local consistent nodal load vector
        self.fcl += self.Zs.T @ self.fcgs
        self.fcl += self.Zp.T @ self.fcgp
        self.fcl += self.Zd.T @ self.fcgd

        # Thermo mechanical load vector
        self.ftl += self.Zs.T @ self.ftgs
        self.ftl += self.Zp.T @ self.ftgp
        self.ftl += self.Zd.T @ self.ftgd

        # Element matrices and vectors in global reference system (model)
        self.Kg  = self.G.T @ self.Kl @ self.G
        self.Mg  = self.G.T @ self.Ml @ self.G
        self.fcg = self.G.T @ self.fcl
        self.ftg = self.G.T @ self.ftl
        self.K = self.Kg
        self.M = self.Mg
        self.C = np.zeros(self.K.shape)

    def element_dofs(self, dofs_per_node): 
        self.dofs = np.empty([dofs_per_node*4,2],dtype=int)

        self.dofs[0:dofs_per_node,0]                  = self.nodal_labels[0] # Label of first node
        self.dofs[dofs_per_node*1:dofs_per_node*2,0]  = self.nodal_labels[1] # Label of second node
        self.dofs[dofs_per_node*2:dofs_per_node*3,0]  = self.nodal_labels[2] # Label of third node
        self.dofs[dofs_per_node*3:dofs_per_node*4,0]  = self.nodal_labels[3] # Label of fourth node
        self.dofs[:,1] = np.tile(np.arange(0,dofs_per_node), 4) + 1 # Dofs of all nodes
    
        return self.dofs

    def gl_quadrature(self, n):
        """
        Gauss-Legendre quadrature rule in Python.
        
        :param n: Number of points
        :return: points (s) and weights (w)
        """
        s = {
            1: [0],
            2: [-0.577350, 0.577350],
            3: [-0.774597, 0        , 0.774597],
            4: [-0.861136, -0.339981, 0.339981, 0.861136],
            5: [-0.906179, -0.538469, 0.000000, 0.538469, 0.906179]
            }

        w = {
            1: [2],
            2: [1       , 1],
            3: [5/9     , 8/9     , 5/9],
            4: [0.347855, 0.652145, 0.652145, 0.347855],
            5: [0.236926, 0.478628, 0.568888, 0.478628, 0.236926]
            }

        return s[n], w[n]
    
    # def polyarea(self, xe):
    #         """
    #         Calculate the area of a polygon given its vertices in the form of a 2D array.
            
    #         Parameters:
    #         xe (list of lists or numpy array): A 2D array where each row contains the x and y coordinates of a vertex.
            
    #         Returns:
    #         float: The area of the polygon.
    #         """
    #         A2 = 0
    #         n = len(xe)
    #         for i in range(n):
    #             j = (i + 1) % n  # Get the next index, wrap around to 0 if at the end
    #             P = [[xe[i][0], xe[i][1]], [xe[j][0], xe[j][1]]]
    #             A2 += P[0][0]*P[1][1] - P[1][0]*P[0][1]  # Determinant of P
    #         return abs(A2 / 2)

    def polyarea(self, xe):
        # xe = np.asarray(xe)
        x = xe[:, 0]
        y = xe[:, 1]
        x_next = np.concatenate((x[1:], [x[0]]))  # Shift x-coordinates
        y_next = np.concatenate((y[1:], [y[0]]))  # Shift y-coordinates
        A2 = np.sum(x * y_next - x_next * y)
        return abs(A2 / 2)


    #%% Mapping
    
    def fun_mapping(self, ind):
        Z = np.zeros((len(ind), 6))

        Z[range(len(ind)), abs(ind) - 1] = np.sign(ind)
        Z = block_diag(Z,Z,Z,Z)
                      
        return coo_array(Z,dtype=np.int8).tocsr()

    #%% Solid behavior

    def compute_solid_pars(self, ds=None):
        """
        Compute the solid parameters for the element.
        """
        if ds is None:
            ds = np.zeros((8, 1))

        # Assuming e_fun_solid is an object or module that contains the functions Dps, Dpe, and Dax
        type_to_D = {
            'ps': solid_Dps,
            'pe': solid_Dpe,
            'ax': solid_Dax
        }

        # Assuming 'e' is an object that has attributes 'type', 'E', and 'nu'
        # Attempt to get the function based on e.type, default to raising an error if not found
        if self.type in type_to_D:
            D = type_to_D[self.type]
            self.D = D(self.E, self.nu)  # Call the function with e.E and e.nu as arguments
        else:
            raise ValueError("Type is not specified correctly!")
 
        sf, wf = self.gl_quadrature(2)
        sr, wr = self.gl_quadrature(1)

        self.Kgs  = np.zeros((8, 8))
        self.Mgs  = np.zeros((8, 8))
        self.fcgs = np.zeros((8, 1))
        # Initialize 2D arrays to store strain and stress
        self.eps_n = np.empty((2, 2), dtype=object)
        self.sig_n = np.empty((2, 2), dtype=object)
        self.eps_s = np.empty((1, 1), dtype=object)
        self.sig_s = np.empty((1, 1), dtype=object)
        
        if self.type == "ax":
            # Gauss-Legendre integration (full)
            sf, wf = self.gl_quadrature(2)
            for i in range(len(sf)):
                for j in range(len(sf)):
                    # Jacobian of the iso-parametric mapping in the point ij
                    Jac = solid_Jac(sf[i], sf[j], self.xe).reshape((2, 2))

                    # Strain interpolation matrix
                    N = solid_N(sf[i], sf[j])

                    # Shape functions
                    phi = solid_phi(sf[i], sf[j])

                    # Density
                    rho_ij = np.dot(phi, self.xe[:, 1])

                    inv_Jac = np.linalg.inv(Jac)    
                    # inv_Jac_blc = block_diag(inv_Jac, inv_Jac)
                    inv_Jac_blc = np.zeros((4, 4))
                    inv_Jac_blc[0:2, 0:2] = inv_Jac
                    inv_Jac_blc[2:4, 2:4] = inv_Jac

                    # Strain interpolation matrix
                    B = np.vstack([
                        np.dot(np.array([[1, 0, 0, 0], [0, 0, 0, 1]]), inv_Jac_blc.T) @ solid_B(sf[i], sf[j]),
                        np.dot(np.array([1, 0]), N) / rho_ij
                    ])

                    # Done once per gauss point
                    dJ = np.linalg.det(Jac) * wf[i] * wf[j] * rho_ij
                    
                    if dJ < 0:
                        raise('negative determinant of the jacobian')

                    # Gauss-Legendre sum for stiffness
                    self.Kgs += B.T @ self.D[0:3, 0:3] @ B * dJ * 2 * np.pi

                    # Gauss-Legendre sum for mass
                    self.Mgs += N.T @ N * self.rho * dJ * 2 * np.pi

                    # strain (e_rr,e_yy,e_tt)
                    self.eps_n[i, j] = B @ ds

                    # stress (e_rr,e_yy,e_tt)
                    self.sig_n[i, j] = self.D[0:3, 0:3] @ self.eps_n[i, j]

                    # Gauss-Legendre sum for distributed load vector
                    self.fcgs += (N.T @ np.array([self.bx, self.by]).reshape(-1, 1)) * dJ * 2 * np.pi

            # Gauss-Legendre integration (reduced)
            sr, wr = self.gl_quadrature(1)
            for i in range(len(sr)):
                for j in range(len(sr)):
                    # Jacobian of the iso-parametric mapping in the point ij
                    Jac = solid_Jac(sr[i], sr[j], self.xe).reshape((2, 2))

                    # Strain interpolation matrix
                    N = solid_N(sr[i], sr[j])

                    # Shape functions
                    phi = solid_phi(sr[i], sr[j])

                    # Density
                    rho_ij = np.dot(phi, self.xe[:, 1])

                    inv_Jac = np.linalg.inv(Jac)    
                    # inv_Jac_blc = block_diag(inv_Jac, inv_Jac)
                    inv_Jac_blc = np.zeros((4, 4))
                    inv_Jac_blc[0:2, 0:2] = inv_Jac
                    inv_Jac_blc[2:4, 2:4] = inv_Jac


                    # Strain interpolation matrix
                    B = np.dot(np.array([0, 1, 1, 0]), inv_Jac_blc.T) @ solid_B(sr[i], sr[j])

                    # Done once per gauss point
                    dJ = np.linalg.det(Jac) * wr[i] * wr[j] * rho_ij
                    
                    if dJ < 0:
                        raise('negative determinant of the jacobian')
                        
                    # Gauss-Legendre sum for stiffness
                    self.Kgs += B.T @ B * self.D[3, 3] * dJ * 2 * np.pi

                    # strain (e_rr,e_yy,e_tt)
                    self.eps_s[i, j] = B @ ds

                    # stress (e_rr,e_yy,e_tt)
                    self.sig_s[i, j] = self.D[3, 3] * self.eps_s[i, j]
        else:
            # Gauss-Legendre full
            sf, wf = self.gl_quadrature(2)  # Assuming sf and wf are defined similarly to sr and wr
            for i in range(len(sf)):
                for j in range(len(sf)):
                    # Jacobian of the iso-parametric mapping in the point ij
                    Jac = solid_Jac(sf[i], sf[j], self.xe).reshape((2, 2))

                    # Strain interpolation matrix
                    N = solid_N(sf[i], sf[j])

                    # Shape functions
                    phi = solid_phi(sf[i], sf[j])

                    # Density
                    rho_ij = np.dot(phi, self.xe[:, 1])
                    Jac_inv = np.linalg.inv(Jac)
                    # Jac_inv_blc = block_diag(Jac_inv, Jac_inv)
                    Jac_inv_blc = np.zeros((4, 4))
                    Jac_inv_blc[0:2, 0:2] = Jac_inv
                    Jac_inv_blc[2:4, 2:4] = Jac_inv


                    # Strain interpolation matrix
                    B = np.dot(np.array([[1, 0, 0, 0], [0, 0, 0, 1]]), Jac_inv_blc.T) @ solid_B(sf[i], sf[j])

                    # Done once per gauss point
                    dJ = np.linalg.det(Jac) * wf[i] * wf[j]
                    
                    if dJ < 0:
                        raise('negative determinant of the jacobian')                    

                    # Gauss-Legendre sum for stiffness
                    self.Kgs += B.T @ self.D[0:2, 0:2] @ B * dJ * self.h

                    # Gauss-Legendre sum for mass
                    self.Mgs += N.T @  N * self.rho * dJ * self.h

                    # strain (e_rr,e_yy,e_tt)
                    self.eps_n[i, j] = B @ ds

                    # stress (e_rr,e_yy,e_tt)
                    self.sig_n[i, j] = self.D[0:2, 0:2] @ self.eps_n[i, j]

                    # Gauss-Legendre sum for distributed load vector

                    # Perform the matrix multiplication, then reshape the result to (8, 1) before multiplying by dJ
                    self.fcgs += (N.T @ np.array([self.bx, self.by]).reshape(-1, 1)) * dJ


            # Gauss-Legendre integration (reduced)
            sr, wr = self.gl_quadrature(1)
            for i in range(len(sr)):
                for j in range(len(sr)):
                    # Jacobian of the iso-parametric mapping in the point ij
                    Jac = solid_Jac(sr[i], sr[j], self.xe).reshape((2, 2))

                    # Strain interpolation matrix
                    N = solid_N(sr[i], sr[j])

                    # Shape functions
                    phi = solid_phi(sr[i], sr[j])

                    # Density
                    rho_ij = np.dot(phi, self.xe[:, 1])
                    Jac_inv = np.linalg.inv(Jac)
                    
                    # Assuming the use of block_diag is necessary as in the full integration example
                    # If not applicable here, adjust accordingly
                    # Jac_inv_blc = block_diag(Jac_inv, Jac_inv)
                    Jac_inv_blc = np.zeros((4, 4))
                    Jac_inv_blc[0:2, 0:2] = Jac_inv
                    Jac_inv_blc[2:4, 2:4] = Jac_inv

                    # Strain interpolation matrix
                    B = np.dot(np.array([[0, 1, 1, 0]]), Jac_inv_blc.T) @ solid_B(sr[i], sr[j])

                    # Done once per gauss point
                    dJ = np.linalg.det(Jac) * wr[i] * wr[j]
                    
                    if dJ < 0:
                        raise('negative determinant of the jacobian')                    

                    # Gauss-Legendre sum for stiffness
                    self.Kgs += B.T @  B * self.D[2, 2] * dJ * self.h

                    # Before the operation, print out the shapes of N, self.rho, dJ, and self.h


                    # Gauss-Legendre sum for mass
                    # self.Mgs += N.T @ N * self.rho * dJ * self.h

                    # strain (e_rr,e_yy,e_tt)
                    self.eps_s[i, j] = B @ ds

                    # stress (e_rr,e_yy,e_tt)
                    self.sig_s[i, j] = self.D[2, 2] * self.eps_s[i, j]
        self.ftgs = np.zeros(self.fcgs.shape)
        self.ds = ds
       
    #%% Plate behavior

    def compute_plate_pars(self, dp=None):
        
        if dp is None:
            dp = np.zeros((12, 1))
        
        self.Dbp = plate_Db(self.E, self.nu) * self.h**3 / 12
        self.Dsp = plate_Ds(self.E, self.nu) * self.h

        # Gauss-Legendre integration (full and reduced)
        sf, wf = self.gl_quadrature(2)
        sr, wr = self.gl_quadrature(1)

        self.Kb = np.zeros((12, 12))
        
        self.defb = np.empty((2, 2), dtype=object)
        self.forb = np.empty((2, 2), dtype=object)

        Bb = np.empty(plate_Bb(1, 1).shape, dtype=float)
        
        Jac = np.empty((2, 2), dtype=float)

        # Computing bending stiffness for bending and twisting
        for i in range(len(sf)):
            for j in range(len(sf)):
                Jac = plate_Jac(sf[i], sf[j], self.xe).reshape((2, 2))
                Bb  = plate_Bb(sf[i], sf[j])
                
                # Blockdiagonal of Jac
                Jacblk = block_diag(Jac, Jac)

                B = np.dot(np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 1, 1, 0]]), np.linalg.solve(Jacblk, Bb))

                dJ = np.linalg.det(Jac) * wf[i] * wf[j]
                
                if dJ < 0:
                    raise('negative determinant of the jacobian')                

                self.Kb += B.T @ self.Dbp @ B * dJ

                self.defb[i, j] = B @ dp
                self.forb[i, j] = self.Dbp @ self.defb[i, j]

        # Computing the mass stiffness matrix
        self.Mb = np.zeros((12, 12))

        N = np.empty(plate_N(1, 1).shape, dtype=float)
        Jac = np.empty((2, 2), dtype=float)

        for i in range(len(sf)):
            for j in range(len(sf)):
                Jac = plate_Jac(sf[i], sf[j], self.xe).reshape((2, 2))
                N = plate_N(sf[i], sf[j])
                dJ = np.linalg.det(Jac) * wf[i] * wf[j]

                # Create the diagonal matrix
                diagonal_matrix = np.diag([self.h, self.h**3/12, self.h**3/12])

                # Update self.Mb using the corrected formula
                self.Mb += N.T @ (self.rho * diagonal_matrix) @ N * dJ

        # Shear stiffness matrix full integration
        self.Ks2 = np.zeros((12, 12))

        Jac = np.empty((2, 2), dtype=float)
        Bs1 = np.empty(plate_Bs1(1, 1).shape, dtype=float)
        Bs2 = np.empty(plate_Bs2(1, 1).shape, dtype=float)

        for i in range(len(sf)):
            for j in range(len(sf)):
                Jac = plate_Jac(sf[i], sf[j], self.xe).reshape((2, 2))
                Bs1 = plate_Bs1(sf[i], sf[j])
                Bs2 = plate_Bs2(sf[i], sf[j])

                Bs = Bs1 + np.linalg.solve(Jac, Bs2)

                dJ = np.linalg.det(Jac) * wf[i] * wf[j]
                
                if dJ < 0:
                    raise('negative determinant of the jacobian')
                        
                self.Ks2 += Bs.T @ self.Dsp @ Bs * dJ

        # Shear stiffness matrix reduced integration
        self.Ks1 = np.zeros((12, 12))
        self.defs = np.empty((1, 1), dtype=object)
        self.fors = np.empty((1, 1), dtype=object)

        Jac = np.empty((2, 2), dtype=float)
        Bs1 = np.empty(plate_Bs1(1, 1).shape, dtype=float)
        Bs2 = np.empty(plate_Bs2(1, 1).shape, dtype=float)

        for i in range(len(sr)):
            for j in range(len(sr)):
                Jac = plate_Jac(sr[i], sr[j], self.xe).reshape((2, 2))
                Bs1 = plate_Bs1(sr[i], sr[j])
                Bs2 = plate_Bs2(sr[i], sr[j])

                Bs = Bs1 + np.linalg.solve(Jac, Bs2)

                dJ = np.linalg.det(Jac) * wr[i] * wr[j]
                
                if dJ < 0:
                    raise('negative determinant of the jacobian')
                
                self.Ks1 += Bs.T @ self.Dsp @ Bs * dJ

                self.defs[i, j] = Bs @ dp
                self.fors[i, j] = self.Dsp @ self.defs[i, j]

        # Stiffness matrix total
        # Hourglass control
        poly_area = self.polyarea(self.xe)
        self.delta = self.epsilon * self.h**2 / poly_area
        self.Ks = self.Ks1 + self.delta * (self.Ks2 - self.Ks1)
        self.Kp = self.Kb + self.Ks

        # Calculate the force vector and element matrices
        self.fcp = np.zeros((12, 1))
        N = np.empty(plate_N(1, 1).shape, dtype=float)
        Jac = np.empty((2, 2), dtype=float)

        for i in range(len(sf)):
            for j in range(len(sf)):
                Jac = plate_Jac(sf[i], sf[j], self.xe).reshape((2, 2))
                N = plate_N(sf[i], sf[j])

                dJ = np.linalg.det(Jac) * wf[i] * wf[j]
                
                if dJ < 0:
                    raise('negative determinant of the jacobian')

                self.fcp += N.T @ np.array([self.bz, 0, 0]).reshape(-1, 1) * dJ

        self.Kgp = self.Kp
        self.Mgp = self.Mb
        self.fcgp = self.fcp
        self.ftgp = np.zeros(self.fcp.shape)

    #%% Drilling behavior

    def compute_drilling_pars(self):

        k3 = np.array([[   1, -1/2, -1/2], 
                       [-1/2,    1, -1/2], 
                       [-1/2, -1/2,    1]])
                
        k4a = np.zeros((4, 4))
        k4b = np.zeros((4, 4))
        
        poly_area_012 = self.polyarea(self.xe[[0,1,2], :])  
        poly_area_123 = self.polyarea(self.xe[[1,2,3], :])
        poly_area_013 = self.polyarea(self.xe[[0,1,3], :])
        poly_area_023 = self.polyarea(self.xe[[0,2,3], :])

        k4a[np.ix_([0, 1, 2], [0, 1, 2])] = k3 * self.h * self.E * self.alpha * poly_area_012
        k4a[np.ix_([1, 2, 3], [1, 2, 3])] = k4a[np.ix_([1, 2, 3], [1, 2, 3])] + k3 * self.h * self.E * self.alpha * poly_area_123
        
        # k4b[np.ix_([0, 2, 3], [0, 2, 3])] = k3 * self.h * self.E * self.alpha * poly_area_3
        # k4b[np.ix_([0, 1, 3], [0, 1, 3])] = k4b[np.ix_([0, 1, 3], [0, 1, 3])] + k3 * self.h * self.E * self.alpha * poly_area_4
          
        k4b[np.ix_([0, 2, 3], [0, 2, 3])] = k3 * self.h * self.E * self.alpha * poly_area_023
        k4b[np.ix_([0, 1, 3], [0, 1, 3])] = k4b[np.ix_([0, 1, 3], [0, 1, 3])] + k3 * self.h * self.E * self.alpha * poly_area_013
      
        self.Kd   = (k4a + k4b) / 2
        self.Kgd  = self.Kd
        self.fcgd = np.zeros((4, 1))
        self.ftgd = np.zeros((4, 1))
        self.Mgd  = self.Kgd/1e10


    #%% Extract parameters

    def extract_pars(self, pars):
        """
        Extract the parameters from the dictionary pars.
        """

        # this is the element class used in packing/unpacking
        self.my_pars['elem'] = 'shell4'


        self.E   = pars.get("E", 210e9)
        self.nu  = pars.get("nu", 0.3)
        self.rho = pars.get("rho", 7850)
        self.h   = pars.get("h", 5e-3)
        self.nodal_labels = pars.get("nodal_labels", [1, 2, 3, 4]) # node labels
        self.nodal_coords = self.my_nodes.find_coords(self.nodal_labels) # extract nodal coordinates
        self.alpha   = pars.get("alpha", 0.3)
        self.epsilon = pars.get("epsilon", 0.01)
        self.bx      = pars.get("bx", 0.0)
        self.by      = pars.get("by", 0.0)
        self.bz      = pars.get("bz", 0.0)
        self.type    = pars.get("type", "ps")  # type of analysis (ps = plane stress, pe = plane strain, ax = axisymmetric)
        self.dofs_q  = pars.get("dofs_q", np.zeros((0, 2), dtype=np.int32))
    
    #%% Plot 3d elements

    # def plot(self, ax, x=None, y=None, z=None, color='cyan'):
    #     if x is None: x = self.nodal_coords[:, 0]
    #     if y is None: y = self.nodal_coords[:, 1]
    #     if z is None: z = self.nodal_coords[:, 2]
            
    #     # Use nodal coordinates directly to form a quadrilateral grid
    #     # x = self.nodal_coords[:, 0]
    #     # y = self.nodal_coords[:, 1]
    #     # z = self.nodal_coords[:, 2]

    #     # Reshape X, Y, Z into a 2x2 grid (since we have 4 points)
    #     X = np.array([[x[0], x[1]], [x[3], x[2]]])
    #     Y = np.array([[y[0], y[1]], [y[3], y[2]]])
    #     Z = np.array([[z[0], z[1]], [z[3], z[2]]])

    #     # Plot the surface with transparency (alpha)
    #     ax.plot_surface(X, Y, Z, color=color, edgecolor='black', alpha=0.5, lw=0.5)

    #     return ax
    
    #%% Plot 3d elements
    def plot(self, ax, x=None, y=None, z=None, color='cyan'):
        if x is None: x = self.nodal_coords[:, 0]
        if y is None: y = self.nodal_coords[:, 1]
        if z is None: z = self.nodal_coords[:, 2]
            
        # Use nodal coordinates directly to form a quadrilateral grid
        surfaces = [[[x[0], y[0], z[0]], 
                     [x[1], y[1], z[1]], 
                     [x[2], y[2], z[2]], 
                     [x[3], y[3], z[3]]]]

        # Collect lines
        lines = [[[x[0], y[0], z[0]], [x[1], y[1], z[1]]],
                 [[x[1], y[1], z[1]], [x[2], y[2], z[2]]],
                 [[x[2], y[2], z[2]], [x[3], y[3], z[3]]],
                 [[x[3], y[3], z[3]], [x[0], y[0], z[0]]]]

        return lines, surfaces

    def dump_to_paraview(self):
        # here it goes the dump_to_paraview implementation for the beam3d element
        pass
