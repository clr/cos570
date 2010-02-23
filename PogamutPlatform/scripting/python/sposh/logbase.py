"""Module providing the logging base class.
    
   Adjusted for Pogamut 2 -> whole POSH-Engine therefore shares one log (java.util.logging.Logger instance). 
"""

class LogBase:
    """Base for agent-based log messages.
    """
    def __init__(self, log, domain):
        """Initialises the logger.
        
        @param log: java.util.logging.Logger instance
        @type log: java.util.logging.Logger instance
        @param domain: identificator of the SPOSH engine part
        @type domain: string
        """       
        self._log = log
        self._domain = domain
        
    def getLog(self):
        """Returns the LogBase's log instance.

        @return: The LogBase's log instance.
        @rtype: java.util.logging.Logger
        """
        return self._log        
        
    def debug(self, message):
        self._log.info(self._domain + ": " +message) 