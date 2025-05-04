import numpy as np
import scipy as sp
import concurrent.futures
import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import scipy.sparse.linalg as spla
import typing
from scipy.sparse import eye as speye
from scipy.sparse import csr_array, coo_array
from scipy.sparse.linalg import eigsh
#from yafem.elem.core_elem import core_elem 
from core_elem_ga import core_elem # This is the customized (GA)

'''
# Function for conversion of dense to sparse matrix
def dense2sparse(A):

    # row and column indices of non-zero elements
    row_ind,col_ind = np.nonzero(A)

    # values of non-zero elements
    data = A[row_ind,col_ind]

    # return sparse matrix
    return csr_array((data,(row_ind,col_ind)),shape=A.shape)
'''
class model:

    # pars : typing.Dict = None # * parameters supplied by the user 
    # ndof : np.ndarray[np.int32] = None # number of dofs
    # dofs : np.ndarray[np.int32] = None # list of model dofs
    # dofs_c : np.ndarray[np.int32] = None # ** constrained dofs
    # dofs_m : np.ndarray[np.int32] = None # ** master dofs
    # dofs_s : np.ndarray[np.int32] = None # ** slave dofs
    # dofs_f : np.ndarray[np.int32] = None # ** force-controlled dofs
    # dofs_u : np.ndarray[np.int32] = None # ** displacement-controlled dofs
    # dofs_q : np.ndarray[np.int32] = None # ** temperature-controlled dofs
    # g_f : np.ndarray[np.float64] = None # ** force history
    # g_u : np.ndarray[np.float64] = None # ** displacement history
    # g_q : np.ndarray[np.float64] = None # ** temperature history
    # step : int = None # ** numner of simulation steps
    # dt : float = None # ** simulation step size 
    # M : csr_array = None # mass matrix
    # K : csr_array = None # stiffness matrix
    # C : csr_array = None # damping matrix
    # Cp : csr_array = None # proportional damping
    # Bf : csr_array = None # collocation matrix for force load
    # Bu : csr_array = None # collocation matrix for displacement load
    # r : np.ndarray[np.float64] = None # restoring force
    # u : np.ndarray[np.float64] = None # displacement
    # v : np.ndarray[np.float64] = None # velocity
    # a : np.ndarray[np.float64] = None # acceleration
    # l : np.ndarray[np.float64] = None # lagrange multipliers
    # damping_model : str = None # ** damping model
    # alpha : float = None # ** mass-proportional damping coefficient
    # beta : float = None # ** stiffness-proportional damping coefficient
    # phi : np.ndarray[np.float64] = None # modal shapes
    # omega : np.ndarray[np.float64] = None # modal frequencies
    
    # my_elements : typing.List[core_elem] = None # list of elements associated with the model

    # dofs_total : np.ndarray[np.int32] = None # total list of dofs

    # dofs_x : np.ndarray[np.int32] = None # ** extended list of dofs for plots
    # ind_x : np.ndarray[np.int32] = None # indices of the model dofs on the dofs_x
    # ndofs_x : np.ndarray[np.int32] = None # number of dofs
    # u_x : np.ndarray[np.float64] = None # displacement (extended)
    # v_x : np.ndarray[np.float64] = None # velocity (extended)
    # a_x : np.ndarray[np.float64] = None # acceleration (extended)
    # phi_x : np.ndarray[np.float64] = None # modal shapes (extended)

    #%% this is the class constructor
    def __init__(self, my_nodes, my_elements, pars):
        
        # save the link the object my_nodes
        self.my_nodes = my_nodes

        # save the link the list object list my_elements
        self.my_elements = my_elements

        # extract the parameters and assign default values
        self.extract_pars(pars)

        # list of model dofs
        self.dofs = np.zeros((0, 2), dtype=int)

        # assembly of the list of model dofs
        for my_element in self.my_elements:
            # for each dof of the element
            for idx_e, dof_e in enumerate(my_element.dofs):
                # loop over the slave dofs
                for idx_s, dof_s in enumerate(self.dofs_s):
                    # if the element dof is a slave dof
                    if np.array_equal(dof_e, dof_s):
                        # replace the element slave dof with the corresponding master dof
                        my_element.dofs[idx_e] = self.dofs_m[idx_s]

            # add the element dofs to the model dofs
            self.dofs = np.concatenate((self.dofs, my_element.dofs), axis=0)

        # remove repeated dofs
        self.dofs = np.unique(self.dofs, axis=0)

        # Removal of constraint dofs (dofs_c)
        if jnp.shape(self.dofs_c)[0] != 0:
            @jax.jit
            def collocation_indices(dof_c, dofs):

                def indices(dof_c, dofs):
                    match = jnp.all(dofs == dof_c, axis=1)
                    return jnp.argmax(match)

                idx = jax.vmap(lambda dof_c: indices(dof_c, dofs))(dof_c)  

                return idx            

            idx = collocation_indices(self.dofs_c, self.dofs)
            self.dofs = np.delete(self.dofs, idx, axis=0)          
           
        # # compute the collocation matrices of all elements
        # for my_element in self.my_elements:
        #     my_element.compute_Zu(self.dofs) 
        #     my_element.compute_Zq(self.dofs_q)

        # compute the collocation matrices of all elements
        self.compute_collocations()

        # if there are master-slave equations
        if self.dofs_m.shape[0] > 0:
            # master-slave matrix
            self.Tu = speye(self.dofs.shape[0]).todense()
            # link slave to master dofs
            self.Tu[self.find_dofs(self.dofs_s), self.find_dofs(self.dofs_m)] = speye(self.dofs_m.shape[0]).todense()
            # eliminate slave dofs columns
            self.Tu = np.delete(self.Tu, self.find_dofs(self.dofs_s), axis=1)
            # eliminate slave dofs from dofs
            self.dofs = np.delete(self.dofs, self.find_dofs(self.dofs_s), axis=0)
            # update element incidence matrices based on master-slave equations
            for e, element in enumerate(self.my_elements, start=1):
                if e % 100 == 0:
                    print(f'update Zu element {e} of {len(self.my_elements)}')
                element.Zu = coo_array(element.Zu @ self.Tu, dtype=np.int8)

        # number of dofs
        self.ndof = self.dofs.shape[0]

        # compute the mass, stiffness and damping matrix
        self.compute_MCK_matricies()

        # compute the proportional damping matrix
        self.compute_Cp()

        # compute collocation matrix for controlled forces
        self.compute_Bf()

        # compute collocation matrix for controlled displacements
        self.compute_Bu()

        # initialization of state vectors
        self.u = np.zeros((self.ndof), dtype=int)
        self.v = self.u.copy()
        self.a = self.u.copy()
        self.r = self.u.copy()
        self.l = np.zeros((self.dofs_u.shape[0]), dtype=int)

        # extended list of model dofs for plot (6 dofs per node)
        self.dofs_x = np.array([np.kron(my_nodes.nodal_labels, np.ones(6)), 
                                np.kron(np.ones(self.my_nodes.nodal_labels.shape[0]), np.array([1, 2, 3, 4, 5, 6]))], dtype=int).T

        # indices of the model dofs on the extended dofs
        self.ind_x = self.find_dofs_x(self.dofs)

        # number of extended dofs
        self.ndofs_x = self.dofs_x.shape[0]
        
        # extended quantities for mesh plots
        self.u_x = np.zeros((self.ndofs_x), dtype=int)
        self.v_x = self.u_x.copy()
        self.a_x = self.u_x.copy()

    #%% concurrent processes 

    def compute_collocations(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.proces_collocations, element) for element in self.my_elements]
            concurrent.futures.wait(futures)

    def proces_collocations(self, element):
        element.compute_Zu(self.dofs)
        element.compute_Zq(self.dofs_q)

    def compute_MCK_matricies(self):
        dofs0   = np.zeros(self.dofs.shape[0])
        dofs0_q = np.zeros(self.dofs_q.shape[0])
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.compute_M),
                executor.submit(self.compute_K, np.zeros(self.dofs.shape[0]), np.zeros(self.dofs.shape[0]), np.zeros(self.dofs_q.shape[0]), 0.0, 0),
                executor.submit(self.compute_C, np.zeros(self.dofs.shape[0]), np.zeros(self.dofs.shape[0]), np.zeros(self.dofs_q.shape[0]), 0.0, 0),
            ]
            concurrent.futures.wait(futures)

    #%% this method extract the parameters and assigns default values
    def extract_pars(self,pars):

        self.step = int(pars.get('step', 10)) # number of simulation steps
        self.dt = float(pars.get('dt', 1.0)) # time step size

        self.dofs_c = pars.get('dofs_c', np.zeros((0, 2), dtype=np.int32)).astype(np.int32) # list of constrained dofs
        self.dofs_m = pars.get('dofs_m', np.zeros((0, 2), dtype=np.int32)).astype(np.int32) # list of master dofs
        self.dofs_s = pars.get('dofs_s', np.zeros((0, 2), dtype=np.int32)).astype(np.int32) # list of slave dofs
        self.dofs_f = np.array(pars.get('dofs_f', np.zeros((0, 2), dtype=np.int32)), dtype=np.int32)  # list of force-controlled dofs
        self.dofs_u = np.array(pars.get('dofs_u', np.zeros((0, 2), dtype=np.int32)), dtype=np.int32)  # list of displacement-controlled dofs
        self.dofs_q = np.array(pars.get('dofs_q', np.zeros((0, 2), dtype=np.int32)), dtype=np.int32)  # list of temperature-controlled dofs

         # Determine the number of steps from g_f, g_u, and g_q
        steps = []
        if 'g_f' in pars: steps.append(np.shape(pars['g_f'])[-1]) 
        if 'g_u' in pars: steps.append(np.shape(pars['g_u'])[-1]) 
        if 'g_q' in pars: steps.append(np.shape(pars['g_q'])[-1]) 

        # Set the number of steps, defaulting to 10 if no steps are provided
        self.step = max(steps) if steps else int(pars.get('step', 10))

        # Handle time step size
        self.dt = float(pars.get('dt', 1.0))

        # loading/force/temperature history applied to force/displacement/temperature-controlled dofs
        self.g_f = np.array(pars.get('g_f', np.zeros((self.dofs_f.shape[0], self.step), dtype=np.float64)), dtype=np.float64)
        self.g_u = np.array(pars.get('g_u', np.zeros((self.dofs_u.shape[0], self.step), dtype=np.float64)), dtype=np.float64)
        self.g_q = np.array(pars.get('g_q', np.zeros((self.dofs_q.shape[0], self.step), dtype=np.float64)), dtype=np.float64)

        # Ensure that g_f, g_u, and g_q are 2D arrays
        if len(self.g_f.shape) == 1: self.g_f = np.array([self.g_f])
        if len(self.g_u.shape) == 1: self.g_u = np.array([self.g_u])
        if len(self.g_q.shape) == 1: self.g_q = np.array([self.g_q])

        self.damping_model = pars.get('damping_model', 'none') # damping model - 'none' is proportional
        self.alpha = float(pars.get('alpha', 0.0)) # mass-proportional damping coefficient
        self.beta = float(pars.get('beta', 0.0)) # stiffness-proportional damping coefficient

        '''
        # damping ratio for modal damping
        if 'zeta' in pars:
            self.zeta = pars['zeta']
        else:
            self.zeta = 0.0
        '''
        # checks on the input
        if self.dofs_s.shape[0] != self.dofs_m.shape[0]:
            raise Exception('number of master/slave dofs do not match!')

    #%% compute the model stiffness matrix
    def compute_r(self,u,v,q,t,i):

        # initialize the restoring force vector
        r = np.zeros((self.dofs.shape[0]))

        # loop over the elements
        for my_element in self.my_elements:

            # compute the element restoring force vector
            re = my_element.compute_r(my_element.Zu @ u,my_element.Zu @ v, my_element.Zq @ q, t, i)

            # assemble the model restoring force vector
            r += my_element.Zu.transpose() @ re

        # return the model restoring force vector
        return r
    
    #%% compute the model stiffness matrix
    def compute_K(self, u, v, q, t, i):
        # Preallocate lists for each element
        data = [[]] * len(self.my_elements)
        row_indices =  data.copy()
        col_indices =  data.copy()

        # Loop over the elements
        for idx, my_element in enumerate(self.my_elements):
            # Compute local quantities
            u_local = my_element.Zu @ u
            v_local = my_element.Zu @ v
            q_local = my_element.Zq @ q

            # Compute the element stiffness matrix
            Ke = csr_array(my_element.compute_K(u_local, v_local, q_local, t, i))

            # Compute global contributions
            coo_assembled_K = coo_array(my_element.Zu.transpose() @ Ke @ my_element.Zu)

            # Append data, rows, and columns to the respective lists
            data[idx]        = coo_assembled_K.data
            row_indices[idx] = coo_assembled_K.row
            col_indices[idx] = coo_assembled_K.col

        # Concatenate the collected data, row, and column indices
        data = np.concatenate(data)
        row_indices = np.concatenate(row_indices)
        col_indices = np.concatenate(col_indices)

        # Construct the global stiffness matrix in COO format, then convert to CSR
        self.K = coo_array((data, (row_indices, col_indices)), shape=(len(self.dofs), len(self.dofs))).tocsr()

        return self.K

    #%% compute the model stiffness matrix
    def compute_C(self, u, v, q, t, i):
        # Preallocate lists for assembling the damping matrix
        data = [[]] * len(self.my_elements)
        row_indices =  data.copy()
        col_indices =  data.copy()

        # Loop over the elements
        for idx, my_element in enumerate(self.my_elements):
            # Compute element damping matrix
            u_local = my_element.Zu @ u
            v_local = my_element.Zu @ v
            q_local = my_element.Zq @ q
            Ce = csr_array(my_element.compute_C(u_local, v_local, q_local, t, i))

            # Collect the non-zero values and indices for final assembly
            coo_assembled_C = coo_array(my_element.Zu.transpose() @ Ce @ my_element.Zu)

            # Append data, rows, and columns to the respective lists
            data[idx]        = coo_assembled_C.data
            row_indices[idx] = coo_assembled_C.row
            col_indices[idx] = coo_assembled_C.col

        # Concatenate the collected data and indices
        data = np.concatenate(data)
        row_indices = np.concatenate(row_indices)
        col_indices = np.concatenate(col_indices)

        # Construct the final damping matrix in COO format, then convert to CSR
        self.C = coo_array((data, (row_indices, col_indices)), shape=(len(self.dofs), len(self.dofs))).tocsr()

        return self.C

    #%% compute the model mass matrix
    def compute_M(self):
        # Preallocate lists for assembling the mass matrix
        data = [[]] * len(self.my_elements)
        row_indices =  data.copy()
        col_indices =  data.copy()

        # Loop over the elements
        for idx, my_element in enumerate(self.my_elements):

            # Compute element mass matrix
            Me = csr_array(my_element.compute_M())

            # Collect the non-zero values and indices for final assembly
            coo_assembled_M = coo_array(my_element.Zu.transpose() @ Me @ my_element.Zu)

            # Append data, rows, and columns to the respective lists
            data[idx]        = coo_assembled_M.data
            row_indices[idx] = coo_assembled_M.row
            col_indices[idx] = coo_assembled_M.col

        # Concatenate the collected data and indices
        data = np.concatenate(data)
        row_indices = np.concatenate(row_indices)
        col_indices = np.concatenate(col_indices)

        # Construct the final mass matrix in COO format, then convert to CSR
        self.M = coo_array((data, (row_indices, col_indices)), shape=(len(self.dofs), len(self.dofs))).tocsr()

        return self.M

    #%% compute the collocation matrix for controlled forces
    # def compute_Bf(self):

    #     # initialize the collocation matrix for controlled forces
    #     self.Bf = csr_array((len(self.dofs),len(self.dofs_f)))

    #     # rows and cols indices for the non-zero entries
    #     rows = []
    #     cols = []

    #     # loop over the model dofs
    #     for idx,dof in enumerate(self.dofs):

    #         # loop over the force-controlled dofs
    #         for idx_f,dof_f in enumerate(self.dofs_f):

    #             # if the model dof is a force-controlled dof then store its indices
    #             if np.array_equal(dof,dof_f):
    #                 rows.append(idx)
    #                 cols.append(idx_f)  

    #     # store the non-zero entries in the collocation matrix
    #     self.Bf = csr_array((np.ones((len(rows))),(rows,cols)),shape=(self.dofs.shape[0],self.dofs_f.shape[0]),dtype=np.int32)     


    def compute_Bf(self):

        # Convert to numpy arrays for broadcasting, if not already
        dofs = np.array(self.dofs)
        dofs_f = np.array(self.dofs_f)

        # Create a boolean matrix where True represents a match between dofs and dofs_f
        matches = np.all(dofs[:, None] == dofs_f, axis=2)

        # Find indices where matches are True
        rows, cols = np.where(matches)

        # Store the non-zero entries in the collocation matrix
        self.Bf = coo_array((np.ones_like(rows), (rows, cols)),shape=(dofs.shape[0], dofs_f.shape[0]),dtype=np.int32).tocsr()


    #%% compute the collocation matrix for controlled displacements
    # def compute_Bu(self):

    #     # initialize the collocation matrix for controlled forces
    #     self.Bu = csr_array((len(self.dofs),len(self.dofs_u)))

    #     # rows and cols indices for the non-zero entries
    #     rows = []
    #     cols = []

    #     # loop over the model dofs
    #     for idx,dof in enumerate(self.dofs):

    #         # loop over the force-controlled dofs
    #         for idx_u,dof_u in enumerate(self.dofs_u):

    #             # if the model dof is a force-controlled dof then store its indices
    #             if np.array_equal(dof,dof_u):
    #                 rows.append(idx)
    #                 cols.append(idx_u)  

    #     # store the non-zero entries in the collocation matrix
    #     self.Bu = csr_array((np.ones((len(rows))),(rows,cols)),shape=(self.dofs.shape[0],self.dofs_u.shape[0]),dtype=np.int32)     


    def compute_Bu(self):

        # Convert to numpy arrays for broadcasting, if not already
        dofs = np.array(self.dofs)
        dofs_u = np.array(self.dofs_u)

        # Create a boolean matrix where True represents a match between dofs and dofs_u
        matches = np.all(dofs[:, None] == dofs_u, axis=2)

        # Find indices where matches are True
        rows, cols = np.where(matches)

        # Store the non-zero entries in the collocation matrix
        self.Bu = coo_array((np.ones_like(rows), (rows, cols)), shape=(dofs.shape[0], dofs_u.shape[0]),dtype=np.int32).tocsr()

    #%% compute the proportional damping
    def compute_Cp(self):

        if self.damping_model == 'none':

            self.Cp = coo_array((len(self.dofs),len(self.dofs))).tocsr()

        elif self.damping_model == 'proportional':
            
            # compute the mass and stiffness matrices
            if np.shape(self.M) == 0 and np.shape(self.K) == 0:

                # initialize the displacement, velocity and acceleration
                u = np.zeros((self.dofs.shape[0],1))
                v = u.copy()
                q = np.zeros((self.dofs_q.shape[0],1))

                self.M = self.compute_M()
                self.K = self.compute_K(u,v,q,0.0,0)

            # compute the proportional damping
            self.Cp = self.M*self.alpha + self.K*self.beta     

        # return the proportional damping matrix
        return self.Cp    

    #%% reset the model
    def reset(self):
        
        self.u = np.zeros_like(self.u)
        self.v = np.zeros_like(self.v)
        self.a = np.zeros_like(self.a)
        self.r = np.zeros_like(self.r)
        self.l = np.zeros_like(self.l)

        self.u_x = np.zeros_like(self.u_x)
        self.v_x = np.zeros_like(self.v_x)
        self.a_x = np.zeros_like(self.a_x)

        # loop over the elements
        for my_element in self.my_elements:

            # reset the element
            my_element.reset()

    #%% compute the modal analysis of the model
    def compute_modal(self,mode=1):

        # compute the mass and stiffness matrices
        if np.shape(self.M) == 0 and np.shape(self.K) == 0:

            # initialize the displacement, velocity and acceleration
            u = np.zeros((self.dofs.shape[0]))
            v = np.zeros((self.dofs.shape[0])) #u.copy()
            q = np.zeros((self.dofs_q.shape[0]))
                
            # compute the mass and stiffness matrices
            self.M = self.compute_M()
            self.K = self.compute_K(u,v,q,0.0,0)

        # solve the eigenvalue problem
        self.omega, self.phi = spla.eigsh(self.K, M=self.M, k=mode, which='LM', sigma=0, mode='normal')
        
        # extended modal shape (for plots)
        self.phi_x = np.zeros((self.dofs_x.shape[0],self.phi.shape[1]))
        self.phi_x[self.ind_x,:] = self.phi

        # Compute natural frequencies (in Hz)
        self.omega = np.real(np.sqrt(self.omega))/(2*np.pi)

        return self.omega, self.phi

    #%% extract the dof indices of selected dofs
    def find_dofs(self, dofs_sel):

        # force "dofs_sel" to a 2d array
        dofs_sel = np.atleast_2d(dofs_sel)

        self.dofs = jnp.array(self.dofs)
        dofs_sel  = jnp.array(dofs_sel)

        idxs_sel = jax.vmap(lambda dofs_sel: jnp.argmax(jnp.all(self.dofs == dofs_sel, axis=1)))
        idxs_sel = np.array(idxs_sel(dofs_sel))

        if np.shape(dofs_sel)[0] != np.shape(idxs_sel)[0]:
            raise Exception("Warning! Number of selected dofs, do not match with detected indices")

        return idxs_sel
        
    def find_dofs_x(self, dofs_sel): # find on extended dofs (for plots)

        # force "dofs_sel" to a 2d array
        dofs_sel = np.atleast_2d(dofs_sel)

        self.dofs_x = jnp.array(self.dofs_x)
        dofs_sel  = jnp.array(dofs_sel)

        idxs_sel = jax.vmap(lambda dofs_sel: jnp.argmax(jnp.all(self.dofs_x == dofs_sel, axis=1)))
        idxs_sel = np.array(idxs_sel(dofs_sel))

        if np.shape(dofs_sel)[0] != np.shape(idxs_sel)[0]:
            raise Exception("Warning! Number of selected dofs, do not match with detected indices")

        return idxs_sel        

    #%% extract the dof indices of selected nodes
    def find_nodes(self, nodes_sel):

        # force "nodes_sel" to a 2d array
        nodes_sel = np.atleast_2d(nodes_sel)

        nodes_sel = np.array(nodes_sel)
        
        nodes_in_dofs = np.array(self.dofs)[:, 0]
        matches = np.isin(nodes_in_dofs, nodes_sel)
        
        # Get the indices of matching elements
        idxs_sel = np.atleast_2d(np.where(matches)[0])

        if np.min(np.shape(nodes_sel)) != np.shape(idxs_sel)[0]:
            raise Exception("Warning! Number of selected nodes, do not match with detected indices")
        
        return idxs_sel

    #%% extract the dof indices of selected directions
    # def find_dirs(self,dirs_sel):
        
    #     # indices of selected nodes
    #     idxs_sel = []
        
    #     # loop over the selected dofs
    #     for idx_sel, dir_sel in enumerate(dirs_sel):

    #         # loop over the model dofs
    #         for idx, dof in enumerate(self.dofs):

    #             # if the model dof dir is a selected dof dir then store its index
    #             if np.array_equal(dof[1],dir_sel):
    #                 idxs_sel.append(idx)

    #     # return the indices of the selected dof dir
    #     return idxs_sel

    def find_dirs(self,dirs_sel):
        dirs_sel = np.array(dirs_sel)
        
        nodes_in_dofs = np.array(self.dofs)[:, 1]
        matches = np.isin(nodes_in_dofs, dirs_sel)
        
        # Get the indices of matching elements
        idxs_sel = np.where(matches)[0]
        
        return idxs_sel
        
    #%% post-processing
        
    def dump_to_paraview(self):
        # save nodal coordinates
        self.my_nodes.dump_to_paraview()
        # save element results
        for element in self.my_elements:
            element.dump_to_paraview()
        
    # dump the model results to the elements
    def dump_to_elements(self):
        for element in self.my_elements:
            element.u = element.Zu @ self.u
            element.v = element.Zu @ self.v
            element.q = element.Zq @ self.q
            # compute the element results (e.g., stress/strain)
            element.compute_results()
            
    #%% plots
    
    def plot(self,labels=True, rotate=(30,30), figsize=8, zoom=1.0, axis='on', response = None, scale=1):
        
        # plotting nodes
        ax = self.my_nodes.plot(labels=labels, rotate=rotate, figsize=figsize, zoom=zoom, axis=axis)
        
        # plotting elements
        for element in self.my_elements:
            element.plot(ax)

        if response is not None:
        
            # modal response expanded to full dofs array
            res = np.zeros([np.shape(self.dofs_x)[0]])
            res[self.find_dofs_x(self.dofs)] = np.atleast_1d(response)

            # plotting model response
            for element in self.my_elements:

                # Check if the element has 'nodal_coords'
                if not hasattr(element, 'nodal_coords'):
                    continue
                
                idx = self.find_dofs_x(element.dofs)

                # storing model responses
                res_x = res[idx[0::6]] * scale + np.atleast_1d(element.nodal_coords[:,0])
                res_y = res[idx[1::6]] * scale + np.atleast_1d(element.nodal_coords[:,1])
                res_z = res[idx[2::6]] * scale + np.atleast_1d(element.nodal_coords[:,2])

                element.plot(ax,x=res_x, y=res_y, z=res_z, color='r')
