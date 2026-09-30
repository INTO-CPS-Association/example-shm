from typing import Any, Dict
import numpy as np

def global_uncertainty(cluster_dict: Dict[str, Any],bound: int = 2):
    """
    Calculate the global uncertainty of a cluster
    Args:
        cluster_dict (Dict[str, Any]): Dictionary containing all clusters
        bound (int): Standard deviation multiplier
    Returns:
        cluster_dict (Dict[str, Any]): Dictionary containing all clusters, now updated with global uncertainty
    """
    for key in cluster_dict:
        cluster = cluster_dict[key]
        SUM_cov = None
        cov_stack = None
        U_stack = None
        # print(f"\n freq: {cluster['median_f']}")
        for ii, U in enumerate(cluster['Ufx']): # eq. (10)
            cov_fx = np.matmul(U, U.T) # eq. (40) Döhler
            # print(cluster['model_order'][ii],cov_fx[0,0]**0.5*2)
            # print(cluster['model_order'][ii],cluster['std_f'][ii])
            if np.isfinite(np.linalg.cond(cov_fx)):
                cov_inv = np.linalg.inv(cov_fx)
            else:
                try:
                    cov_inv = np.linalg.pinv(cov_fx)
                    print("Cov_fx is singular")
                    print(np.linalg.pinv(cov_fx))
                except:
                    continue
            # constructing eq. (7) and (8)
            if SUM_cov is None:
                SUM_cov = cov_inv
                cov_stack = cov_inv
            else:
                SUM_cov = SUM_cov + cov_inv
                cov_stack = np.hstack((cov_stack,cov_inv))
            # constructing eq. (9)
            if U_stack is None:
                U_stack = U
            else:
                U_stack = np.vstack((U_stack,U))
        cov_cluster = np.matmul(U_stack, U_stack.T) # calculate eq. (9)

        # calculate eq. (7)
        try:
            SUM_cov_inv = np.linalg.inv(SUM_cov)
        except:
            print("Sum_cov_inv is singular.")
            SUM_cov_inv = np.linalg.pinv(SUM_cov)
        # calculate eq. (6)
        jacobian = np.matmul(SUM_cov_inv,cov_stack)
        # calculate eq. (5)
        global_cov = np.matmul(np.matmul(jacobian,cov_cluster),jacobian.T)
        cluster_dict[key]['global_std']  = global_cov**0.5
        # print(global_cov**0.5)
        cluster_dict[key]['global_ci']  = global_cov**0.5 * bound
        # print(global_cov**0.5 * bound)
        # print(cluster['median_f'],cluster_dict[key]['global_ci'])

    return cluster_dict

# def tracked_covariance(tracked_cluster_list: Dict[str, Any],cluster: Dict[str, Any],params):
#     """
#     Calculate the global uncertainty of a cluster
#     Args:
#         cluster_dict (Dict[str, Any]): Dictionary containing all clusters
#     Returns:
#         cluster_dict (Dict[str, Any]): Dictionary containing all clusters, now updated with global uncertainty
#     """
#     for t_cluster in tracked_cluster_list:
#         U_stack = None
#         SUM_cov = None
#         for ii, U in enumerate(t_cluster['Ufx']):
#             cov_fx = np.matmul(U, U.T)
#             if np.isfinite(np.linalg.cond(cov_fx)):
#                 cov_inv = np.linalg.inv(cov_fx)
#             else:
#                 print("Cov_fx is singular")
#                 continue
#             if SUM_cov is None:
#                 SUM_cov = cov_inv
#                 cov_stack = cov_inv
#             else:
#                 SUM_cov = SUM_cov + cov_inv
#                 cov_stack = np.hstack((cov_stack,cov_inv))
#             if U_stack is None:
#                 U_stack = U
#             else:
#                 U_stack = np.vstack((U_stack,U))

#     for ii, U in enumerate(cluster['Ufx']): # eq. (10)
#         cov_fx = np.matmul(U, U.T) # eq. (40) Döhler
#         if np.isfinite(np.linalg.cond(cov_fx)):
#             cov_inv = np.linalg.inv(cov_fx)
#         else:
#             print("Cov_fx is singular")
#             continue
#         # constructing eq. (7) and (8)
#         SUM_cov = SUM_cov + cov_inv
#         cov_stack = np.hstack((cov_stack,cov_inv))
#         # constructing eq. (9)
#         if U_stack is None:
#             U_stack = U
#         else:
#             U_stack = np.vstack((U_stack,U))
        
#         cov_cluster = np.matmul(U_stack, U_stack.T)
#         # calculate eq. (7)
#         SUM_cov_inv = np.linalg.inv(SUM_cov)
#         # calculate eq. (6)
#         jacobian = np.matmul(SUM_cov_inv,cov_stack)
#         # calculate eq. (5)
#         global_cov = np.matmul(np.matmul(jacobian,cov_cluster),jacobian.T)

#     return global_cov
