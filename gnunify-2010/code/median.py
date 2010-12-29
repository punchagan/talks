def med_filter(a):
    """ Median Filter - Iterates over the image. """
    b = a.copy()
    m, n = a.shape
    for i in range(1, m-1):
        for j in range(1, n-1):
            k = a[i-1:i+2, j-1:j+2]
            med_val = median(k.flatten())
            b[i, j] = med_val
    return b
        
def med_arr_filter(a):
    """ Median Filter - using slicing and NO iteration"""
    A = []
    n, m = a.shape
    for i in range(-1, 2):
        for j in range(-1, 2):
            A.append(a[1+i:n-1+i, 1+j:m-1+j])
    A = array(A)
    return median(A, axis=0)
