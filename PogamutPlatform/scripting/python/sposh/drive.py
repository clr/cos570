"""Implementation of DriveCollection, DrivePriorityElement and DriveElement.

A L{SPOSH.DriveCollection} contains several L{SPOSH.DrivePriorityElement}s
that contains several L{SPOSH.DriveElement}s. Upon firing a drive
collection, either the goal is satisfied, or either of the drive
priority elements needs to be fired successfully. Otherwise, the
drive fails. The drive priority elements are tested in order or
their priority. A drive priority element fires successfully if one
of its drive elements is ready and can be fired.
"""

# POSH modules
from element import Element, ElementCollection, FireResult
from action import Action


class DriveCollection(ElementCollection):
    """A drive collection, containing drive priority elements.
    """
    def __init__(self, agent, collection_name, priority_elements, goal):
        """Initialises the drive collection.
        
        The log domain is set to [Agent].DC.[collection_name]

        If no goal is given (goal = None), then it can never be satisfied.
        
        @param agent: The collection's agent.
        @type agent: L{SPOSH.Agent}
        @param collection_name: The name of the drive collection.
        @type collection_name: string
        @param priority_elements: The drive elements in order of their
            priority, starting with the highest priority.
        @type priority_elements: sequence of L{SPOSH.DrivePriorityElement}
        @param goal: The goal of the drive collection.
        @type goal: L{SPOSH.Trigger} or None
        """
        ElementCollection.__init__(self, agent, "DC.%s" % collection_name)
        self._name = collection_name
        self._elements = priority_elements
        self._goal = goal
        self.debug("Created")
    
    def reset(self):
        """Resets all the priority elements of the drive collection.
        """
        self.debug("Reset")
        for element in self._elements:
            element.reset()
    
    def fire(self):
        """Fires the drive collection.
        
        This method first checks if the goal (if not None) is met. If
        that is the case, then FireResult(0, self) is
        returned. Otherwise it goes through the list of priority
        elements until the first one was fired successfully (returning
        something else than None). In that case, FireResult(1,
        None) is returned. If none of the priority elements were
        successful, FireResult(0, None) is returned, indicating a
        failing of the drive collection.
        
        To Summaries:
            - FireResult(1, None): drive element fired
            - FireResult(0, self): goal reached
            - FireResult(0, None): drive failed
        
        @return: The result of firing the drive.
        @rtype: L{SPOSH.FireResult}
        """
        self.debug("Fired")
        # check if goal reached
        if self._goal and self._goal.fire():
            self.debug("Goal Satisfied")
            return FireResult(0, self)
        # fire elements
        for element in self._elements:
            # a priority element returns None if it wasn't
            # successfully fired
            if element.fire() != None:
                return FireResult(1, None)
        # drive failed (no element fired)
        self.debug("Failed")
        return FireResult(0, None)
    
    def copy(self):
        """Is never supposed to be called and raises an error.
        
        @raise NotImplementedError: always
        """
        raise NotImplementedError, "DriveCollection.copy() is never supposed to be called"


class DrivePriorityElement(ElementCollection):
    """A drive priority element, containing drive elements.
    """
    def __init__(self, agent, drive_name, elements):
        """Initialises the drive priority element.
        
        The log domain is set to [AgentName].DP.[drive_name]
        
        @param agent: The element's agent.
        @type agent: L{SPOSH.Agent}
        @param drive_name: The name of the associated drive.
        @type drive_name: string
        @param elements: The drive elements of the priority element.
        @type elements: sequence of L{SPOSH.DriveElement}
        """
        ElementCollection.__init__(self, agent, "DP.%s" % drive_name)
        self._name = drive_name
        self._elements = elements
        self._timer = agent.getTimer()
        self.debug("Created")
    
    def reset(self):
        """Resets all drive elements in the priority element.
        """
        self.debug("Reset")
        for element in self._elements:
            element.reset()
    
    def fire(self):
        """Fires the drive prority element.
        
        This method fires the first ready drive element in its
        list and returns FireResult(0, None). If no
        drive element was ready, then None is returned.
        
        @return: The result of firing the element.
        @rtype: L{SPOSH.FireResult} or None
        """
        self.debug("Fired")
        timestamp = self._timer.time()
        for element in self._elements:
            if element.isReady(timestamp):
                element.fire()
                return FireResult(0, None)
        return None

    def copy(self):
        """Is never supposed to be called and raises an error.
        
        @raise NotImplementedError: always
        """
        raise NotImplementedError, "DrivePriorityElement.copy() is never supposed to be called"


class DriveElement(Element):
    """A drive element.
    """
    def __init__(self, agent, element_name, trigger, root, max_freq):
        """Initialises the drive element.
        
        The log domain is set to [AgentName].DE.[element_name]
        
        @param agent: The element's agent.
        @type agent: L{SPOSH.Agent}
        @param element_name: The name of the drive element.
        @type element_name: string
        @param trigger: The trigger of the element.
        @type trigger: L{SPOSH.Trigger}
        @param root: The element's root element.
        @type root: L{SPOSH.Action}, L{SPOSH.Competence} or
            L{SPOSH.ActionPattern}
        @param max_freq: The maximum frequency at which is element is
            fired. The frequency is given in milliseconds between
            invocation. A negative number disables this feature.
        @type max_freq: long
        """
        Element.__init__(self, agent, "DE.%s" % element_name)
        self._name = element_name
        self._trigger = trigger
        self._root, self._element = root, root
        self._max_freq = max_freq
        # the timestamp when it was last fired
        self._last_fired = -100000l
        self.debug("Created")
    
    def reset(self):
        """Resets the drive element to its root element,
        and resets the firing frequency.
        """
        self.debug("Reset")
        self._element = self._root
        self._last_fired = -100000l
    
    def isReady(self, timestamp):
        """Returns if the element is ready to be fired.
        
        The element is ready to be fired if its trigger is
        satisfied and if the time since the last firing is
        larger than the one given by C{maxFreq}. The time of the
        last firing is determined by the timestamp given
        to L{isReady} when it was called the last time and returned
        1. This implies that the element has to be fired
        every time when this method returns 1.
        
        @param timestamp: The current timestamp in milliseconds
        @type timestamp: long.
        """
        if self._trigger.fire():
            if self._max_freq < 0 or \
               (timestamp - self._last_fired) >= self._max_freq:
                self._last_fired = timestamp
                return 1
            else:
                self.debug("Max. firing frequency exceeded")
        return 0 
    
    def fire(self):
        """Fires the drive element.
        
        This method fires the current drive element and always
        returns None. It uses the slip-stack architecture to determine
        the element to fire in the next step.
        
        @return: None.
        @rtype: None
        """
        self.debug("Fired")
        element = self._element
        # if our element is an action, we just fire it and do
        # nothing afterwards. That's because we can only have an action
        # as an element, if it is the drive element's root element.
        # Hence, we didn't descend in the plan tree and can keep
        # the same element.
        # type() doesn't return the right thing, we need to use __class__
        if element.__class__ == Action:
            element.fire()
            self._element = self._root
            return None
        # the element is a competence or an action pattern
        result = element.fire()
        if result.continueExecution():
            # if we have a new next element, store it as the next
            # element to execute
            nextElement = result.nextElement()
            if nextElement:
                self._element = nextElement
        else:
            # we were told not to continue the execution -> back to root
            # We must not call reset() here, as that would also reset
            # the firing frequency of the element.
            self._element = self._root
        return None

    def copy(self):
        """Is never supposed to be called and raises an error.
        
        @raise NotImplementedError: always
        """
        raise NotImplementedError, "DriveElement.copy() is never supposed to be called"
