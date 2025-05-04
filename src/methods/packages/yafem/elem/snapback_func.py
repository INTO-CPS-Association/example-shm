import numpy 

def snapback_r(W, A, E, L, a, _Dummy_34):
    [u1, u2] = _Dummy_34
    return numpy.array([[A*E*W*(u1 - u2)/L], [A*E*(L**2*W*(-u1 + u2) + 2*u2*(a**2 - 1.5*a*u2 + 0.5*u2**2))/L**3]])

def snapback_K(W, A, E, L, a, _Dummy_35):
    [u1, u2] = _Dummy_35
    return numpy.array([[A*E*W/L, -A*E*W/L], [-A*E*W/L, A*E*(L**2*W + 2*a**2 - 3.0*a*u2 + 1.0*u2**2 + 2*u2*(-1.5*a + 1.0*u2))/L**3]])

