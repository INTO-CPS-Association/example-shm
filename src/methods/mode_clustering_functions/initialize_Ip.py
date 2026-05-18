from typing import Any, List, Dict
import numpy as np
# pylint: disable=C0103, R0914

def cluster_initial(ip: List[float], data: Dict[str,Any], bound: float = 2) -> Dict[str,Any]:
    """
        Find the initial cluster points

        Args:
            ip (List[float]): Frequency, damping and covariance for the inital point (ip)
            data (Dict[str,Any]): OMA points data
            bound (float): Multiplier on standard deviation
        Returns:
            initial_points (Dict[str,Any]): Initial points to create cluster from

    """
    #Extract data of initial point
    ip_f = ip[0]
    ip_cov_f = ip[1]
    ip_d = ip[2]
    ip_cov_d = ip[3]

    # Confidence interval using the ±2*standard_deviation
    f_lower_bound = ip_f - bound * np.sqrt(ip_cov_f)
    f_upper_bound = ip_f + bound * np.sqrt(ip_cov_f)
    z_lower_bound = ip_d - bound * np.sqrt(ip_cov_d)
    z_upper_bound = ip_d + bound * np.sqrt(ip_cov_d)

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
    initial_points['cov_f'] = data['cov_f'][condition_mask]
    initial_points['d'] = data['damping_ratios'][condition_mask]
    initial_points['cov_d'] = data['cov_d'][condition_mask]
    initial_points['ms'] = data['mode_shapes'][condition_mask,:]
    initial_points['row'] = indices[:,0]
    initial_points['col'] = indices[:,1]

    return initial_points
