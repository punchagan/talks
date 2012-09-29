#------------------------------------------------------------------------------
#  Copyright (c) 2011, Enthought, Inc.
#  All rights reserved.
#------------------------------------------------------------------------------
from traits.api import HasTraits, Str, Range, on_trait_change


class Person(HasTraits):
    """ A simple class representing a person object.

    """
    last_name = Str

    first_name = Str

    age = Range(low=0)

    @on_trait_change('age')
    def debug_print(self):
        """ Prints out a debug message whenever the person's age changes.

        """
        templ = "{first} {last} is {age} years old."
        print templ.format(first=self.first_name, 
                           last=self.last_name, 
                           age=self.age)


if __name__ == '__main__':
    import enaml
    with enaml.imports():
        from person_view import PersonView
    
    john = Person(first_name='John', last_name='Doe', age=42)
    
    view = PersonView(person=john)
    view.show()

