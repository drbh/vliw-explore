def sqrt_fixed(n):
    """
    Compute the square root of n using five fixed iterations of Newton's method.
    This unrolled version avoids any loop constructs.
    """
    if n < 0:
        raise ValueError("Cannot compute square root of a negative number")
    if n == 0:
        return 0
    # Initial guess:
    x = n
    # Unroll 5 iterations of Newton's method
    x = 0.5 * (x + n / x)
    x = 0.5 * (x + n / x)
    x = 0.5 * (x + n / x)
    x = 0.5 * (x + n / x)
    x = 0.5 * (x + n / x)
    return x

def rms_layer_norm_3(x, gamma, epsilon=1e-8):
    """
    Applies RMS Layer Normalization to a fixed-size (3-element) input vector.
    
    Parameters:
      x       : A list of 3 numerical values.
      gamma   : A list of 3 scaling factors.
      epsilon : Small constant for numerical stability.
      
    Returns:
      A list of 3 normalized and scaled values:
          output[i] = (x[i] / sqrt(mean(x^2) + epsilon)) * gamma[i]
    """
    # Compute sum of squares (unrolled for three elements)
    sum_sq = x[0]*x[0] + x[1]*x[1] + x[2]*x[2]
    mean_sq = sum_sq / 3.0

    # Compute RMS using the fixed-iteration sqrt function
    rms = sqrt_fixed(mean_sq + epsilon)
    
    # Compute normalized outputs for each element (unrolled)
    out0 = (x[0] / rms) * gamma[0]
    out1 = (x[1] / rms) * gamma[1]
    out2 = (x[2] / rms) * gamma[2]
    
    return [out0, out1, out2]


x = [3.0, 4.0, 5.0]
gamma = [0.1, 0.2, 0.3]
normalized_x = rms_layer_norm_3(x, gamma)
print(x)
print(normalized_x)
