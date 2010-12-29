from pylab import imread, np, average, zeros_like, figure, imshow, show, title

colors = ['R', 'G', 'B']

def zoom(x, factor=2):
    rows, cols = x.shape
    row_stride, col_stride = x.strides
    view = np.lib.stride_tricks.as_strided(x,
                        (rows, factor, cols, factor),
                        (row_stride, 0, col_stride, 0))
    return view.reshape((rows*factor, cols*factor))

def show_channels(I):
    for i in range(3):
        J = zeros_like(I)
        J[:, :, i] = I[:, :, i]
        figure(i)
        imshow(J)


def show_grey_channels(I):
    K = average(I, axis=2)
    for i in range(3):
        J = zeros_like(I)
        J[:, :, i] = K
        figure(i+10)
        imshow(J)

def subsample(I):
    for i in range(3):
        J = I.copy()
        J[:, :, i] = zoom(I[::4, ::4, i], 4)
        figure(i)
        title("%s channel subsampled" %colors[i])
        imshow(J)

def swap_subsample(I, k=1):
    for c, color in enumerate(colors):
        print "%s <-- %s" %(colors[c], colors[(c+k)%3])
    for i in range(3):
        J = zeros_like(I)
        for j in range(3):
            J[:, :, j] = I[:, :, (j+k)%3]
        J[:, :, i] = zoom(I[::4, ::4, (i+k)%3], 4)
        figure(i+10)
        title("%s channel subsampled" %colors[i])
        imshow(J)

if __name__=="__main__":
    I = imread('lena.png')
    # figure(100)
    # imshow(I)
    # show_channels(I)
    # show_grey_channels(I)
    # show()
    subsample(I)
    swap_subsample(I, 1)
    show()

