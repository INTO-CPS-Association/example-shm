import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import typing
from scipy.sparse.linalg import spsolve
from scipy.sparse import csr_array, csc_array
from methods.packages.yafem.nodes import *
from methods.packages.yafem.elem.core_elem import *
from methods.packages.yafem.model import *

class simulation:

    # recorder_fields : typing.List[np.ndarray[np.float64]] = []
    msg = "step {} converged in {} iterations with residual {}" # pre-loading a message for simulations

#%% object constructor
    def __init__(self,my_model,pars={}):

        # link the list of elements to the model
        self.my_model = my_model

        # extract the parameters and assign default values
        self.extract_pars(pars)

        # initialize recorder data
        self.recorder_data = {}

        # initialize recorder fields
        for recorder_tag in self.recorder_tags:
            print("created recorder field for: " + recorder_tag)
            self.recorder_data[recorder_tag] = np.zeros(self.my_model.step)

        # initialize solution variables
        self.u = np.zeros((self.my_model.dofs.shape[0],self.my_model.step)) # displacements
        self.v = self.u.copy()  # velocities
        self.a = self.u.copy()  # accelerations
        self.r = self.u.copy()  # restoring force
        self.l = np.zeros((self.my_model.dofs_u.shape[0],self.my_model.step)) # lagrange multipliers

        # initialize the mass matrix (constant)
        self.M = self.my_model.M

        # initialize the proportional damping matrix (constant)
        self.Cp = self.my_model.Cp

        # initialize the time axis
        self.t = np.arange(0, self.my_model.step * self.my_model.dt + self.my_model.dt, self.my_model.dt)
        

#%% extract parameters and assign default values
    def extract_pars(self,pars):

        # storage of input for packing/unpacking
        self.my_pars = pars

        self.tol_min       = float(pars.get('tol_min', 1e-6)) # minimum convergence tolerance
        self.iter_max      = int(pars.get('iter_max', 20)) # maximum number of iterations
        self.gamma         = pars.get('gamma', 0.5) # Newmark gamma
        self.beta          = pars.get('beta', 0.25) # Newmark beta
        self.delta         = pars.get('delta', 1.0) # Arclen parameter
        self.recorder_tags = pars.get('recorder_tags', []) # recorders

#%% dynamic analysis
    # time history analysis using the Newmark method (only force and temperature controlled dofs)
    def dynamic_analysis(self, step1=0, step2=None,output=True):

        if step2 is None:
            step2 = self.my_model.step  # Default last analysis step

        # time integration loop
        for i in range(step1,step2-1):

            # perform dynamic analysis step
            self.u[:,i+1],self.v[:,i+1],self.a[:,i+1],self.r[:,i+1] = self.dynamic_analysis_step(self.u[:,i],self.v[:,i],self.a[:,i],self.t[i],i,output)

            # record model results
            self.record_step(i+1)

            # store response for plotting
            self.my_model.u_x[self.my_model.ind_x] = self.u[:,i]
            self.my_model.v_x[self.my_model.ind_x] = self.v[:,i]
            self.my_model.a_x[self.my_model.ind_x] = self.a[:,i]

        # return output
        return self.u,self.v,self.a,self.r
    
    # perform dynamic analysis step
    def dynamic_analysis_step(self,u0,v0,a0,t0,i0,output):

        # Newmark predictors
        a1 = np.zeros(self.my_model.dofs.shape[0])
        v1 = v0 + self.my_model.dt * (1-self.gamma) * a0

        u1 = u0 + self.my_model.dt * v0 + self.my_model.dt**2 * (0.5-self.beta) * a0
        t1 = t0 + self.my_model.dt
        i1 = i0 + 1

        # compute the internal forces
        r1 = self.my_model.compute_r(u1,v1,self.my_model.g_q[:,i1],t1,i1)
        
        # residual of the equilibrium equation
        res = self.M @ a1 + self.Cp @ v1 + r1 - self.my_model.Bf @ self.my_model.g_f[:,i1]

        # iteration counter
        cc = 0

        while True:

            # tangent stiffness matrix
            K = self.my_model.compute_K(u1,v1,self.my_model.g_q[:,i1],t1,i1)

            # tangent damping matrix
            C = self.my_model.compute_C(u1,v1,self.my_model.g_q[:,i1],t1,i1)
            
            # jacobian of the residual           
            jac = self.M + (self.Cp + C) * self.gamma * self.my_model.dt + K * self.beta * self.my_model.dt**2

            # acceleration update
            da = -spsolve(jac,res)
 
            # update all kinematic quantities
            a1 = a1 + da
            v1 = v1 + da * self.gamma * self.my_model.dt
            u1 = u1 + da * self.beta  * self.my_model.dt**2

            # compute the internal forces
            r1 = self.my_model.compute_r(u1,v1,self.my_model.g_q[:,i1],t1,i1)

            # residual of the equilibrium equation
            res = self.M @ a1 + self.Cp @ v1 + r1 - self.my_model.Bf @ self.my_model.g_f[:,i1]

            # convergence tolerance
            tol = (np.linalg.norm(res) * self.my_model.ndof) / (self.my_model.ndof * (1 + np.linalg.norm(np.dot(self.my_model.Bf.todense(), self.my_model.g_f[:, i1]))))

            # exit condition
            if cc >= self.iter_max or tol < self.tol_min:
                if output == True:
                    # print(f"step {i1} converged in {cc+1} iterations with residual {tol}")
                    print(simulation.msg.format(i1, cc + 1, tol))
                break
            else:
                cc += 1

        # return the results of the analysis step
        return u1,v1,a1,r1

