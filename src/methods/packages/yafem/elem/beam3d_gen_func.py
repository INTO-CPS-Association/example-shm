import numpy

def beam3d_gen_Ka(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[A*E/L, -A*E/L], [-A*E/L, A*E/L]])

def beam3d_gen_Kwa(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[(1/3)*L*k0a, (1/6)*L*k0a], [(1/6)*L*k0a, (1/3)*L*k0a]])

def beam3d_gen_Ma(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[(1/3)*A*L*rho, (1/6)*A*L*rho], [(1/6)*A*L*rho, (1/3)*A*L*rho]])

def beam3d_gen_fca(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[(1/2)*L*fa], [(1/2)*L*fa]])

def beam3d_gen_fta(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[-A*E*alpha*theta], [A*E*alpha*theta]])

def beam3d_gen_Kby(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[12*E*Iyy/L**3, 6*E*Iyy/L**2, -12*E*Iyy/L**3, 6*E*Iyy/L**2], [6*E*Iyy/L**2, 4*E*Iyy/L, -6*E*Iyy/L**2, 2*E*Iyy/L], [-12*E*Iyy/L**3, -6*E*Iyy/L**2, 12*E*Iyy/L**3, -6*E*Iyy/L**2], [6*E*Iyy/L**2, 2*E*Iyy/L, -6*E*Iyy/L**2, 4*E*Iyy/L]])

def beam3d_gen_Kbz(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[12*E*Ixx/L**3, -6*E*Ixx/L**2, -12*E*Ixx/L**3, -6*E*Ixx/L**2], [-6*E*Ixx/L**2, 4*E*Ixx/L, 6*E*Ixx/L**2, 2*E*Ixx/L], [-12*E*Ixx/L**3, 6*E*Ixx/L**2, 12*E*Ixx/L**3, 6*E*Ixx/L**2], [-6*E*Ixx/L**2, 2*E*Ixx/L, 6*E*Ixx/L**2, 4*E*Ixx/L]])

def beam3d_gen_Kwby(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[(13/35)*L*k0b, (11/210)*L**2*k0b, (9/70)*L*k0b, -13/420*L**2*k0b], [(11/210)*L**2*k0b, (1/105)*L**3*k0b, (13/420)*L**2*k0b, -1/140*L**3*k0b], [(9/70)*L*k0b, (13/420)*L**2*k0b, (13/35)*L*k0b, -11/210*L**2*k0b], [-13/420*L**2*k0b, -1/140*L**3*k0b, -11/210*L**2*k0b, (1/105)*L**3*k0b]])

def beam3d_gen_Kwbz(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[(13/35)*L*k0b, -11/210*L**2*k0b, (9/70)*L*k0b, (13/420)*L**2*k0b], [-11/210*L**2*k0b, (1/105)*L**3*k0b, -13/420*L**2*k0b, -1/140*L**3*k0b], [(9/70)*L*k0b, -13/420*L**2*k0b, (13/35)*L*k0b, (11/210)*L**2*k0b], [(13/420)*L**2*k0b, -1/140*L**3*k0b, (11/210)*L**2*k0b, (1/105)*L**3*k0b]])

def beam3d_gen_Mby(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[(1/35)*rho*(13*A*L**2 + 42*Iyy)/L, (1/210)*rho*(11*A*L**2 + 21*Iyy), (3/70)*rho*(3*A*L**2 - 28*Iyy)/L, (1/420)*rho*(-13*A*L**2 + 42*Iyy)], [(1/210)*rho*(11*A*L**2 + 21*Iyy), (1/105)*L*rho*(A*L**2 + 14*Iyy), (1/420)*rho*(13*A*L**2 - 42*Iyy), (1/420)*L*rho*(-3*A*L**2 - 14*Iyy)], [(3/70)*rho*(3*A*L**2 - 28*Iyy)/L, (1/420)*rho*(13*A*L**2 - 42*Iyy), (1/35)*rho*(13*A*L**2 + 42*Iyy)/L, (1/210)*rho*(-11*A*L**2 - 21*Iyy)], [(1/420)*rho*(-13*A*L**2 + 42*Iyy), (1/420)*L*rho*(-3*A*L**2 - 14*Iyy), (1/210)*rho*(-11*A*L**2 - 21*Iyy), (1/105)*L*rho*(A*L**2 + 14*Iyy)]])

def beam3d_gen_Mbz(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[(1/35)*rho*(13*A*L**2 + 42*Ixx)/L, (1/210)*rho*(-11*A*L**2 - 21*Ixx), (3/70)*rho*(3*A*L**2 - 28*Ixx)/L, (1/420)*rho*(13*A*L**2 - 42*Ixx)], [(1/210)*rho*(-11*A*L**2 - 21*Ixx), (1/105)*L*rho*(A*L**2 + 14*Ixx), (1/420)*rho*(-13*A*L**2 + 42*Ixx), (1/420)*L*rho*(-3*A*L**2 - 14*Ixx)], [(3/70)*rho*(3*A*L**2 - 28*Ixx)/L, (1/420)*rho*(-13*A*L**2 + 42*Ixx), (1/35)*rho*(13*A*L**2 + 42*Ixx)/L, (1/210)*rho*(11*A*L**2 + 21*Ixx)], [(1/420)*rho*(13*A*L**2 - 42*Ixx), (1/420)*L*rho*(-3*A*L**2 - 14*Ixx), (1/210)*rho*(11*A*L**2 + 21*Ixx), (1/105)*L*rho*(A*L**2 + 14*Ixx)]])

def beam3d_gen_fcby(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[(1/2)*L*fby], [(1/12)*L**2*fby], [(1/2)*L*fby], [-1/12*L**2*fby]])

def beam3d_gen_fcbz(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[(1/2)*L*fbz], [-1/12*L**2*fbz], [(1/2)*L*fbz], [(1/12)*L**2*fbz]])

def beam3d_gen_Kt(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[G*Jv/L, -G*Jv/L], [-G*Jv/L, G*Jv/L]])

def beam3d_gen_Mt(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[(1/3)*Jv*L*rho, (1/6)*Jv*L*rho], [(1/6)*Jv*L*rho, (1/3)*Jv*L*rho]])

def beam3d_gen_Na_mid(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[1/2, 1/2]])

def beam3d_gen_Nby_mid(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[1/2, (1/8)*L, 1/2, -1/8*L]])

def beam3d_gen_Nbz_mid(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[1/2, -1/8*L, 1/2, (1/8)*L]])

def beam3d_gen_Ba_mid(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[-1/L, L**(-1.0)]])

def beam3d_gen_Bby_mid(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[0, -1/L, 0, L**(-1.0)]])

def beam3d_gen_Bbz_mid(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[0, L**(-1.0), 0, -1/L]])

def beam3d_gen_Dcs_mid(A, E, G, Ixx, Iyy, Jv, L, alpha, fa, fby, fbz, k0a, k0b, rho, theta):
    return numpy.array([[A*E, 0, 0], [0, E*Iyy, 0], [0, 0, E*Ixx]])

