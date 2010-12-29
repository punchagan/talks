from PIL import Image, ImageDraw, ImageFont
from pylab import imread, imshow, sum, average, array, argsort, show
import os

fontpath = "/usr/share/fonts/truetype/freefont"

def txt2img(label, fontname="FreeMono.ttf", fgcolor=0,
            bgcolor=255, rotate_angle=0, n=1):
    """Render label as image."""

    font = ImageFont.truetype(os.path.join(fontpath,fontname), 12)

    imgOut = Image.new("L", (20,49), bgcolor)

    # calculate space needed to render text
    # square blocks of size nxn are rendered
    draw = ImageDraw.Draw(imgOut)
    sizex, sizey = draw.textsize(label*n, font=font)

    imgOut = imgOut.resize((sizex,sizey*n))

    # render label into image draw area
    draw = ImageDraw.Draw(imgOut)
    for i in range(n):
        draw.text((0, sizey*i), label*n, fill=fgcolor, font=font)

    if rotate_angle:
        imgOut = imgOut.rotate(rotate_angle)

    return imgOut

def get_images(dirname="sample", num=10):
    if not os.path.isdir(dirname):
        if os.path.exists(dirname):
            print "Cannot create directory %s" %dirname
            raise SystemExit
        os.mkdir(dirname, 0755)
    for i in range(32, 127):
        i_img = txt2img(chr(i), n=num)
        i_img_name = os.path.join(".", dirname, str(i)+".png")
        i_img.save(i_img_name, format="PNG")
        print "saved %s" %i_img_name

def get_density_stats(dirname="sample"):
    img_stats = []
    chr_density_sort = []
    tree = os.walk(dirname)
    
    for subfol in tree:
        img_path = subfol[0]
        img_files = subfol[2]
        for img in img_files:
            img_char = img.split(".")[0]
            img_sum = sum(imread(os.path.join(img_path,img)))
#            print (os.path.join(img_path,img))
            img_stats.append(img_sum)

#            print img_sum, img_char
            chr_density_sort.append(int(img_char))

    chr_density_sort = array(chr_density_sort)
    chr_density_sort = chr_density_sort[argsort(img_stats)]

    # print chr_density_sort, len(chr_density_sort)
    print "Visual density sort obtained."
    
    return chr_density_sort

def img2ascii(filename, map_array=None):
    a = imread(filename)

    print "Converting ..."
    # useful only when reading .jpg files.
    # PIL is used for jpegs; converting PIL image to numpy array messes up. 
    # a = a[::-1, :] 

    # convert image to grayscale.
    if len(a.shape) > 2:
        a = 0.21 * a[:,:,0] + 0.71 * a[:,:,1] + 0.07 * a[:,:,2]
    a_r, a_c = a.shape[:2]
    a_max = float(a.max())

    blk_siz = 1 #size of block

    if map_array == None:
        # just linearly map gray level to characters.
        # giving lowest gray level to space character.
        out_file = open(filename + 'lin' + str(blk_siz) + '.txt', 'w')
        print "File %s opened" %out_file.name
        for i in range(0, a_r, blk_siz*2):
            for j in range(0, a_c, blk_siz):
                b = a[i:i+2*blk_siz, j:j+blk_siz]
                b_char = chr(32+int((1-average(b))*94))
                out_file.write(b_char)
            out_file.write("\n")
        out_file.close()
    else:
        # map based on visual density of characters.
        out_file = open(filename + 'arr' + str(blk_siz) + '.txt', 'w')
        print "File %s opened" %out_file.name
        for i in range(0, a_r, blk_siz*2):
            for j in range(0, a_c, blk_siz):
                b = a[i:i+2*blk_siz, j:j+blk_siz]
                b_mean = int(average(b)/a_max*(len(map_array)-1))
                b_char = chr(map_array[b_mean])
                out_file.write(b_char)
            out_file.write("\n")
        out_file.close()
        
    print "%s Converted! \nWritten to %s" %(filename, out_file.name)

if __name__=="__main__":
    chr_order = get_density_stats()
    img2ascii('433959-gray.png', chr_order)


# References
# http://code.activestate.com/recipes/483756/


# def get_symmetry_stats(dirname="sample"):
#     """Gets ordering of characters based on vertical & horizontal symmetry.
#     NOTE: Make sure the images have just 1x1 array of each character. Else, the
#     results are utterly meaningless. 
#     """
#     img_stats = []
#     tree = os.walk(dirname)
    
#     for subfol in tree:
#         img_path = subfol[0]
#         img_files = subfol[2]
#         for img_f in img_files:
#             img_char = img_f.split(".")[0]
#             img = imread(os.path.join(img_path,img_f))
#             img_r, img_c = img.shape[:2]
#             if img_r*img_c>200:
#                 print get_symmetry_stats.__doc__
#             # vertical and horizontal symmetry score calculation
#             v_sym_mat = img[:, :img_c/2] - img[:, :(img_c-1)/2:-1]
#             v_sym_score = sum(abs(v_sym_mat))
#             h_sym_mat = img[:img_r/2] - img[:(img_r-1)/2:-1]
#             h_sym_score = sum(abs(h_sym_mat))
# #            print chr(int(img_char)), v_sym_score, h_sym_score, v_sym_score*h_sym_score, v_sym_score + 5*h_sym_score
#             chr_symmetry_sort = []
# #            img_stats.append(str(int(img_sum*100)) + " " + img_char)
# #    symmetry_density_sort = [int(each.split()[1]) for each in sorted(img_stats)]
#     # print chr_density_sort, len(chr_density_sort)
#     return chr_symmetry_sort
    
