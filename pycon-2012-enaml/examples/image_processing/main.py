#------------------------------------------------------------------------------
#  Copyright (c) 2011, Enthought, Inc.
#  All rights reserved.
#------------------------------------------------------------------------------
from processing_model import ProcessorModel


def main():
    import enaml
    with enaml.imports():
        from processing_view import Main
    window = Main(model=ProcessorModel())
    window.show()


if __name__ == "__main__":
    main()

