import numpy as np
import scipy as sp
import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import typing
from scipy.sparse import coo_array
from methods.packages.yafem.nodes import nodes


#%% element class
class core_elem:

    #%% class constructor
    def __init__(self, my_nodes,pars):

         # link the nodes to the element
        self.my_nodes = my_nodes       
        
        # extract parameters and assign default values
        self.extract_pars_core(pars)

    def extract_pars_core(self,pars):
        
        # this is stored for packing/unpacking
        self.my_pars = pars

        # set the default element tag
        self.tag = pars.get("tag",0)

        # extract nodal labels
        self.nodal_labels = pars.get("nodal_labels", np.array([1]))
        
        # extract nodal coordinates
        self.nodal_coords = self.my_nodes.find_coords(self.nodal_labels)
    
        # temperature controlled dofs
        self.dofs_q = np.array(pars.get("dofs_q", []), dtype=np.int32).reshape(-1, 2) if "dofs_q" in pars else np.zeros((0, 2), dtype=np.int32)

    #%% compute the mass matrix
    def compute_M(self):
        return self.M
    
    #%% compute the damping matrix
    def compute_C(self,u,v,q,t,i):
        return self.C

    #%% compute the stiffness matrix
    def compute_K(self,u,v,q,t,i):
        return self.K
    
    #%% compute the restoring force
    def compute_r(self,u,v,q,t,i):

        # compute the restoring force
        r = self.K @ u + self.C @ v

        if hasattr(self, 'B'):

            # compute the strain/cross-sectional deformation
            self.e = self.B @ u

            # compute the stress/cross-sectional force
            self.s = self.D @ self.e

        # store the state variables
        self.u = u
        self.v = v
        self.r = r
        self.t = t 
        self.i = i

        # return the restoring force
        return r

    #%% Function for compute the collocation matrix Zu and Zq
    @jax.jit
    def compute_collocations(dof_e, dofs):
        def indices(dof_e, dofs):
            match = jnp.all(dofs == dof_e, axis=1)
            return jnp.argmax(match), jnp.any(match)
                    
        idx, found = jax.vmap(indices, in_axes=(0, None))(dof_e, dofs)
        all_true = jnp.all(found)
        rows = jnp.where(found, jnp.arange(jnp.shape(found)[0]), 0)
        cols = jnp.take(idx, rows)
        data = jnp.ones_like(rows, dtype=bool)

        return rows, cols, data, found, all_true

    #%% compute the collocation matrix for displacement-controlled dofs
    def compute_Zu(self,dofs):
        if jnp.shape(dofs)[0] != 0:
            rows, cols, data, found, all_true = core_elem.compute_collocations(self.dofs, dofs)

            if not all_true:
                rows = rows[found]
                cols = cols[found]
                data = np.ones_like(rows, dtype=bool)
        else:
            rows = []
            cols = []
            data = []

        # Create the collocation matrix for displacement-controlled dofs
        self.Zu = coo_array((data, (rows, cols)), shape=(self.dofs.shape[0], dofs.shape[0]), dtype=bool).tocsr()

    #%% compute the collocation matrix for temperature-controlled dofs
    def compute_Zq(self,dofs_q):
        if jnp.shape(dofs_q)[0] != 0:
            data, rows, cols, found, all_true = core_elem.compute_collocations(self.dofs_q, dofs_q)

            if not all_true:
                rows = rows[found]
                cols = cols[found]
                data = np.ones_like(rows, dtype=bool)
        else:
            rows = []
            cols = []
            data = []

        # Create the collocation matrix for temperature-controlled dofs
        self.Zq = coo_array((data, (rows, cols)), shape=(self.dofs_q.shape[0], dofs_q.shape[0]), dtype=bool).tocsr()

    #%% reset the element state
    def reset(self):

        self.u = np.zeros(self.dofs.shape[0], dtype=int)
        self.v = self.u.copy()
        self.a = self.u.copy()
        self.q = np.zeros(self.dofs_q.shape[0], dtype=int)

    #%% plot the element
    def plot(self,ax,x=None, y=None, z=None, color=None):
        pass
    
    #%% compute element results (e.g., strain and stress)
    def compute_results(self):
        pass

    #%% save element results in paraview
    def dump_to_paraview(self):
        pass

#%%

