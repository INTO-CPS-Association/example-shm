from typing import Any, List, Dict
import numpy as np
# pylint: disable=C0103, R0914

def cluster_initial(ip: List[float], data: Dict[str,Any], params: Dict[str,Any]) -> Dict[str,Any]:
    """
        Find the initial cluster points

        Args:
            ip (List[float]): Frequency, damping and covariance for the inital point (ip)
            data (Dict[str,Any]): OMA points data
            params (Dict[str,Any]): Parameters
        Returns:
            initial_points (Dict[str,Any]): Initial points to create cluster from

    """
    #Extract data of initial point
    ip_f = ip[0]
    ip_std_f = ip[1]*params['bound_multiplier']
    ip_d = ip[2]
    ip_std_d = ip[3]*params['bound_multiplier']

    # Confidence interval using the ±2*standard_deviation
    f_lower_bound = ip_f - ip_std_f
    f_upper_bound = ip_f + ip_std_f
    z_lower_bound = ip_d - ip_std_d
    z_upper_bound = ip_d + ip_std_d

    frequencies = data['frequencies']
    damping_ratios = data['damping_ratios']

    # Find elements within the current limit that are still ungrouped
    condition_mask = ((frequencies >= f_lower_bound)
                      & (frequencies <= f_upper_bound)
                      & (damping_ratios >= z_lower_bound)
                      & (damping_ratios <= z_upper_bound))# & ungrouped_mask
    indices = np.argwhere(condition_mask)  # Get indices satisfying the condition

    #Generate the data for inital points
    initial_points = {}
    initial_points['f'] = data['frequencies'][condition_mask]
    initial_points['std_f'] = data['std_f'][condition_mask]
    initial_points['d'] = data['damping_ratios'][condition_mask]
    initial_points['std_d'] = data['std_d'][condition_mask]
    initial_points['ms'] = data['mode_shapes'][condition_mask,:]
    initial_points['row'] = indices[:,0]
    initial_points['col'] = indices[:,1]

    #Reorder initial points, so ip is the first point in I_p
    if initial_points['f'][0] != ip_f:
        initial_points2 = initial_points.copy()
        id_0 = np.argwhere(initial_points['f'] == ip_f)
        id_rest = np.argwhere(initial_points['f'] != ip_f)
        for key in initial_points2:
            if key == "ms":
                initial_points2[key] = np.append(initial_points[key][id_0,:],initial_points[key][id_rest,:]).reshape(initial_points[key].shape)
            else:
                initial_points2[key] = np.append(initial_points[key][id_0],initial_points[key][id_rest])
        initial_points = initial_points2

    return initial_points
