import numpy as np
from scipy.stats import chi2

def MSD(mu,cov_X,x,cov_fd,chi_dof,alpha=0.05):
    """
    Calculate Mahalnobis squared distance
    Args:
        mu (np.array): Mean vector of historical feature matrix
        cov_X (np.array): Covariance of historical feature matrix
        x (np.array): New feature vector (cluster)
        cov_fd (np.array): Covariance of new cluster
        chi_dof (int): chi2 degrees of freedom
        alpha (float): Significance level
    Returns
        d2 (float): Mahalanobis squared distance
        t (float): Threshold for chi2-distribution
    """
    cov_X[np.isnan(cov_X)] = 0
    cov_fd[np.isnan(cov_fd)] = 0
    cov = cov_X + cov_fd
    try:
        d2 = ((x - mu).T @ np.linalg.inv(cov) @ (x - mu)).reshape(-1)
        # d2 = ((x - mu).T @ np.linalg.pinv(cov) @ (x - mu)).reshape(-1)
    except:
        d2 = ((x - mu).T @ np.linalg.pinv(cov) @ (x - mu)).reshape(-1)

    # Mahalanobis chi2 
    alpha = 0.05
    t = chi2.ppf(1-alpha,chi_dof)

    return d2, t

def construct_x(clusters,params):
    """
    Construct a matrix of mode shapes
        Args:
            clusters (Optional(List or Dict[str,Any])): Cluster either a list, e.g. tracked cluster group, or dictionary, e.g. single cluster.
            params (Dict[str,Any]): Settings/parameters for 'mstab'
        returns:
            X (np.array): Matrix of features
    """
    USE_MODE_SHAPES = params.get("MDS_use_mode_shapes",False)

    m_f = []
    m_d = []
    mode_shapes = None
    if type(clusters) == list:
        for t_cluster in clusters:
            m_f.append(t_cluster["median_f"])
            m_d.append(t_cluster["median_d"])
            if USE_MODE_SHAPES:
                stacked_mode_shape = construct_ms(t_cluster,params)
                if mode_shapes is None:
                    mode_shapes = stacked_mode_shape
                else:
                    mode_shapes = np.hstack((mode_shapes,stacked_mode_shape))
        # Mahalanobis
        X = np.vstack((np.array(m_f),np.array(m_d)))
    elif type(clusters) == dict:
        cluster = clusters
        omega = cluster['median_f']
        zeta = cluster['median_d']
        X = np.vstack((omega,zeta)) # constructing x for Mahalanobis
        if USE_MODE_SHAPES:
            mode_shapes = construct_ms(cluster,params)

    if USE_MODE_SHAPES:
        X = np.vstack((X,mode_shapes))

    return X

def construct_ms(cluster,params):
    """
    Construct a matrix of mode shapes
    Args:
        cluster (Dict[str,Any]): Cluster
        params (Dict[str,Any]): Settings/parameters for 'mstab'
    returns:
        mode_shapes (np.array): Matrix of mode shapes
    """
    mode_shapes_r = None
    print("Using mode shapes with mahalanobis uses normalization, which may be problematic if the first dof close to zero")
    for jj, ms in enumerate(cluster['mode_shapes']):
        try:
            params['mstab']
        except:
            raise KeyError("'mstab' missing in settings")
        if jj > params['mstab']:
            break
        if jj == 0:
            ms_1 = ms[0]
        ms_n = (np.conjugate(ms_1)/abs(ms_1)**2)*ms.T #Normalization
        ms_r = np.real(ms_n[1:]) # We don't need the first value, 1.
        ms_i = np.imag(ms_n[1:])
        if mode_shapes_r is None:
            mode_shapes_r = ms_r.reshape(-1,1)
            mode_shapes_i = ms_i.reshape(-1,1)
        else:
            mode_shapes_r = np.hstack((mode_shapes_r,ms_r.reshape(-1,1)))
            mode_shapes_i = np.hstack((mode_shapes_i,ms_i.reshape(-1,1)))
    
    stacked_mode_shape = np.vstack((mode_shapes_r,mode_shapes_i))
    mode_shapes = np.mean(stacked_mode_shape,axis=1).reshape(-1,1)

    return mode_shapes