'''
class element_solid2d(element):

    def __init__(self, pars, node):

        super().__init__(pars)

        self.E = pars['youngs_modulus']
        self.nu = pars['poisson']        
        self.h = pars['thickness']
        self.node_ID = node[:,0].astype(int)
        self.node_coord = node[:,1:3]
        self.dof = np.array([[self.node_ID[0],0],   #dof 0 = axial load
                             [self.node_ID[0],1],   #dof 1 = bending 
                             [self.node_ID[1],0],
                             [self.node_ID[1],1],
                             [self.node_ID[2],0],   
                             [self.node_ID[2],1],   
                             [self.node_ID[3],0],
                             [self.node_ID[3],1]],dtype="int")
        disp = np.zeros((1,8))
        self.compute_K(disp) 

    def compute_K(self,disp):
        self.Ke = np.zeros((8,8))                     #element stiffness
        Ke_b = np.zeros((8,8))

        #Derivative of shape functions 
        N = lambda s, t : 1/4* np.array([[-(1-t),  (1-t), (1+t), -(1+t)],
                                         [-(1-s), -(1+s), (1+s),  (1-s)]])
        #Plane stress
        D = np.array([[self.E/(1-self.nu**2),          self.nu*self.E/(1-self.nu**2),  0],         #plane stress
                      [self.nu*self.E/(1-self.nu**2),  self.E/(1-self.nu**2),          0],
                      [0,                              0,                              self.E/(2*(1+self.nu))]])   

        #Quadrature rule (shear)
        r,w = self.GaussPoints(1)

        #Jacobian matrix [dx/ds,dx/dt;dy/ds,dy/dt]
        Jsh = N(r,r) @ self.node_coord

        Bssh = np.zeros((4,8))
        Bssh[0,[0,2,4,6]] = N(r,r)[0,:] #dphi_ds_val
        Bssh[1,[0,2,4,6]] = N(r,r)[1,:] #dphi_dt_val
        Bssh[2,[1,3,5,7]] = N(r,r)[0,:]
        Bssh[3,[1,3,5,7]] = N(r,r)[1,:]

        Bsh = np.array([[0,1,1,0]]) @ sp.linalg.block_diag(np.linalg.inv(Jsh),np.linalg.inv(Jsh)) @ Bssh

        Ke_sh = self.h * Bsh.transpose() * D[2,2]  * Bsh * np.linalg.det(Jsh) * w * w 
        
        #Quadrature rule (bending)
        r,w = self.GaussPoints(2)

        #Numerical ingration
        self.stress = np.zeros((4,3))
        n = 0
        for si,wi in zip(r,w):
            for tj,wj in zip(r,w):

                # Jacobian matrix [dx/ds,dx/dt;dy/ds,dy/dt]
                J = N(si,tj) @ self.node_coord

                Bs = np.zeros((4,8))
                Bs[0,[0,2,4,6]] = N(si,tj)[0,:] #dphi_ds_val
                Bs[1,[0,2,4,6]] = N(si,tj)[1,:] #dphi_dt_val
                Bs[2,[1,3,5,7]] = N(si,tj)[0,:]
                Bs[3,[1,3,5,7]] = N(si,tj)[1,:]

                Bb = np.array([[1,0,0,0],[0,0,0,1]]) @ sp.linalg.block_diag(np.linalg.inv(J),np.linalg.inv(J)) @ Bs

                Ke_b += self.h * Bb.transpose() @ D[0:2,0:2] @ Bb * np.linalg.det(J) * wi * wj 

                #set displacement to zero, and run again later with known displacement. calculate the stress here
                B = np.concatenate((Bb,Bsh),axis=0)
                strain = B @ disp.transpose()
                stress = D @ strain
                self.stress[n,:] = stress.transpose()
                n += 1

        self.Ke = Ke_b + Ke_sh

    def GaussPoints(self,order):
        # quadrature rules in 1D (2D rules are obtained by combining 1Ds as in a grid)
        if order == 1:
            r = 0.0
            w = 2.0 
        elif order == 2:
            r = np.array([-1/np.sqrt(3),1/np.sqrt(3)])
            w = np.array([1.0,1.0])

        return r,w
    
    def calculate_stress(self,u):
        self.compute_K(u)
    
    def plot(self,ax,ue,uscale):

        # Add the polygon patch to the axes
        ax.add_patch(patches.Polygon(self.node_coord[:,0:2],color='blue', alpha=0.5)) 

        # Update position
        self.pos = self.node_coord.copy # be carefull !!!
        
        self.pos[0,0] = self.pos[0,0] + ue[0] * uscale
        self.pos[0,1] = self.pos[0,1] + ue[1] * uscale
        self.pos[1,0] = self.pos[1,0] + ue[2] * uscale
        self.pos[1,1] = self.pos[1,1] + ue[3] * uscale
        self.pos[2,0] = self.pos[2,0] + ue[4] * uscale
        self.pos[2,1] = self.pos[2,1] + ue[5] * uscale
        self.pos[3,0] = self.pos[3,0] + ue[6] * uscale
        self.pos[3,1] = self.pos[3,1] + ue[7] * uscale

        ax.add_patch(patches.Polygon(self.pos[:,0:2],color='red', alpha=0.5))

    def plot_stress(self,ax,stress_min,stress_max,direction,u):
        self.calculate_stress(u)
        avg_stress = (self.stress[0,direction] + self.stress[1,direction] + self.stress[2,direction] + self.stress[3,direction])/4.0
        stress_norm = np.interp(avg_stress,np.array([stress_min,stress_max]),np.array([0.0,1.0]))

        ax.add_patch(patches.Polygon(self.pos[:,0:2], closed=True, edgecolor='black', facecolor=plt.cm.viridis(stress_norm)))

'''

