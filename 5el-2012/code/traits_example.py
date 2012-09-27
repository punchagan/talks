from traits.api import HasTraits, Float, Enum

class Person(HasTraits):
    age = Float(10.0)
    gender = Enum('male', 'female')

    def _age_changed(self):
        print self.age

joe = Person()

joe.configure_traits()
