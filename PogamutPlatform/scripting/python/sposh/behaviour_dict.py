"""Implementation of the behaviour dictionary.
"""

class BehaviourDict:
    """The behaviour dictionary.
    
    The behaviour dictionary is a dictionary of behaviours, its
    actions and senses. Each of the behaviours is registered
    with the dictionary. Subsequently, it allows looking up actions
    and senses by their names, and returns their behaviour and
    their actual method.
    """
    def __init__(self):
        """Initialises the behaviour dictionary.
        """
        # name -> behaviour
        self._behaviours = {}
        # name -> (method, behaviour)
        self._actions = {}
        # name -> (method, behaviour)
        self._senses = {}
    
    def registerBehaviour(self, behaviour):
        """Registers the given behaviour.
        
        Upon registering, it is checked if all action and sense
        methods are actually available in the given behaviour.
        If that is not the case, an AttributeError is thrown.
        
        If there is already an action or a sense with the same
        name registered in the behaviour dictionary, a
        NameError is thrown.
        
        The actions and senses are aquired by using the behaviour's
        L{SPOSH.Behaviour.getActions} and L{SPOSH.Behaviour.getSenses}
        methods.
        
        @param behaviour: The behaviour to register.
        @type behaviour: L{SPOSH.Behaviour}
        @raise AttributeError: If an action or a sense method could
            not be found.
        @raise NameError: If a given action or sense is already
            registered in the behaviour dictionary, or if a behaviour
            with the same name is already registered in the
            dictionary.
        """
        actions = behaviour.getActions()
        senses = behaviour.getSenses()
        # add the behaviour
        behaviourName = behaviour.getName()
        if self._behaviours.has_key(behaviourName):
            raise NameError, "Behaviour '%s' cannot be registered twice" % behaviourName
        self._behaviours[behaviourName] = behaviour
		# add the actions
        for action in actions:
            if self._actions.has_key(action):
                raise NameError, "Action '%s' registered twice: For '%s' and '%s'" % (action, self._actions[action].getName(), behaviourName)
            try:
                actionMethod = getattr(behaviour, "action_"+action)
            except AttributeError:
                try:
                    actionMethod = getattr(behaviour, action)
                except AttributeError:	
                    raise AttributeError, "Behaviour '%s' does not provide an action method named '%s'" % (behaviourName, action)
            self._actions[action] = (actionMethod, behaviour)
        # .. and the senses
        for sense in senses:
            if self._senses.has_key(sense):
                raise NameError, \
                    "Sense '%s' registered twice: For '%s' and '%s'" % \
                    (sense, self._senses[sense].getName(), behaviourName)
            try:
				senseMethod = getattr(behaviour, "sense_"+sense)
            except AttributeError:
                try:
                    senseMethod = getattr(behaviour, sense)
                except AttributeError:
                    raise AttributeError, "Behaviour '%s' does no provide a sense method named '%s'" % (behaviourName, sense)
            self._senses[sense] = (senseMethod, behaviour)
    
    def getBehaviours(self):
        """Returns a list of behaviours.
        
        @return: List of behaviours.
        @rtype: sequence of L{SPOSH.Behaviour} objects
        """
        return self._behaviours.values()

    def getBehaviour(self, behav_name):
        """Returns the behaviour object with the given name.

        @param behav_name: The name of the behaviour.
        @type behav_name: string
        @raise NameError: If no behaviour with the given name was registered.
        """
        try:
            return self._behaviours[behav_name]
        except KeyError:
            raise NameError, "Cannot find behaviour '%s'" % behav_name
    
    def getAction(self, actionName):
        """Returns an action by name.

        This method raises a NameError if no action with the given name
        was registered.
        
        @return: The action with the given name.
        @rtype: L{SPOSH.Behaviour} class method
        @raise NameError: If action wasn't registered.
        """
        try:
            return self._actions[actionName][0]
        except KeyError:
            raise NameError, "Action '%s' not provided by any behaviour" % \
                actionName

    def getActionNames(self):
        """Returns the list of available action names.

        @return: A list of action names.
        @rtype: sequence of strings
        """
        return self._actions.keys()

    def getActionBehaviour(self, actionName):
        """Returns the behaviour that provides the given action.

        @param actionName: The action that the behaviour provides
        @type actionName: string
        @return: The behaviour that provides the given action.
        @rtype: L{SPOSH.Behaviour}
        @raise NameError: If no behaviour provides that action.
        """
        try:
            return self._actions[actionName][1]
        except KeyError:
            raise NameError, "Action '%s' not provided by any behaviour" % \
                actionName

    def getSense(self, senseName):
        """Returns a sense by name.

        The method raises a NameError if no sense with the given name
        was registered.
        
        @return: The sense with the given name.
        @rtype: L{SPOSH.Behaviour} class method
        """
        try:
            return self._senses[senseName][0]
        except KeyError:
            raise NameError, "Sense '%s' not provided by any behaviour" % \
                senseName

    def getSenseNames(self):
        """Returns a list of available sense names.

        @return: A list of sense names.
        @rtype: sequence of strings
        """
        return self._senses.keys()

    def getSenseBehaviour(self, senseName):
        """Returns the behaviour that provides the given sense.

        @param senseName: The sense that the behaviour provides
        @type senseName: string
        @return: The behaviour that provides the given sense.
        @rtype: L{SPOSH.Behaviour}
        @raise NameError: If no behaviour provides that sense.
        """
        try:
            return self._senses[senseName][1]
        except KeyError:
            raise NameError, "Sense '%s' not provided by any behaviour" % \
                senseName
