"""Implementation of a POSH Agent.
   
   The implementation here is adjusted for the Pogamut 2 initialization sequence.
   The main differences is:
       1) different approach for registering behaviours (they are not created upon Agent instantiation but
          before and added as an parametr to the agent)
       2) the SPOSH engine is not running in the thread but the iteration (Agent.followDrive) is called from within
          the Pogamut 2
       3) for logging we're using java.util.logging.Logger class which is added to the agent as an parameter and then
          it's passed to all of the plan / agent components   
          
"""

# POSH modules
from behaviour_dict import BehaviourDict
from lapparser import LAPParser
from logbase import *
from timer import *

# drive collection results
DRIVE_FOLLOWED = 0
DRIVE_WON = 1
DRIVE_LOST = -1

class Agent(LogBase):
    """A POSH Agent.
    """
    def __init__(self, behaviours, plan, log):
        """Initialises the agent with the given behaviours and plan.
        
        This method register the behaviours and uses them in
        the plan with the given name.

        @param behaviours: list or sequence of Behaviours instances
        @type behaviours: list or sequence of Behavours instances
        @param plan: Name of the plan (complete path + file + extension).
        @type plan: string
        @param log: java.util.logging.Logger instance
        @type java.logging.Logger        
        """
        # initialize the logging
        LogBase.__init__(self, log, "Agent")
               
        # if setTimer() is not called, then the first use of
        # the timer will fail. setTimer() is called when the drive
        # collection is built.
        self._timer = None
                
        # load the behaviours
        self._bdict = self._loadBehaviours(behaviours)
        
        # load the plan an create the tree
        plan_str = open(plan).read()
        plan_builder = LAPParser().parse(plan_str)
        self._dc = plan_builder.build(self)
        
    def getBehaviourDict(self):
        """Returns the agent's behaviour dictionary.

        @return: The agent's behaviour dictionary.
        @rtype: L{SPOSH.BehaviourDict}
        """
        return self._bdict
    
    def getBehaviours(self):
        """Returns the agent's behaviour objects.
        
        @return: List of behaviour objects.
        @rtype: Sequence of L{SPOSH.Behaviour}
        """
        return self._bdict.getBehaviours()

    def setTimer(self, timer):
        """Sets the agent timer.

        The agent timer determines the timing behaviour of an agent.
        Is is usually set when loading a plan, as the drive collection
        specifies if a stepped timer (DC) or a real-time timer (RDC) is
        required.

        @param timer: The agent's timer.
        @type timer: L{SPOSH.TimerBase}
        """
        self._timer = timer
        self._timer.reset()
        
    def setSteppedTimer(self):
        """
        Sets SteppedTimer as the timer for the engine (no waits)
        """
        self.setTimer(SteppedTimer())        
        
    def setRealTimeTimer(self, freq):
        """
        Sets RealTimeTime as the timer for the engine (has frequency)
        """
        self.setTimer(RealTimeTimer(freq))    

    def getTimer(self):
        """Returns the currently used timer.

        @return: The currently used timer.
        @rtype: L{SPOSH.TimerBase}
        """
        return self._timer

    def reset(self):
        """Resets the agent's timer.

        This method should be called just before running the main loop.
        """
        self._timer.reset()
    
    def getBehaviour(self, behav_name):
        """Returns the agent's behaviour object with the given name.

        @param behav_name: The name of the behaviour.
        @type behav_name: string
        """
        return self._bdict.getBehaviour(behav_name)
    
    def _loadBehaviours(self,  behaviours):
        """Loads the given behaviours from the behaviour library.
        
        @param libraryName: The name of the behaviour library.
        @type libraryName: string
        @param behaviours: The names of the behaviours to load.
        @type behaviours: sequence of strings
        @return: Behaviour dictionary with the given behaviours.
        @rtype: L{SPOSH.BehaviourDict}
        """
        
        self.debug("Registering behaviour methods")
        beh_dict = BehaviourDict()
        
        for behaviour in behaviours:
            self.debug("Loading behaviour '%s'" % behaviour.getName())
            beh_dict.registerBehaviour(behaviour)
            
        return beh_dict
    
    def followDrive(self):
        """Performes one loop through the drive collection.
        
        This method takes the first triggering drive element and either
        descends further down in the competence tree, or performs
        the drive's current action.
        
        It returns either DRIVE_WON if the drive collection's goal was
        reached, DRIVE_LOST if no drive triggered, or DRIVE_FOLLOWED if
        the goal wasn't reached and a drive triggered.
        
        @return: The result of processing the drive collection.
        @rtype: DRIVE_FOLLOWED, DRIVE_WON or DRIVE_LOST
        """
        self.debug("SPOSH iteration - processing Drive Collection")
        self._timer.loopWait()
        result = self._dc.fire()
        self._timer.loopEnd()
        if result.continueExecution():
            return DRIVE_FOLLOWED
        else:
            if result.nextElement():
                return DRIVE_WON
            else:
                return DRIVE_LOST