#%% static analysis
    def static_analysis(self, step1=0, step2=None,output=True):
            
            if step2 is None: 
                step2 = self.my_model.step  # Default last analysis step
            
            # Sequence of analysis steps
            for i in range(step1, step2-1):

                # Single analysis step
                self.u[:, i+1], self.l[:, i+1], self.r[:, i+1] = self.static_analysis_step(self.u[:, i], self.l[:, i], self.t[i], i, output)
        
                # record model results
                self.record_step(i+1)

                # store response for plotting
                self.my_model.u_x[self.my_model.ind_x] = self.u[:,i]

            return self.u, self.l, self.r

    def static_analysis_step(self, u0, l0, t0, i0, output):
        
        u1 = u0.copy()
        l1 = l0.copy()
        i1 = i0 + 1
        t1 = t0 + self.my_model.dt
            
        # Compute the restoring force
        r1 = self.my_model.compute_r(u1, np.zeros_like(u1), self.my_model.g_q[:, i1], t1, i1)

        # Compute the residual of the equilibrium equation  
        res = r1 - self.my_model.Bf @ self.my_model.g_f[:, i1] - self.my_model.Bu @ l1
       
        # Iteration counter
        cc = 0
           
        while True:

            # Jacobian of the residual
            K = self.my_model.compute_K(u1, np.zeros_like(u1), self.my_model.g_q[:, i1], t1, i1)
           
            # Newton-Raphson updates
            duI = -spsolve(K, res)

            # Newton-Raphson updates for Lagrange multipliers
            if self.my_model.Bu.shape[1] != 0 and self.my_model.Bu.nnz != 0:
                g_u_shape = np.shape(self.my_model.g_u)

                if self.my_model.g_u.ndim == 1 or (self.my_model.g_u.ndim == 2 and (self.my_model.g_u.shape[0] == 1 or self.my_model.g_u.shape[1] == 1)):
                    dl = -spsolve(csc_array(np.atleast_2d(self.my_model.Bu.T @ spsolve(K, self.my_model.Bu))), self.my_model.Bu.T @ (u1 + duI) - self.my_model.g_u[:, i1])
                else:
                    dl = -spsolve(self.my_model.Bu.T @ spsolve(K.tocsc(), self.my_model.Bu), self.my_model.Bu.T @ (u1 + duI) - self.my_model.g_u[:, i1])
                
                duII = spsolve(K, self.my_model.Bu @ dl)
            else:
                dl = np.zeros_like(l0)
                duII = np.zeros_like(u0)
            
            # Update all state variables
            u1 = u1 + duI + duII
            l1 = l1 + dl
            
            # Compute the restoring force
            r1 = self.my_model.compute_r(u1, np.zeros_like(u1), self.my_model.g_q[:, i1], t1, i1)

            # Evaluation of the residual
            res = r1 - self.my_model.Bf @ self.my_model.g_f[:, i1] - self.my_model.Bu @ l1

            # Convergence tolerance
            tol = (np.linalg.norm(res) * self.my_model.ndof) / (self.my_model.ndof * (1 + np.linalg.norm(self.my_model.Bf @ self.my_model.g_f[:, i1] + self.my_model.Bu @ l1)))

            # Exit condition
            if cc >= self.iter_max or tol < self.tol_min:
                if output == True:
                    # print(f"step {i1} converged in {cc+1} iterations with residual {tol}")
                    print(simulation.msg.format(i1, cc + 1, tol))
                break
            else:
                # Iteration counter increment
                cc += 1
        
        return u1, l1, r1

