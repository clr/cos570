"""Implementation of the Behaviour base class.
"""

# POSH modules
from logbase import LogBase

class Behaviour(LogBase):
    """Behaviour base class.
    """
    def __init__(self, log):
        """Initialises behaviour.
        
        Here is the place to implement your acts and senses
        
        The log domain of a behaviour is set to class name.
              
        """
        LogBase.__init__(self, log, self.__class__.__name__)
    
    def getName(self):
        """Returns the name of the behaviour.
        
        The name of a behaviour is the same as the name of
        the class that implements it.
        
        @return: Name of the behaviour.
        @rtype: string
        """
        return self.__class__.__name__
    
    def getActions(self):
        """Returns a list of available actions (strings).
        
        @return: List of behaviour actions.
        @rtype: sequence of strings
        """
        return self._actions
    
    def getSenses(self):
        """Returns a list of available senses (strings)
        
        @return: List of behaviour senses.
        @rtype: sequence of strings
        """
        return self._senses

    def registerInspectors(self, inspectors):
        """Sets the methods to call to get/modify the state of the behaviour.
        
        Inspectors can be used to observe and modify the state of a behaviour.
        Each inspector has to be given by a string that gives the name of
        the behaviour method to be called. The method has to be named 'get'
        followed by the name of the inspector, and has to take 0 arguments
        (other than C{self}, naturally). If you want to allow changing
        the behaviour state, you have to provide another method taking a single
        string as an argument (besides the obligatory C{self}), and being
        called 'set' followed by the name of the inspector.
        
        Given, for example, that we want to control the energy level of a
        behaviour. Then, if the string 'Energy' is given to the
        inspector, it looks for the method 'getEnergy' to get the energy level.
        If another method 'setEnergy' is provided, taking a string as an
        argument, we can also modify the energy level of the behaviour.
        
        @param inspectors: A list of inspector methods, as described above.
        @type inspectors: sequence of strings.
        @raise AttributeError: If the inspector method cannot be found.
        """
        self._inspectors = []
        accessor, mutator = None, None
        for inspector in inspectors:
            accessor = getattr(self, "get%s" % inspector, None)
            mutator = getattr(self, "set%s" % inspector, None)
            if not accessor:
                raise AttributeError, "Could not find inspector method %s " \
                    "in behaviour %s" % (inspector, self._name)
            self._inspectors.append((inspector, accessor, mutator))

    def getInspectors(self):
        """Returns the list of currently registered inspectors.
        
        The list of inspectors contains elements of the form
        C{(name, accessor, mutator)}, where C{name} is the name of the
        inspector, C{accessor} is the accessor method (taking no arguments),
        and C{mutator} is the mutator method (taking a single string as its
        only argument), or C{None} if no mutator is provided.
        
        @return: List of inspectors.
        @rtype: Sequence of (string, method, method|None)
        """
        return self._inspectors
