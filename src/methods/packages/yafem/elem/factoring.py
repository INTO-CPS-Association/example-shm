import sympy as sp

def factoring(A):
    # Extract numerators and denominators separately
    numerators   = [sp.numer(x) for x in A]
    denominators = [sp.denom(x) for x in A]

    # Compute GCD of numerators and denominators
    gcd_numer = sp.gcd(tuple(numerators))  # Common factor from numerators
    gcd_denom = sp.lcm(tuple(denominators))  # Least Common Multiple of denominators

    # Compute the overall factor
    common_factor = sp.simplify(gcd_numer / gcd_denom)

    # Ensure no fractions remain inside the matrix
    factored_matrix = sp.simplify(A * gcd_denom / gcd_numer)  # Scale entries to be integer
    

    # Return the structured output
    result_A = sp.MatMul(common_factor, factored_matrix, evaluate=False)
    
    return result_A
