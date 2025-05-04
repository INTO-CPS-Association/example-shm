import numpy as np
from methods.packages.yafem import nodes
from methods.packages.yafem import model
from methods.packages.yafem.elem import beam2d
from methods.packages.yafem.elem import MCK

def eval_yafem_model(pars=None):
    if pars is None: pars = {}
    pars.setdefault('b'  ,29e-3)    # [m] width of the beam
    pars.setdefault('h'  ,1e-3)     # [m] heigh of the beam
    pars.setdefault('E'  ,210e9)    # [Pa] youngs modulus
    pars.setdefault('rho',7850)     # [kg/m3] density
    pars.setdefault('L'  ,0.530)    # [m] total length of the beam
    pars.setdefault('Lab',0.423)    # [m] total length of the beam
    pars.setdefault('l0' ,0.067)    # [m] distance of cantileveredness
    pars.setdefault('l1' ,0.030)    # [m] distance to end of beam
    pars.setdefault('l2' ,0.135)    # [m] distance to second sensor (mass)
    pars.setdefault('ma' ,4.8e-3)   # [kg] mass
    pars.setdefault('m'  ,4.8e-3)   # [kg] mass
    pars.setdefault('k'  ,3.5e3)    # stiffness
    pars.setdefault('dofs_sel',np.array([1,1]))
    pars.setdefault('modes'   ,3)

    L   = pars['L']
    Lab = pars['Lab']
    l0  = pars['l0']
    l1  = pars['l1']
    l2  = pars['l2']
    A   = pars['b'] * pars['h']
    I   = pars['b'] * pars['h']**3/12
    E   = pars['E']
    rho = pars['rho']
    k   = pars['k']
    ma  = pars['ma']
    m   = pars['m']
    dofs_sel = pars['dofs_sel']
    modes    = pars['modes']

    # nodal parameters
    nodes_pars = {}
    nodes_pars['nodal_data'] = np.array([[1,0.0,0.0     ,0.0],
                                         [2,0.0,L-Lab-l0,0.0], # support 1
                                         [3,0.0,L-Lab   ,0.0], # support 2
                                         [4,0.0,L-l1-l2 ,0.0], # acc 1
                                         [5,0.0,L-l1    ,0.0], # acc 2
                                         [6,0.0,L       ,0.0], # tip mass
                                         ])

    # node object
    myNodes = nodes(nodes_pars)      

    #%% Element object

    # accelerometers
    acc_pars = {}
    acc_pars['M'] = np.array([[ma,0],[0,ma]])
    acc_pars['K'] = np.zeros((2,2))
    acc_pars['dofs'] = np.array([[4,1],[5,1]])
    mass = MCK(myNodes,acc_pars)

    # tip mass
    mass_pars = {}
    mass_pars['M'] = np.array([[m,0,0],[0,m,0],[0,0,m]])
    mass_pars['K'] = np.zeros((3,3))
    mass_pars['dofs'] = np.array([[6,1],[6,2],[6,3]])
    mass_tip = MCK(myNodes,mass_pars)

    # springs
    spring1_pars = {}
    spring1_pars['K'] = np.array([[k]])
    spring1_pars['dofs'] = np.array([[2,3]])
    spring1 = MCK(myNodes,spring1_pars)

    # springs
    spring2_pars = {}
    spring2_pars['K'] = np.array([[k]])
    spring2_pars['dofs'] = np.array([[3,3]])
    spring2 = MCK(myNodes,spring2_pars)

    beam2d1_pars = {}
    beam2d1_pars['E'] = E
    beam2d1_pars['rho'] = rho
    beam2d1_pars['A'] = A
    beam2d1_pars['I'] = I
    beam2d1_pars['nodal_labels'] = np.array([1,2])
    beam2d1 = beam2d(myNodes,beam2d1_pars)

    beam2d2_pars = {}
    beam2d2_pars['E'] = E
    beam2d2_pars['rho'] = rho
    beam2d2_pars['A'] = A
    beam2d2_pars['I'] = I
    beam2d2_pars['nodal_labels'] = np.array([2,3])
    beam2d2 = beam2d(myNodes,beam2d2_pars)

    beam2d3_pars = {}
    beam2d3_pars['E'] = E
    beam2d3_pars['rho'] = rho
    beam2d3_pars['A'] = A
    beam2d3_pars['I'] = I
    beam2d3_pars['nodal_labels'] = np.array([3,4])
    beam2d3 = beam2d(myNodes,beam2d3_pars)

    beam2d4_pars = {}
    beam2d4_pars['E'] = E
    beam2d4_pars['rho'] = rho
    beam2d4_pars['A'] = A
    beam2d4_pars['I'] = I
    beam2d4_pars['nodal_labels'] = np.array([4,5])
    beam2d4 = beam2d(myNodes,beam2d4_pars)

    beam2d5_pars = {}
    beam2d5_pars['E'] = E
    beam2d5_pars['rho'] = rho
    beam2d5_pars['A'] = A
    beam2d5_pars['I'] = I
    beam2d5_pars['nodal_labels'] = np.array([5,6])
    beam2d5 = beam2d(myNodes,beam2d5_pars)

    # list of all elements
    myElements = [mass,
                  mass_tip,
                  spring1,
                  spring2,
                  beam2d1,
                  beam2d2,
                  beam2d3,
                  beam2d4,
                  beam2d5,
                  ]
    #%% model parameters
    model_pars = {}
    model_pars['dofs_c'] = np.array([[2,1],
                                     [2,2],
                                     [3,1],
                                     [3,2],
                                    ]) 
    model_pars['damping_model'] = 'proportional'
    model_pars['alpha'] = 2.0
    model_pars['beta'] = 0.1

    # modal analysis
    myModel = model(myNodes, myElements,model_pars)

    # modal analysis
    omega, phi = myModel.compute_modal(modes)
    idxs_sel = myModel.find_dofs(dofs_sel)
    phi_sel = phi[idxs_sel,:]

    return omega, phi, phi_sel, myModel
