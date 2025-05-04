import numpy 

def snapthrough_r0(A, E, a, L):
    return numpy.array([[0.0, -2.0*a, -a]])

def snapthrough_K0(A, E, a, L):
    return numpy.array([[-1.57735026918963*a, -0.422649730810374*a]])

def snapthrough_rmax(A, E, a, L):
    return 0.38490017945975*A*E*a**3/L**3

def snapthrough_r(A, E, a, L, u):
    return 2*A*E*a**3*(u/a + 1.5*u**2/a**2 + 0.5*u**3/a**3)/L**3

def snapthrough_K(A, E, a, L, u):
    return 2*A*E*a**3*(a**(-1.0) + 3.0*u/a**2 + 1.5*u**2/a**3)/L**3

