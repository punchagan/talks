import sys
import cv
 
def detect(image):
    image_size = cv.GetSize(image)
 
    # create grayscale version
    grayscale = cv.CreateImage(image_size, 8, 1)
    cv.CvtColor(image, grayscale, cv.CV_BGR2GRAY)
 
    # create storage
    storage = cv.CreateMemStorage(0)
 
    # equalize histogram
    cv.EqualizeHist(grayscale, grayscale)
 
    # detect objects
    cascade = cv.Load('haarcascade_frontalface_alt.xml')
    faces = cv.HaarDetectObjects(grayscale, cascade, storage, 1.2, 2, cv.CV_HAAR_DO_CANNY_PRUNING, (50, 50))
 
    if faces:
        print 'face detected!'
        for i in faces:
            x, y, width, height = i[0]
            cv.Rectangle(image, (x, y), (x + width, y + height),
                         cv.RGB(0, 255, 0), 3, 8, 0)
 
if __name__ == "__main__":
 
    # create windows
    cv.NamedWindow('Image', cv.CV_WINDOW_AUTOSIZE)
 
    frame = cv.LoadImage("lena.png")
 
    # check if image is available
    if not frame:
        print "Error opening image"
        sys.exit(1)
 
    # face detection
    detect(frame)
 
    # display webcam image
    cv.ShowImage('Camera', frame)
 
    # handle events
    k = cv.WaitKey(1000000)
    
