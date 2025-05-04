import numpy

def beam2d_gen_Ka(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[A*E/L, -A*E/L], [-A*E/L, A*E/L]])

def beam2d_gen_Kwa(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[(1/3)*L*k0a, (1/6)*L*k0a], [(1/6)*L*k0a, (1/3)*L*k0a]])

def beam2d_gen_Ma(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[(1/3)*A*L*rho, (1/6)*A*L*rho], [(1/6)*A*L*rho, (1/3)*A*L*rho]])

def beam2d_gen_fca(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[(1/2)*L*fa], [(1/2)*L*fa]])

def beam2d_gen_fta(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[-A*E*alpha*theta], [A*E*alpha*theta]])

def beam2d_gen_Kb(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[12*E*I/L**3, 6*E*I/L**2, -12*E*I/L**3, 6*E*I/L**2], [6*E*I/L**2, 4*E*I/L, -6*E*I/L**2, 2*E*I/L], [-12*E*I/L**3, -6*E*I/L**2, 12*E*I/L**3, -6*E*I/L**2], [6*E*I/L**2, 2*E*I/L, -6*E*I/L**2, 4*E*I/L]])

def beam2d_gen_Kwb(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[(13/35)*L*k0b, (11/210)*L**2*k0b, (9/70)*L*k0b, -13/420*L**2*k0b], [(11/210)*L**2*k0b, (1/105)*L**3*k0b, (13/420)*L**2*k0b, -1/140*L**3*k0b], [(9/70)*L*k0b, (13/420)*L**2*k0b, (13/35)*L*k0b, -11/210*L**2*k0b], [-13/420*L**2*k0b, -1/140*L**3*k0b, -11/210*L**2*k0b, (1/105)*L**3*k0b]])

def beam2d_gen_Mb(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[(13/35)*A*L*rho, (11/210)*A*L**2*rho, (9/70)*A*L*rho, -13/420*A*L**2*rho], [(11/210)*A*L**2*rho, (1/105)*A*L**3*rho, (13/420)*A*L**2*rho, -1/140*A*L**3*rho], [(9/70)*A*L*rho, (13/420)*A*L**2*rho, (13/35)*A*L*rho, -11/210*A*L**2*rho], [-13/420*A*L**2*rho, -1/140*A*L**3*rho, -11/210*A*L**2*rho, (1/105)*A*L**3*rho]])

def beam2d_gen_fcb(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[(1/2)*L*fb], [(1/12)*L**2*fb], [(1/2)*L*fb], [-1/12*L**2*fb]])

def beam2d_gen_Na_mid(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[1/2, 1/2]])

def beam2d_gen_Nb_mid(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[1/2, (1/8)*L, 1/2, -1/8*L]])

def beam2d_gen_Ba_mid(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[-1/L, L**(-1.0)]])

def beam2d_gen_Bb_mid(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[0, -1/L, 0, L**(-1.0)]])

def beam2d_gen_Dcs_mid(A, E, I, L, alpha, fa, fb, k0a, k0b, rho, theta):
    return numpy.array([[A*E, 0], [0, E*I]])

