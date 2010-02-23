"""Implementation of an ActionPattern.
"""

# Python modules
from copy import copy

# POSH modules
from element import ElementCollection, FireResult
from action import Action
from sense import Sense


class ActionPattern(ElementCollection):
    """An Action Pattern.
    """
    def __init__(self, agent, pattern_name, elements):
        """Initialises the action pattern.
        
        The log domain is set to [Agentname].AP.[patternName]
        
        @param agent: The corresponding agent.
        @type agent: L{SPOSH.Agent}
        @param pattern_name: The name of the action pattern.
        @type pattern_name: string
        @param elements: The sequence of actions, with an optional
            competence as the final element.
        @type elements: sequence of L{SPOSH.Action}, L{SPOSH.Sense}
            and L{SPOSH.Competence}
        """
        ElementCollection.__init__(self, agent, "AP.%s" % pattern_name)
        self._name = pattern_name
        self._elements = elements
        self._element_idx = 0
        self.debug("Created")
    
    def reset(self):
        """Resets the action pattern.
        
        This method sets the action pattern to fire the
        first action of the pattern upon the next call to L{fire}.
        """
        self.debug("Reset")
        self._element_idx = 0
    
    def fire(self):
        """Fires the action pattern.
        
        This method fires the current action / sense / sense-act or
        competence of the pattern. In case of firing an action / sense
        / sense-act, the method points to the next element in the
        pattern and returns FireResult(1, None) if the current
        action / sense / sense-act was successful (i.e. evaluated to
        1) and not the last action in the sequence, in which case
        it returns FireResult(0, None) and resets the action
        pattern.
        
        If the current element is a competence, then competence is
        returned as the next element by returning
        FireResult(1, competence), and the action pattern is
        reset.
        
        @return: The result of firing the action pattern.
        @rtype: L{SPOSH.FireResult}
        """
        self.debug("Fired")
        element = self._elements[self._element_idx]
        # type() doesn't work, which is why we have to use __class__
        if element.__class__ == Action or element.__class__ == Sense:
            # check if action was successful
            if not element.fire():
                self.debug("Action/Sense '%s' failed" % element.getName())
                self._element_idx = 0
                return FireResult(0, None)
            # check if we've just fired the last action
            self._element_idx += 1
            if self._element_idx >= len(self._elements):
                self._element_idx = 0
                return FireResult(0, None)
            return FireResult(1, None)
        else:
            # we have a competence
            self._element_idx = 0
            return FireResult(1, element)
    
    def copy(self):
        """Returns a reset copy of itsself.
        
        This method returns a copy of itsself, and calls L{reset}
        on it.
        
        @return: A reset copy of itsself.
        @rtype: L{SPOSH.ActionPattern}
        """
        new_obj = copy(self)
        new_obj.reset()
        return new_obj

    def setElements(self, elements):
        """Sets the elements of an action pattern.

        Calling this method also resets the action pattern.

        @param elements: The list of elements of the action patterns.
        @type elements: sequence of L{SPOSH.Action} or L{SPOSH.Competence}
            (as last element of the sequence)
        """
        self._elements = elements
        self.reset()
