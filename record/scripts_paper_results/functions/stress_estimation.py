import numpy as np
import functions.fun_cantilever_beam_new as beam_new

def estimate_stress(model_pars,displacement,extraction_lists):
    _, _, _, Model, _ = beam_new.eval_yafem_model(model_pars)

    N = np.max(displacement.shape)
    s = Model.my_elements[extraction_lists['elements'][0]].s_phi.shape[0]
    stress = np.zeros((len(extraction_lists['elements']),s,N)) # s x m
    strain = np.zeros((len(extraction_lists['elements']),s,N)) # s x m
    moment = np.zeros((len(extraction_lists['elements']),s,N)) # s x m

    print(displacement.shape)
    print(Model.my_elements[extraction_lists['elements'][0]].s_phi.shape)
    print(Model.dofs)
    print(model_pars)

    for idx, element in enumerate(extraction_lists['elements']):
        I = Model.my_elements[element].I
        moment[idx,:] = (Model.my_elements[element].s_phi @ displacement) # [Nm]
        stress[idx,:] = (Model.my_elements[element].s_phi @ displacement) * - extraction_lists['y'][idx] / I / 10**6 # [MPa]
        strain[idx,:] = (Model.my_elements[element].e_phi @ displacement)
    
    return moment, stress, strain