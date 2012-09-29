#------------------------------------------------------------------------------
#  Copyright (c) 2012, Enthought, Inc.
#  All rights reserved.
#------------------------------------------------------------------------------
""" The entry point launcher for the Enaml Preview application.

"""
import os
import enaml

from preview_config import ViewConfig


if __name__ == '__main__':
    path = os.path.join(os.path.expanduser('~'), 'Desktop')
    if not os.path.exists(path):
        path = '.'

    config = ViewConfig(search_dir=path)
    
    with enaml.imports():
        from viewer import PreviewMain
    
    view = PreviewMain(view_config=config, initial_size=(640, 480))
    view.show()

