"""A module to build plans and create plan objects

This module is used by the lap-file parser to create plan objects.
"""

__revision__ = "0.1"

# Python modules
import types

# POSH modules
from sense import Sense, Trigger
from action import Action
from action_pattern import ActionPattern
from competence import Competence, CompetencePriorityElement, CompetenceElement
from drive import DriveCollection, DrivePriorityElement, DriveElement
from timer import SteppedTimer, RealTimeTimer


class PlanBuilder:
    """A class to construct plans and build plan objects.
    """
    def __init__(self):
        """Initialises the plan builder.
        """
        # store drive collections, action pattern, competences, docstring
        self._docstring = None
        self._drivecollection = None
        self._actionpatterns = {}
        self._competences = {}

    def setDocstring(self, docstring):
        """Sets the docstring of the plan.

        This string is not used for plan generation.
        Calling this method replaces an alreay set docstring.

        @param docstring: The docstring as list of strings.
        @type docstring: [string, string, string]
        """
        self._docstring = docstring

    def setDriveCollection(self, drivecollection):
        """Sets the drive collection of the plan.

        The drive collection has to be given in the following format:
        (type, name, goal, priorities)
        where:
          - type: string, any of DC, RDC, SDC, SRDC
          - name: string, name of drive collection
          - goal: a goal list as described below
          _ priorities: a list of comptence priorities as described below

        A goal is a sequence of senses and sense-acts, where sense-acts
        are given by their name as a string, and senses are given by a
        triple of the form (name, value, predicate), where all elements
        are given as string. Valid values for predicates are discussed in
        the documentation of L{SPOSH.Sense}. If there is no goal, then
        None can be given instead of the goal, which is treated equivalently
        to an empty list.

        A list of priorities is a sequence of collections of drive elements,
        like [[drive element 1a, drive element 1b], [drive element 2a], ...],
        Each drive element is a quadruple given by (name, trigger, triggerable,
        frequency), where the name is a string, the trigger is - just as a
        goal - a collection of senses and sense-acts, a triggerable is given
        by its name, and the frequency is a long integer. If there is no
        trigger (i.e. the element is always triggered), then None can be
        given as a trigger.

        @param drivecollection: A structure describing the drive collection.
        @type drivecollection: described above
        """
        self._drivecollection = drivecollection

    def addActionPattern(self, actionpattern):
        """Adds the given action pattern to the plan.

        The given action pattern has to be a triple of the form (name,
        time, action squence), where the name is given by a string,
        the time is given as a long integer (or None, if no time is
        specified), and the action sequence is given as a sequence of
        strings that give the action / sense-act / competence names, or
        triples of the form (name, value, predicate), where all elements
        are given as string and the triple describes a sense. Valid values
        for predicates are discussed in the documentation of L{SPOSH.Sense}.

        @param actionpattern: A structure describing the action pattern.
        @type actionpattern: described above
        @raise NameError: If there is already an action pattern or competence
            with the given name in the plan.
        """
        name = actionpattern[0]
        if self._actionpatterns.has_key(name):
            raise NameError, "More than one action pattern named '%s'" % name
        elif self._competences.has_key(name):
            raise NameError, "Action pattern name '%s' clashes with " \
                "competence of same name" % name
        self._actionpatterns[name] = actionpattern

    def addCompetence(self, competence):
        """Adds the given competence to the plan.

        The competence structure is similar to a drive collection and
        is described by the quatruple (name, time, goal, priorities).
        The name is given as string, and the time as a long integer (or None
        if no time is specified).
        
        A goal is a sequence of senses and sense-acts, where sense-acts
        are given by their name as a string, and senses are given by a
        triple of the form (name, value, predicate), where all elements
        are given as string. Valid values for predicates are discussed in
        the documentation of L{SPOSH.Sense}. If either vqlue or predicate are
        not specified, then None can be given instead of the string.
        If there is no goal, then None can be given instead of the goal,
        which is treated equivalently to an empty list.

        A list of priorities is a sequence of collections of competence
        elements, like [[competence element 1a, competence element 1b],
        [competence element 2a], ...]. Each competence element is a quadruple
        given by (name, trigger, triggerable, retries), where the name is
        a string, the trigger is - just as a goal - a collection of senses
        and sense-acts, a triggerable is given by its name, and the number of
        retries is is a long integer. If there is no trigger (i.e. the element
        is always triggered), then None can be  given as a trigger.

        @param competence: A structure describing a competence.
        @type competence: described above
        @raise NameError: If there is already an action pattern or competence
            with the same name in the plan.
        """
        name = competence[0]
        if self._competences.has_key(name):
            raise NameError, "More than one competence named '%s'" % name
        elif self._actionpatterns.has_key(name):
            raise NameError, "Competence name '%s' clashes with " \
                "action pattern of same name" % name        
        self._competences[name] = competence

    def build(self, agent):
        """Builds the plan and returns the drive collection.

        This method operates in several stages:

          1. It is checked if none of the action pattern or competence
             names are already taken by an action or sense/sense-act
             in the behaviour library. If a conflict
             is found, then NameError is raised.

          2. All competence / action pattern objects are created, together
             with goals and triggers, but their elements are left empty.

          3. The elements of competences and action pattern are created.

          4. The drive collection is built and returned.

        @param agent: The agent that uses the plan.
        @type agent: L{SPOSH.Agent}
        @return: The drive collection as the root of the plan.
        @rtype: L{SPOSH.DriveCollection}
        @raise NameError: If clashes in naming of actions / action pattern /
            competences were found, or if a sense / action / sense-act was
            not found.
        """
        self._checkNameClashes(agent)
        competences = self._buildCompetenceStubs(agent)
        actionpatterns = self._buildActionPatternStubs(agent)
        self._buildCompetences(agent, competences, actionpatterns)
        self._buildActionPatterns(agent, competences, actionpatterns)
        return self._buildDriveCollection(agent, competences, actionpatterns)

    def _checkNameClashes(self, agent):
        """Checks for naming clashes in actions / senses / action pattern /
        competences.

        @param agent: The agent to check clashes for (as the agent provides
            the behaviour dictionary).
        @type agent: L{SPOSH.Agent}
        @raises NameError: If a clash is detected.
        """
        behDict = agent.getBehaviourDict()
        actions, senses = behDict.getActionNames(), behDict.getSenseNames()
        for competence in self._competences.keys():
            if competence in actions:
                raise NameError, "Competence name '%s' clashes with " \
                    "action of same name" % competence
            if competence in senses:
                raise NameError, "Competence name '%s' clashes with " \
                    "sense of same name" % competence
        for actionpattern in self._actionpatterns.keys():
            if actionpattern in actions:
                raise NameError, "Action pattern name '%s' clashes with " \
                    "action of same name" % actionpattern
            if actionpattern in senses:
                raise NameError, "Action pattern name '%s' clashes with " \
                     "sense of same name" % actionpattern
            
    def _buildDriveCollection(self, agent, competences, actionpatterns):
        """Builds the drive collection and returns it.

        This method builds the drive collection, of which the structure has
        been set by L{setDriveCollection}. Additionally, its
        assigns the agent a timer, as specified by the drive collection
        (i.e. a stepped timer, in the case of an SDC drive, and a
        real-time timer in the case of an SRDC drive). If the timer is
        a real-time timer, then it is initialised with a loop frequency of
        50Hz.

        Only drives of type 'SDC' and 'SRDC' are accepted. In any other case
        a TypeError is raised.

        @param agent: The agent that the drive collection is built for.
        @type agent: L{SPOSH.Agent}
        @param competences: A competence object dictionary.
        @type competences: Dictionary, string -> L{SPOSH.Competence}
        @param actionpatterns: An action pattern dictionary.
        @type actionpatterns: Dictionary, string -> L{SPOSH.ActionPattern}
        @return: The drive collection.
        @rtype: L{SPOSH.DriveCollection}
        @raise TypeError: For drives of types other than SDC or SRDC.
        """
        dctype, dcname = self._drivecollection[0], self._drivecollection[1]
        # create the agent timer
        if dctype == 'SDC':
            agent.setTimer(SteppedTimer())
        elif dctype == 'SRDC':
            agent.setTimer(RealTimeTimer(long(1000.0 / 50.0)))
        elif dctype == 'DC':
            agent.setTimer(SteppedTimer())
            print "Warning: using StrictPOSH with POSH Drive Collection."
        elif dctype == 'RDC':
            agent.setTimer(RealTimeTimer(long(1000.0 / 50.0)))
            print "Warning: using StrictPOSH with POSH Real time Drive Collection."
        else:
            raise TypeError, "Drive collection of type '%s' not " \
                "supported (only supporting SDC and SRDC, DC and RDC)." % dctype
        goal = self._buildGoal(agent, self._drivecollection[2])
        priority_elements = []
        for priority_element in self._drivecollection[3]:
            element_list = []
            for element in priority_element:
                element_list.append(
                    self._buildDriveElement(element, agent,
                                            competences, actionpatterns))
            priority_elements.append(
                DrivePriorityElement(agent, dcname, element_list))
        return DriveCollection(agent, dcname, priority_elements, goal)

    def _buildDriveElement(self, element, agent,
                           competences, actionpatterns):
        """Builds a drive element according to the given structure.

        The structure of a drive element is described in
        L{setDriveCollection}.

        @param element: The structure of the drive element to build.
        @type element: Described in L{setDriveCollection}
        @param agent: The agent to build the drive collection for.
        @type agent: L{SPOSH.Agent}
        @param competences: A competences object dictionary.
        @type competences: Dictionary, string -> L{SPOSH.Competence}
        @param actionpatterns: An action pattern object dictionary.
        @type actionpatterns: Dictionary, string -> L{SPOSH.ActionPattern}
        @return: A drive element.
        @rtype: L{SPOSH.DriveElement}
        """
        trigger = self._buildTrigger(agent, element[1])
        triggerable = self._getTriggerable(agent, element[2],
                                           competences, actionpatterns)
        return DriveElement(agent, element[0], trigger, triggerable,
                            element[3])
        

    def _buildCompetenceStubs(self, agent):
        """Builds stub objects for the plan competences.

        The stub competences are competences without elements.

        @param agent: The agent to build the competences for.
        @type agent: L{SPOSH.Agent}
        @return: A dictionary with competence stubs.
        @rtype: Dictionary, string -> L{SPOSH.Competence}
        """
        stub_dict = {}
        for competence in self._competences.values():
            name = competence[0]
            goal = self._buildGoal(agent, competence[2])
            # we're just ignoring the time qs we use the simple slip-stack
            stub = Competence(agent, name, [], goal)
            stub_dict[name] = stub
        return stub_dict

    def _buildActionPatternStubs(self, agent):
        """Build stub objects fopr the plan action pattern.

        The stub action pattern are action pattern without actions.

        @param agent: The action to build the action pattern for.
        @type agent: L{SPOSH.Agent}
        @return: A dictionary with action pattern stubs.
        @rtype: Dictionary, string -> L{SPOSH.ActionPattern}
        """
        stub_dict = {}
        for pattern in self._actionpatterns.values():
            name = pattern[0]
            # we're just ignoring the time, as we use the simple slip-stack
            stub = ActionPattern(agent, name, [])
            stub_dict[name] = stub
        return stub_dict

    def _buildCompetences(self, agent, competences, actionpatterns):
        """Completes the competences based on the given competence stubs.

        This method modifies the given competence stubs and creates
        all its elements. These elements can either be other
        competences, action pattern, or actions. In case of actions,
        the corresponding L{SPOSH.Action} objects are created. The
        actions have to be available in the agent's behaviour dictionary.

        @param agent: The agent to build the competences for.
        @type agent: L{SPOSH.Agent}
        @param competences: The competence stubs, as returned by
            L{_buildCompetenceStubs}.
        @type competences: Dictionary, string -> L{SPOSH.Competence}
        @param actionpatterns: The action pattern stubs, as returned by
            L{_buildActionPatternStubs}
        @type actionpatterns: Dictionary, string -> L{SPOSH.ActionPattern}
        """
        for competence in self._competences.keys():
            # start with priority elements
            priority_elements = []
            for priority_element in self._competences[competence][3]:
                element_list = []
                for element in priority_element:
                    element_list.append(
                        self._buildCompetenceElement(element, agent,
                                                     competences,
                                                     actionpatterns))
                priority_elements.append(
                    CompetencePriorityElement(agent, competence, element_list))
            competences[competence].setElements(priority_elements)
            
    def _buildActionPatterns(self, agent, competences, actionpatterns):
        """Completes the action pattern based on the given
        action pattern stubs.

        This method modifies the given action pattern stubst and
        creates all its elements. The elements can either be other
        competences, actions or senses, where competences are only
        allowed as the last elements in action patterns. In case of
        actions / senses, the corresponding L{SPOSH.Action} /
        L{SPOSH.Sense} objects are created. The actions / senses have
        to be available in the agent's behaviour dictionary.

        @param agent: The agent to build the competences for.
        @type agent: L{SPOSH.Agent}
        @param competences: The competence stubs, as returned by
            L{_buildCompetenceStubs}.
        @type competences: Dictionary, string -> L{SPOSH.Competence}
        @param actionpatterns: The action pattern stubs, as returned by
            L{_buildActionPatternStubs}
        @type actionpatterns: Dictionary, string -> L{SPOSH.ActionPattern}
        """
        senses = agent.getBehaviourDict().getSenseNames()
        for actionpattern in self._actionpatterns.keys():
            # create the elements of the action pattern
            element_list = []
            element_names = self._actionpatterns[actionpattern][2]
            # build all but the last elements
            for element in element_names[:-1]:
                if element in senses:
                    # its in senses and a string -> sense-act
                    element_list.append(self._buildSenseAct(agent, element))
                elif not type(element) == types.StringType:
                    # its not a string -> sense
                    element_list.append(self._buildSense(agent, element))
                else:
                    # neither of above -> action
                    element_list.append(self._getTriggerable(agent, element))
            # for the last element also allow competences
            element = element_names[-1]
            if element in senses:
                element_list.append(self._buildSenseAct(agent, element))
            elif not type(element) == types.StringType:
                element_list.append(self._buildSense(agent, element))
            else:
                element_list.append(self._getTriggerable(agent, element,
                                                         competences))
            actionpatterns[actionpattern].setElements(element_list)

    def _buildCompetenceElement(self, element, agent,
                                competences, actionpatterns):
        """Builds a competence element from the given structure.

        The competence element has to be given as a the quadruple (name,
        trigger, triggerable, retries), where the name is a string, the
        trigger is described in L{addCompetence}, the triggerable is the
        name of an action, competence or action pattern, and retries is the
        number of retries and given as long.

        If the triggerable cannot be found, then a NameError is raised.

        @param element: The structure od the competence element.
        @type element: described above
        @param agent: The agent that the competence element is built for.
        @type agent: L{SPOSH.Agent}
        @param competences: A competence object dictionary.
        @type competences: Dictionary, string -> L{SPOSH.Competence}
        @param actionpatterns: An action pattern object dictionary.
        @type actionpatterns: Dictionary, string -> L{SPOSH.ActionPattern}
        @return: The competence element described by the given structure.
        @rtype: L{SPOSH.CompetenceElement}
        @raise NameError: If the triggerable cannot be found.
        """
        trigger = self._buildTrigger(agent, element[1])
        triggerable = self._getTriggerable(agent, element[2],
                                           competences, actionpatterns)
        return CompetenceElement(agent, element[0], trigger, triggerable,
                                 element[3])

    def _buildGoal(self, agent, goal):
        """Builds the goal from the given structure.

        The given goal structure is a sequence of sense-acts given by
        simple strings, and senses given by the triple (name, value,
        predicate), where all of the elements of the triple are string.
        Optionally, the value and predicate can be None.

        If the goal list is empty, or None is given for the goal,
        then None is returned.

        @param agent: The agent to build the goal for.
        @type agent: L{SPOSH.Agent}
        @param goal: The sequence of senses and sense-acts.
        @type goal: described above
        @return: The goal object.
        @rtype: L{SPOSH.Trigger} or None.
        """
        if not goal:
            return None
        sense_list = []
        for sense in goal:
            if type(sense) == types.StringType:
                sense_list.append(self._buildSenseAct(agent, sense))
            else:
                sense_list.append(self._buildSense(agent, sense))
        return Trigger(agent, sense_list)

    def _buildTrigger(self, agent, trigger):
        """Builds the trigger forn the given structure.

        The given trigger structure is a sequence of sense-acts given
        by simple strings, and senses given by the triple (name, value,
        predicate), where all of the elements of the triple are string.
        Optionally, the value and predicate can be None.

        If the trigger list is empty, or None is given for the trigger,
        then None is returned.

        @param agent: The agent to build the trigger for.
        @type agent: L{SPOSH.Agent}
        @param trigger: The sequence of senses and sense-acts.
        @type trigger: described above
        @return: The trigger object
        @rtype: L{SPOSH.Trigger}
        """
        # is the same as _buildGoal
        return self._buildGoal(agent, trigger)

    def _buildSenseAct(self, agent, sense_name):
        """Returns a sense-act object for the given name.

        @param agent: The agent to build the sense-act for.
        @type agent: L{SPOSH.Agent}
        @param sense_name: The name of the sense-act.
        @type sense_name: string
        @return: The created sense-act object
        @rtype: L{SPOSH.Sense}
        """
        return Sense(agent, sense_name)

    def _buildSense(self, agent, sense_struct):
        """Returns a sense object for the given structure.

        The structure is of the form (name, value, predicate), where
        the first is a string, and the other two elements are either
        a string or None.

        @param agent: The agent to build the sense for.
        @type agent: L{SPOSH.Agent}
        @param sense_struct: The sense structure.
        @type sense_struct: described above
        @return: The created sense object
        @rtype: L{SPOSH.Sense}
        @raise NameError: If the sense could not be found in the
            behaviour dictionary.
        """
        return Sense(agent, sense_struct[0], sense_struct[1], sense_struct[2])

    def _getTriggerable(self, agent, name,
                        competences = {}, actionpatterns = {}):
        """Returns the action / competence / actionpattern with the given name.

        This method looks for the element with the given name and
        returns it.  If the element is an action, then it creates a
        new L{SPOSH.Action} object from the agent's behaviour
        dictionary. Otherwise it just returns the competence or action
        pattern object.

        The method also checks if the the given name is both an action and a
        competence / action pattern. In that case a NameError is raised.

        @param agent: The agent that the element belongs to.
        @type agent: L{SPOSH.Agent}
        @param name: The name of the element.
        @type name: string
        @param competences: A competence object dictionary.
        @type competences: Dictionary, name -> L{SPOSH.Competence}
        @param actionpatterns: An action pattern object dictionary.
        @type actionpatterns: Dictionary, name -> L{SPOSH.ActionPattern}
        @return: The element with the given name.
        @rtype: L{SPOSH.Action}, L{SPOSH.Competence} or L{SPOSH.ActionPattern}
        @raise NameError: If actions and competences / action pattern have
            the same name.
        """
        # creating an action would raise a NameError when looking up the
        # according behaviour in the behaviour dictionary. Hence, if no
        # behaviour provides that action, we need to check competences and
        # action pattern
        try:
            element = Action(agent, name)
        except NameError:
            # action not found, try competences and action patterns
            if competences.has_key(name):
                return competences[name]
            elif actionpatterns.has_key(name):
                return actionpatterns[name]
            else:
                raise NameError, "No action / competence / action pattern " \
                      "with name '%s' found" % name
        # we get here only if the action was created successfully,
        # check now for clashes with competences / action pattern
        if (competences.has_key(name) or actionpatterns.has_key(name)):
            raise NameError, "Name of action '%s' also held by other " \
                "competence / action pattern" % name
        return element