#%% Arc-length analysis
    def arclen_analysis(self, step1=0, step2=None, output=True):

        if step2 is None:
            step2 = self.my_model.step

        # Error check
        if self.my_model.dofs_u.shape[0] != 1:
            raise ValueError('arclen analysis supports only 1 displacement controlled dof')

        # Initialize increment direction vectors
        self.Du_last = self.my_model.Bu
        self.Dl_last = 0

        # Sequence of analysis steps
        for i in range(step1, step2-1):

            # Single analysis step
            self.u[:, i+1], self.l[:, i+1], self.r[:, i+1] = self.arclen_analysis_step(self.u[:, i], self.l[:, i], self.t[i], i, output)

            # store response for plotting
            self.my_model.u_x[self.my_model.ind_x] = self.u[:,i]

        return self.u, self.l, self.r

    def arclen_analysis_step(self, u0, l0, t0, i0, output):
       
        u1 = u0.copy()
        l1 = l0.copy()
        i1 = i0 + 1
        t1 = t0 + self.my_model.dt

        # Initialize increments
        Du = u1 - u0  # displacement increment (total)
        Dl = l1 - l0  # Lagrange multiplier increment (total)

        ds = self.my_model.g_u[:,i1] - self.my_model.g_u[:,i0]  # arc length

        # Compute the restoring force
        r1 = self.my_model.compute_r(u1, np.zeros_like(u1), self.my_model.g_q[:, i1], t1, i1)

        # Compute the residual of the equilibrium equation
        res = r1 - self.my_model.Bf @ self.my_model.g_f[:, i1] - self.my_model.Bu @ l1
        
        # Iteration counter
        cc = 0

        while True:
            # Jacobian of the residual
            K = self.my_model.compute_K(u1, np.zeros_like(u1), self.my_model.g_q[:, i1], t1, i1)

            # Displacement increments predictors.
            duI = spsolve(K, self.my_model.Bu)
            duII = -spsolve(K, res)

            # Lagrange multiplier predictor.
            dl1, dl2 = self.arclen_analysis_dll(duI, duII, Du, Dl, ds)

            if (Du + duII + dl1 * duI) @ self.Du_last > 0:
                dl = dl1.reshape(1,-1)[0]
            else:
                dl = dl2.reshape(1,-1)[0]

            du = duII + dl * duI

            # Update of displacement and Lagrange multipliers (total increments)
            Du += du
            Dl += dl

            # Update of displacement and Lagrange multipliers
            u1 += du
            l1 += dl

            # Compute the restoring force
            r1 = self.my_model.compute_r(u1, np.zeros_like(u1), self.my_model.g_q[:, i1], t1, i1)

            # Compute the residual of the equilibrium equation
            res = r1 - self.my_model.Bf @ self.my_model.g_f[:, i1] - self.my_model.Bu @ l1

            if self.my_model.Bf.shape[1] != 0:
                tol = np.linalg.norm(res) / (1 + sp.sparse.linalg.norm(self.my_model.Bf * self.my_model.g_f[:, i1] + self.my_model.Bu * l1))
            else:
                tol = np.linalg.norm(res) / (1 + sp.sparse.linalg.norm(self.my_model.Bu * l1))

            if cc >= self.iter_max or tol < self.tol_min:
                if output == True:
                    # print(f'step {i1}, iter {cc+1}, res {np.linalg.norm(res)}')
                    print(simulation.msg.format(i1, cc + 1, tol))
                break
            else:
                cc += 1

        # Store the last increment at convergence.
        self.Du_last = Du
        self.Dl_last = Dl

        return u1, l1, r1

    def arclen_analysis_dll(self, duI, duII, Du, Dl, ds):
        h2 = sp.sparse.linalg.norm(self.my_model.Bu)**2
        
        c1 = duI.T @ duI + self.delta**2 * h2
        c2 = 2 * (Du + duII).T @ duI + 2 * self.delta**2 * Dl * h2
        c3 = (Du + duII).T @ (Du + duII) + Dl**2 * self.delta**2 * h2 - ds**2

        discriminant = c2**2 - 4 * c1 * c3
        div_factor = 1 / (2 * c1)

        if discriminant > 0:
            dl1 = (-c2 + np.sqrt(discriminant)) * div_factor
            dl2 = (-c2 - np.sqrt(discriminant)) * div_factor
        else:
            dl1 = -c2 * div_factor
            dl2 = -c2 * div_factor

        return dl1, dl2

#%% store the results of the analysis step from the recorder fields
    def record_step(self,step=0):
        
        # update each field of recorder data
        for recorder_tag in self.recorder_tags:
            self.recorder_data[recorder_tag][step] = eval('self.my_model.' + recorder_tag)
        
#%% save simulations
    def dump_to_model(self,step=1):
        
        # simulation results to the model
        self.my_model.u = self.u[:,step]
        self.my_model.v = self.v[:,step]
        self.my_model.a = self.a[:,step]
        
        self.my_model.u_x[self.my_model.ind_x] = self.u[:,step]
        self.my_model.v_x[self.my_model.ind_x] = self.v[:,step]
        self.my_model.a_x[self.my_model.ind_x] = self.a[:,step]

        # dump model results to the elements
        # self.my_model.dump_to_elements()
        
