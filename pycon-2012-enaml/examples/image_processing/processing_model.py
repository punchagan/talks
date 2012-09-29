#------------------------------------------------------------------------------
#  Copyright (c) 2011, Enthought, Inc.
#  All rights reserved.
#------------------------------------------------------------------------------
import numpy as np
from scipy.misc import imread

from skimage.filter import canny
from skimage.transform import probabilistic_hough

from chaco.api import Plot, ArrayPlotData, bone
from enable.api import ColorTrait
from traits.api import (
    HasTraits, File, Array, Property, Instance, Any, Int, List, Tuple, Range,
    DelegatesTo, cached_property, on_trait_change,
)

from segments_overlay import SegmentsOverlay


class ImageProcessor(HasTraits):

    original_image = Array

    canny_sigma = Range(value=1, low=0.0)
    canny_low_threshold = Range(value=0.1, low=0.0)
    canny_high_threshold = Range(value=0.2, low=0.0)
    canny_image = Property(
        Array, depends_on=['original_image', 'canny_sigma', 
                           'canny_low_threshold', 'canny_high_threshold'],
    )

    hough_threshold = Int(10)
    hough_line_length = Int(50)
    hough_line_gap = Int(10)
    hough_segments = Property(
        List, depends_on=['canny_image', 'hough_threshold', 
                          'hough_line_length', 'hough_line_gap'],
    )

    def _original_image_default(self):
        return np.array([[0]])

    @cached_property
    def _get_canny_image(self):
        ci = canny(
            self.original_image, sigma=self.canny_sigma,
            low_threshold=self.canny_low_threshold,
            high_threshold=self.canny_high_threshold,
        )
        return ci

    @cached_property
    def _get_hough_segments(self):
        segs = probabilistic_hough(
            self.canny_image, threshold=self.hough_threshold,
            line_length=self.hough_line_length, line_gap=self.hough_line_gap,
        )
        return segs


class ProcessorModel(HasTraits):

    filename = File

    image = Instance(ImageProcessor, ())
    
    shape = Property(Tuple, depends_on=['image'])
    width = Property(Int, depends_on=['shape'])
    height = Property(Int, depends_on=['shape'])

    original_image = DelegatesTo('image')
    canny_sigma = DelegatesTo('image')
    canny_low_threshold = DelegatesTo('image')
    canny_high_threshold = DelegatesTo('image')
    canny_image = DelegatesTo('image')

    hough_threshold = DelegatesTo('image')
    hough_line_length = DelegatesTo('image')
    hough_line_gap = DelegatesTo('image')
    hough_segments = DelegatesTo('image')

    segments_overlay = Any

    original_alpha = Range(value=1.0, low=0.0, high=1.0) 

    plot_data = Instance(ArrayPlotData)
    main_plot = Instance(Plot)

    canny_color = ColorTrait('red')
    canny_alpha = Range(value=1.0, low=0.0, high=1.0)
    canny_plot_image = Property(
        Array, depends_on=['image', 'canny_image', 'canny_sigma',
                           'canny_low_threshold', 'canny_high_threshold',
                           'canny_color'],
    )

    hough_segments_alpha = Range(value=1.0, low=0.0, high=1.0) 
    hough_segments_color = ColorTrait('green')

    original_plot = Any
    canny_plot = Any

    background_color = ColorTrait('black')

    #--------------------------------------------------------------------------
    # Trait defaults
    #--------------------------------------------------------------------------
    def _plot_data_default(self):
        pd = ArrayPlotData(
            original_image=self.image.original_image,
            canny_plot_image=self.canny_plot_image,
        )
        return pd

    def _main_plot_default(self):
        p = Plot(self.plot_data, default_origin='top left', padding=0)
        self.original_plot = p.img_plot(
            'original_image', colormap=bone, alpha=self.original_alpha,
            bgcolor=self.background_color_,
        )[0]
        self.canny_plot = p.img_plot(
            'canny_plot_image', alpha=self.canny_alpha,
        )[0]
        p.x_axis = None
        p.y_axis = None
        self.segments_overlay = SegmentsOverlay(
            component=self.canny_plot, image_size=self.image.canny_image.shape,
        )
        p.overlays.append(self.segments_overlay)
        return p

    #--------------------------------------------------------------------------
    # Trait property methods
    #--------------------------------------------------------------------------
    @cached_property
    def _get_shape(self):
        shape = self.image.original_image.shape
        return shape

    @cached_property
    def _get_width(self):
        width = self.shape[1]
        return width

    @cached_property
    def _get_height(self):
        height = self.shape[0]
        return height

    @cached_property
    def _get_canny_plot_image(self):
        # self.image.canny_image is an array of bools.
        # self.canny_plot_image is a 3D array (2D image with (r,g,b,a)
        # values).  The color (0,0,0,0) (transparent) is assigned where
        # canny_image is False, and (canny_color_, 255) is assigned where
        # canny_image is True.
        ci = self.image.canny_image
        x = np.zeros(ci.shape + (4,), dtype=np.uint8)
        x[ci, :3] = [255 * c for c in self.canny_color_[:3]]
        x[ci, 3] = 255
        return x

    #--------------------------------------------------------------------------
    # Trait change handlers
    #--------------------------------------------------------------------------
    def _filename_changed(self):
        try:
            image_data = imread(self.filename, flatten=True).astype(np.float32)
            image_data /= image_data.max()
            image = ImageProcessor(original_image=image_data)
        except IOError:
            image = ImageProcessor(original_image=np.array([[0]]))
        self.image = image

        self.plot_data['original_image'] = self.image.original_image
        self.plot_data['canny_plot_image'] = self.canny_plot_image
        self.segments_overlay.image_size = self.image.canny_image.shape
        self.segments_overlay.segments = self.image.hough_segments

    @on_trait_change('canny_plot_image')
    def _canny_parameter_changed(self):
        self.plot_data['canny_plot_image'] = self.canny_plot_image

    def _original_alpha_changed(self):
        self.original_plot.alpha = self.original_alpha
        # Temporary hack...
        self.plot_data['original_image'] = self.image.original_image
        self.plot_data['canny_plot_image'] = self.canny_plot_image

    @on_trait_change('canny_alpha, canny_color')
    def _canny_display_parameters_changed(self):
        self.canny_plot.alpha = self.canny_alpha
        # Temporary hack...
        self.plot_data['original_image'] = self.image.original_image
        self.plot_data['canny_plot_image'] = self.canny_plot_image

    @on_trait_change('hough_segments_alpha, hough_segments_color')
    def _hough_display_parameters_changed(self):
        self.segments_overlay.line_color = self.hough_segments_color
        self.segments_overlay.alpha = self.hough_segments_alpha
        self.segments_overlay.request_redraw()

    def _background_color_changed(self):
        self.original_plot.bgcolor = self.background_color_
        self.original_plot.request_redraw()

    @on_trait_change('hough_segments')
    def _update_hough_segments_plot(self):
        self.segments_overlay.segments = self.image.hough_segments
        self.canny_plot.request_redraw()

