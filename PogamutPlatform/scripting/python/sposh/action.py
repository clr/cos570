"""Implementation of an Action.
"""

# POSH modules
from element import CopiableElement

class Action(CopiableElement):
    """An action as a thin wrapper around a behaviour's action method.
    """
    def __init__(self, agent, action_name):
        """Picks the given action from the given agent.

        The method uses the agent's behaviour dictionary to get the
        action method.
        
        The log domain is set to "[AgentName].Action.[action_name]".

        The action name is set to "[BehaviourName].[action_name]".
        
        @param agent: The agent that can perform the action.
        @type agent: L{SPOSH.Agent}
        @param action_name: The name of the action
        @type action_name: string
        """
        CopiableElement.__init__(self, agent, "Action.%s" % action_name)
        beh_dict = agent.getBehaviourDict()
        self._action = beh_dict.getAction(action_name)
        behaviour = beh_dict.getActionBehaviour(action_name)
        self._name = "%s.%s" % (behaviour.getName(), action_name)
        self.debug("Created")
    
    def fire(self):
        """Performs the action and returns if it was successful.
        
        @return: 1 if the action was successful, and 0 otherwise.
        @rtype: boolean
        """
        self.debug("Firing")
        if self._action():
            return 1
        else:
            return 0

    def copy(self):
        """Returns itsself.

        This method does NOT return a copy of the action as the action
        does not have an internal state and therefore doesn't need to
        be copied.
        """
        return self
