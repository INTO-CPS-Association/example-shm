import numpy as np
from yafem import nodes
from yafem import model
from yafem import simulation
from yafem.elem import beam2d
from yafem.elem import MCK


def eval_yafem_model(pars=None):
    #%% Parameters
    if pars is None: pars = {}
    L   = pars.setdefault('L'  ,0.530)  # [m] ruler length
    ma  = pars.setdefault('ma' ,4.8e-3) # [kg] mass of the accelerometer
    l1  = pars.setdefault('l1' ,0.030)  # [m] distance from the beam top to the top accelerometer
    l2  = pars.setdefault('l2' ,0.0675) # [m] distance between the accelerometers 0.0675
    l3  = pars.setdefault('l3' ,0.070)  # [m] distance between the supports
    l4   = pars.setdefault('l4'  ,0.1289)  # [m] VARIABLE approx. the depth of the "ground"
    E   = pars.setdefault('E'  ,200e9)  # [Pa] Young modulus, normal steel
    b   = pars.setdefault('b'  ,29e-3)  # [m] width of the ruler
    h   = pars.setdefault('h'  ,1e-3)   # [m] thichness of the ruler
    rho = pars.setdefault('rho',7850)   # [kg/m3] density of the steel
    m   = pars.setdefault('m'  ,15e-3)  # [kg] VARIABLE tip mass
    k_rot = pars.setdefault('k_rot' ,10) # [Nm/rad] VARIABLE rotational stiffness
    modes = pars.setdefault('modes' ,3)
    dofs_sel = pars.setdefault('dofs_sel',np.array([1,1]))

    A = b * h
    I = b * h**3/12   

    #%% nodal object
    nodes_pars = {}

    nodes_pars['nodal_data'] = np.array([[8,0.0,L        ,0.0], # tip mass
                                         [7,0.0,L-l1     ,0.0], # acc 1
                                         [6,0.0,L-l1-1*l2,0.0], # acc 3
                                         [5,0.0,L-l1-2*l2,0.0], # acc 2
                                         [4,0.0,L-l1-3*l2,0.0], # acc 4
                                         [3,0.0,l4        ,0.0], # support 2
                                         [2,0.0,l4-l3     ,0.0], # support 1
                                         [1,0.0,0.0      ,0.0],
                                         ])

    # node object
    myNodes = nodes(nodes_pars)      

    #%% Element object

    # accelerometers
    acc_pars = {}
    acc_pars['M'] = np.array([[ma,0,0,0],[0,ma,0,0],[0,0,ma,0],[0,0,0,ma]])
    acc_pars['K'] = np.zeros((4,4))
    acc_pars['dofs'] = np.array([[7,1],[6,1],[5,1],[4,1]])
    mass_acc = MCK(myNodes,acc_pars)

    # tip mass
    mass_pars = {}
    mass_pars['M'] = np.array([[m]])
    mass_pars['K'] = np.zeros((1,1))
    mass_pars['dofs'] = np.array([[8,1]])
    mass_tip = MCK(myNodes,mass_pars)

    # springs
    spring_pars = {}
    spring_pars['K'] = np.array([[k_rot,0],[0,k_rot]])
    spring_pars['dofs'] = np.array([[3,3],[2,3]])
    springs = MCK(myNodes,spring_pars)

    # Common beam parameters
    beam2d_pars = {}
    beam2d_pars['E'] = E
    beam2d_pars['rho'] = rho
    beam2d_pars['A'] = A
    beam2d_pars['I'] = I

    beam2d1_pars = beam2d_pars
    beam2d1_pars['nodal_labels'] = np.array([1,2])
    beam2d1 = beam2d(myNodes,beam2d1_pars)

    beam2d2_pars = beam2d_pars
    beam2d2_pars['nodal_labels'] = np.array([2,3])
    beam2d2 = beam2d(myNodes,beam2d2_pars)

    beam2d3_pars = beam2d_pars
    beam2d3_pars['nodal_labels'] = np.array([3,4])
    beam2d3 = beam2d(myNodes,beam2d3_pars)

    beam2d4_pars = beam2d_pars
    beam2d4_pars['nodal_labels'] = np.array([4,5])
    beam2d4 = beam2d(myNodes,beam2d4_pars)

    beam2d5_pars = beam2d_pars
    beam2d5_pars['nodal_labels'] = np.array([5,6])
    beam2d5 = beam2d(myNodes,beam2d5_pars)

    beam2d6_pars = beam2d_pars
    beam2d6_pars['nodal_labels'] = np.array([6,7])
    beam2d6 = beam2d(myNodes,beam2d6_pars)

    beam2d7_pars = beam2d_pars
    beam2d7_pars['nodal_labels'] = np.array([7,8])
    beam2d7 = beam2d(myNodes,beam2d7_pars)

    # list of all elements
    myElements = [mass_acc,
                  mass_tip,
                  springs,
                  beam2d1,
                  beam2d2,
                  beam2d3,
                  beam2d4,
                  beam2d5,
                  beam2d6,
                  beam2d7,
                  ]
    
    #%% model object
    model_pars = {}
    model_pars['dofs_c'] = np.array([[3,1],
                                     [3,2],
                                     [2,1],
                                     [2,2],
                                    ]) 
    
    model_pars['damping_model'] = 'proportional'
    model_pars['alpha'] = 2.0
    model_pars['beta'] = 0.1

    # modal analysis
    myModel = model(myNodes, myElements,model_pars)

    # simulation
    mySimulation = simulation(myModel)

    # modal analysis
    dofs_sel = np.array(dofs_sel)
    omega, phi = myModel.compute_modal_ss(modes,dofs_sel)
    idxs_sel = myModel.find_dofs(dofs_sel)
    phi_sel = phi[idxs_sel,:]

    return omega, phi, phi_sel, myModel, mySimulation
