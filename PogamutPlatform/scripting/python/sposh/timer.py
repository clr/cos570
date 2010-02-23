"""Implementation of the agent timer.

The agent timer is responsible for checking drive element call
frequencies, and for adjusting the loop timing. The time is usually
initialised at 0 and then each call to C{time} returns the time in
milliseconds that has passed since initialisation.

Currently, this module provides a stepped timer and a real-time
timer. The step timer increases its time by 1 every time that
loopEnd() is called, but does not provide frequency checking and
neither cares about the loop timing, as it is assumed that the timing
is controlled from the outside. The real-time timer uses the pc time
and provides both frequency checking and loop frequency control.
"""

# Python modules
import sys
import time
from operator import add

if sys.platform == "win32":
    # On Windows, the best timer is time.clock()
    default_timer = time.clock
else:
    # On most other platforms the best timer is time.time()
    default_timer = time.time

def timestamp():
    """Returns the current timestamp in milliseconds.
    
    @return: time stamp in milliseconds.
    @rtype: long
    """
    return long(default_timer() * 1000.0)


class TimerBase:
    """An agent timer base class.

    This class defines the interface of an agent timer class.
    """
    def __init__(self):
        """Initialises the timer.

        This method resets the timer.
        """
        self.reset()
        
    def reset(self):
        """Resets the timer.

        Resetting the timer sets its internal starting time to 0. All
        calls to L{time} after calling this method return
        the time that has passed since the this method has been
        classed.
        """
        raise NotImplementedError

    def time(self):
        """Returns the current time in milliseconds.

        @return: The current time in milliseconds.
        @rtype: long
        """
        raise NotImplementedError

    def loopEnd(self):
        """To be called at the end of each loop.

        For a stepped timer, this method increases the time. For a
        real-time timer, this method does nothing.
        """
        raise NotImplementedError

    def loopWait(self):
        """Manages the loop frequency.

        This method is supposed to be called at the end of each loop
        to adjust the loop frequency. It waits a certain time and then
        returns, to make the loop run at a certain frequency. Hence,
        it holds statistics about the time inbetween two calls of this
        methods and adjusts the wait time to achieve the required time
        difference.
        """
        raise NotImplementedError

    def setLoopFreq(self, loop_freq):
        """Sets the new loop frequency and resets the timer.

        This method should only affect real-time timers.

        @param loop_freq: The loop frequence, given by the time in milliseconds
            that one loop should take.
        @type loop_freq: long.
        """
        raise NotImplementedError


class SteppedTimer(TimerBase):
    """A stepped agent timer.

    This timer is a stepped timer, which is to be used if the agent is
    stepped, i.e. controlled from and outside controller. The timer
    starts at time 0 and increases the time every time that L{loopEnd} is
    called. It does not provide loop timing, as that wouldn't make any
    sense if the agent is controlled from the outside.
    """
    def __init__(self):
        self._time = 0L
        TimerBase.__init__(self)

    def reset(self):
        """Resets the timer by setting its internal time to 0.
        """
        self._time = 0L

    def time(self):
        """Returns the current state of the internal timer.

        @return: The current state of the internal timer.
        @rtype: long
        """
        return self._time

    def loopEnd(self):
        """Increases the internal timer by 1.
        """
        self._time += 1

    def loopWait(self):
        """Does nothing, as the stepped timer does not provide loop control.
        """
        pass

    def setLoopFreq(self, loop_freq):
        """Does nothing, as the stepped timer does not provide loop control.
        """
        pass


class RealTimeTimer(TimerBase):
    """An agent real-time timer.

    The real-time timer relies on the system clock for its timing. On
    initialising and resetting the timer, its internal clock is set to
    0, and any call to L{time} returns the time that passed since the
    timer was resetted last. The timer provides loop frequency
    control.
    """
    def __init__(self, loop_freq):
        """Resets the timer and sets the loop frequency.

        The loop frequency is the one used by L{loopWait}.

        @param loop_freq: The wanted loop frequency, given by the time in
            milliseconds that one loop should take.
        @type loop_freq: long.
        """
        self._base = 0
        self._last_return = 0
        self._proc_time = None
        self._freq = loop_freq
        self._wait = float(1) / float(self._freq)
        TimerBase.__init__(self)

    def reset(self):
        """Resets the timer.

        All future calls to L{time} return the time that passed since this
        method was called last.
        """
        self._last_return = 0
        self._proc_time = None
        self._base = timestamp()

    def time(self):
        """Returns the time passed since the last call of L{reset}.

        @return: Time passed in milliseconds.
        @rtype: long
        """
        return timestamp() - self._base

    def loopEnd(self):
        self._proc_time = self.time()

    def loopWait(self):
        """Waits some time to adjust the loop frequency.

        The loop frequency is the one given on initialising the timer, or
        by calling L{setLoopFreq}. The method adjusts its own waiting time
        based on passed statistics about when it was called, to reach that
        it is called in a certain interval, based on the assumption that the
        process that calls this method always takes the same time inbetween
        calling this method.

        The waiting time is estimated based on the average of the estimate
        of the last 5 process times. The process time is estimated by the
        time inbetween the last return of this method and the time when it
        is called the next time.

        To make sure that the process time estimate is accurate, the
        timer has to be resetted (by calling L{reset}) just before the
        loop is started (for the first time, or after a pause).
        """
        if self._proc_time == None:
            return
        ts = self.time()
        pc = self._proc_time
        diff = ts - pc
        if diff >= self._wait:
            return            
        time.sleep(self._wait - diff)
        
    def setLoopFreq(self, loop_freq):
        """Sets the new loop frequency and resets the timer.

        @param loop_freq: The loop frequence, given by the time in milliseconds
            that one loop should take.
        @type loop_freq: long.
        """
        self._freq = loop_freq
        self._wait = float(1) / float(self._freq)
        self.reset()
