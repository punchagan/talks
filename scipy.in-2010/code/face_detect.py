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
    cascade = cv.Load('../data/haarcascade_frontalface_alt.xml')
    faces = cv.HaarDetectObjects(grayscale, cascade, storage, 1.2, 2, cv.CV_HAAR_DO_CANNY_PRUNING, (50, 50))
 
    if faces:
        print 'face detected!'
        for i in faces:
            x, y, width, height = i[0]
            cv.Rectangle(image, (x, y), (x + width, y + height),
                         cv.RGB(0, 255, 0), 3, 8, 0)
 
if __name__ == "__main__":
    # print "OpenCV version: %s (%d, %d, %d)" % (cv.VERSION,
    #                                            cv.MAJOR_VERSION,
    #                                            cv.MINOR_VERSION,
    #                                            cv.SUBMINOR_VERSION)
 
    # print "Press ESC to exit ..."
 
    # create windows
    cv.NamedWindow('Camera', cv.CV_WINDOW_AUTOSIZE)
 
    # create capture device
    device = 0 # assume we want first device
    capture = cv.CreateCameraCapture(device)
    cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
    cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
 
    # check if capture device is OK
    if not capture:
        print "Error opening capture device"
        sys.exit(1)
 
    while 1:
        # do forever
 
        # capture the current frame
        frame = cv.QueryFrame(capture)
        if frame is None:
            break
 
        # mirror
        cv.Flip(frame, None, 1)
 
        # face detection
        detect(frame)
 
        # display webcam image
        cv.ShowImage('Camera', frame)
 
        # handle events
        k = cv.WaitKey(10)
 
        if k == 0x1b: # ESC
            print 'ESC pressed. Exiting ...'
            break
