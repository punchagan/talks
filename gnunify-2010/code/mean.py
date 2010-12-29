def mean_filter(a):
    """ Mean Filter - Iterates over the image.
    Implemented only for 2 dimensional images. """
    b = a.copy().astype('float32')
    m, n = a.shape
    for i in range(1, m-1):
        for j in range(1, n-1):
            k = a[i-1:i+2, j-1:j+2]
            k_sum = (sum(k) - k[1,1])/8.0
            b[i, j] = k_sum
    return b[1:-1, 1:-1]
        
def mean_arr_filter(a):
    """ Mean Filter - using slicing and NO iteration
    Implemented only for 2 dimensional images. """
    b = a[1:-1, 1:-1].copy().astype('float32')
    b *= -1/8.0
    n, m = a.shape
    for i in range(-1, 2):
        for j in range(-1, 2):
            b += a[1+i:n-1+i, 1+j:m-1+j]/8.0
    return b

