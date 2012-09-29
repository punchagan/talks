#------------------------------------------------------------------------------
#  Copyright (c) 2012, Enthought, Inc.
#  All rights reserved.
#------------------------------------------------------------------------------
from traits.api import (
    HasTraits, Bool, Range, Enum, on_trait_change, Property, Str, List, Int,
    cached_property, Instance
)

from enaml.styling.color import Color


# An enum defining a image extension.
ImageFileExt = Enum(
    'bmp', 'png', 'jpg', 'jpeg', 'gif', 'pbm', 
    'pgm', 'ppm', 'tiff', 'xbm', 'xpm',
)


class ViewConfig(HasTraits):
    """ A simple state object to share amongst the various ui widgets. 
    This is not strictly required when developing an Enaml application, 
    but as the view complexity grows, it makes the code more unified and
    manageable. It's also easier to see the view logic in centralized
    place.

    """
    #: The types of images for which to search.
    search_image_exts = List(ImageFileExt, value=['png', 'jpg', 'jpeg'])

    #: The regex pattern to use when searching for images.
    image_file_pattern = Property(Str, depends_on='search_image_exts')

    #: The directory currently being searched.
    search_dir = Str('.')
    
    #: The minimum allowed thumbnail size.
    min_thumb_size = Int(16)

    #: The maximum allowed thumbnail size.
    max_thumb_size = Int(256)

    #: The size of the thumbnails in the ui.
    thumb_size = Range('min_thumb_size', 'max_thumb_size', value=150)

    #: Select which browsing widget should be visible
    visible_browser_widget = Enum('textual', 'thumbnails')

    #: The layout mode to use for the thumbnails view.
    thumb_layout = Enum('vertical', 'horizontal', 'grid')
 
    #: The location of the dock pane
    dock_area = Enum('left', 'right', 'top', 'bottom', value='left')

    #: Whether or not the dock pane is floating
    floating_dock = Bool(False)

    #: Whether or not to recrusively load the thumbnails
    recursive_load = Bool(True)

    #: The background color of the image viewing widget.
    viewer_bgcolor = Instance(Color, (146, 146, 146))

    #: The background color of the browser widgets.
    browser_bgcolor = Instance(Color, (235, 239, 246))

    @cached_property
    def _get_image_file_pattern(self):
        """ Creates a search regex for the requested image types.

        """
        return r'.*?\.(%s)$' % '|'.join(self.search_image_exts)

    @on_trait_change('dock_area, floating_dock')
    def _update_thumb_layout(self):
        """ Updates the thumbnail layout mode based on the position
        of the dock pane.

        """
        if self.floating_dock:
            self.thumb_layout = 'grid'
        elif self.dock_area in ('left', 'right'):
            self.thumb_layout = 'vertical'
        else:
            self.thumb_layout = 'horizontal'

