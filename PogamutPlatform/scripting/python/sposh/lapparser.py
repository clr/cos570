"""Parser for .lap files.

The parser accepts the following grammar:

Preprocessing
-------------
  All element matching L{(\#|\;)[^\n]*} are removed. That removes
  all the comments staring with '#' or ';'.

Terminal Symbols
----------------
  The following terminal symbols are accepted::

    AP                       AP
    C                        C
    DC                       DC
    RDC                      RDC
    SDC                      SDC
    SRDC                     SRDC
    nil                      NIL
    (?i)drives               DRIVES
    (?i)elements             ELEMENTS
    (?i)trigger              TRIGGER
    (?i)goal                 GOAL
    (?i)hours                HOURS
    (?i)minutes              MINUTES
    (?i)seconds              SECONDS
    (?i)hz                   HZ
    (?i)pm                   PM
    (?i)none                 NONE
    (?i)documentation        DOCUMENTATION
    (==|=|!=|<|>|<=|>=)      PREDICATE
    \-?(\d*\.\d+|\d+\.)([eE][\+\-]?\d+)?  NUMFLOAT
    \-?[0-9]+                NUMINT
    (?i)[a-z][a-z0-9_\-]*    NAME
    (?i)'?[a-z][a-z0-9_\-]*  STRINGVALUE
    \"[^\"]*\"                  COMMENT

Production Rules
----------------
  The following production rules are used::

                       plan ::= "(" [ "(" <docstring> ]
                                    ( ( "(" <competence> | <action-pattern> )*
                                      "(" <drive-collection>
                                      ( "(" <competence> | <action-pattern> )*
                                    )
                                    | ( "(" <competence> )
                                    | ( "(" <action-pattern> )
                                ")"
                  docstring ::= DOCUMENTATION COMMENT COMMENT COMMENT ")"

           drive-collection ::= <drive-collection-id> NAME
                                ( NIL | "(" <goal> | )
                                "(" DRIVES <drive-priorities> ")" ")"
        drive-collection-id ::= DC | RDC | SDC | SRDC
           drive_priorities ::= <drive-elements>+
             drive-elements ::= "(" <drive-element>+ ")"
              drive-element ::= "(" NAME ( NIL | "(" <trigger> | ) NAME
                                    ( NIL | "(" <freq> | ) <opt-comment> ")"

                 competence ::= C NAME ( NIL | "(" <time> | )
                                ( NIL | "(" <goal> | ) "(" ELEMENTS
                                <competence-priorities> ")" <opt-comment> ")"
      competence-priorities ::= <competence-elements>+
        competence-elements ::= "(" <competence-element>+ ")"
         competence-element ::= "(" NAME [ "(" <trigger> ] NAME [ INTNUM ]
                                    <opt-comment> ")"

             aption-pattern ::= AP NAME ( NIL | "(" <time> | )
                                "(" <action-pattern-elements> <opt-comment> ")"
    action-pattern-elements ::= ( <full-sense> | NAME )+ ")"

                       goal ::= GOAL <senses> ")"
                    trigger ::= TRIGGER <senses> ")"
                     senses ::= ( NIL | "(" ( NAME | <full-sense> )+ ")" )
                 full-sense ::= "(" NAME [<value> [<predicate>]] ")"
                      value ::= NUMINT | NUMFLOAT | NAME | STRINGVALUE | NIL
                  predicate ::= PREDICATE
                  
                       freq ::= <freq-unit> <numfloat> ")"
                  freq-unit ::= HOURS | MINUTES | SECONDS | HZ | PM | NONE
                       time ::= <time-unit> <numfloat> ")"
                  time-unit ::= HOURS | MINUTES | SECONDS | NONE
                   numfloat ::= NUMINT | NUMFLOAT
                   
                opt-comment ::= COMMENT |
  
"""

__revision__ = "0.1"

# Python modules
import sys
from org.python.modules import re

# POSH modules
from planbuilder import PlanBuilder

# ----------------------------------------------------------------------------
# Lexer
# ----------------------------------------------------------------------------

class Token:
    """A single token.
    """
    def __init__(self, token, value):
        """Initilaises the token with a token-name and a value.

        @param token: The name (type) of the token.
        @type token: string
        @param value: The value of the token.
        @type value: string
        """
        self.token = token
        self.value = value


class LAPLexer:
    """A Lexer for tokenising .lap files.

    This lexer is used by L{LAPParser} to tokenise the input string.
    """

    # preprocessing pattern. Everything that they match is
    # substituted by the second string in the pair.
    subs_pattern = (
        (re.compile(r'(\#|\;)[^\n]*'), ''),
    )

    # tokens that match fully, independent of what follows after
    # them. These are tokens that don't need to be separated by
    # separating characters. This doesn't work for reserved words,
    # as they would match even if they only match the beginning
    # of a word.
    full_tokens = (
        (re.compile(r'"[^"]*"'), 'COMMENT'),
    )

    # separating characters are characters that split the input
    # string into tokens. These will be ignored, if they are not
    # in char_tokens.
    separating_chars = ' ()\n\r\t'

    # character tokens are tokens that are represented by single
    # characters. This has to be a subset of separating_chars.
    char_tokens = {
        '(' : 'LPAREN',
        ')' : 'RPAREN',
    }

    # these tokens need to be spearated by separating characters
    # and need to match the strings inbetween fully. The tokens are
    # given in their order of priority. Hence, if several of those
    # tokens match, the first in the list is returned.
    tokens = (
        (re.compile(r"AP"), 'AP'),
        (re.compile(r"C"), 'C'),
        (re.compile(r"DC"), 'DC'),
        (re.compile(r"RDC"), 'RDC'),
        (re.compile(r"SDC"), 'SDC'),
        (re.compile(r"SRDC"), 'SRDC'),
        (re.compile(r"nil"), 'NIL'),
        (re.compile(r"(?i)drives"), 'DRIVES'),
        (re.compile(r"(?i)elements"), 'ELEMENTS'),
        (re.compile(r"(?i)trigger"), 'TRIGGER'),
        (re.compile(r"(?i)goal"), 'GOAL'),
        (re.compile(r"(?i)hours"), 'HOURS'),
        (re.compile(r"(?i)minutes"), 'MINUTES'),
        (re.compile(r"(?i)seconds"), 'SECONDS'),
        (re.compile(r"(?i)hz"), 'HZ'),
        (re.compile(r"(?i)pm"), 'PM'),
        (re.compile(r"(?i)none"), 'NONE'),
        (re.compile(r"(?i)documentation"), 'DOCUMENTATION'),
        (re.compile(r"(==|=|!=|<|>|<=|>=)"), 'PREDICATE'),
        (re.compile(r"\-?(\d*\.\d+|\d+\.)([eE][\+\-]?\d+)?"), 'NUMFLOAT'),
        (re.compile(r"\-?[0-9]+"), 'NUMINT'),
        (re.compile(r"(?i)[a-z][a-z0-9_\-]*"), 'NAME'),
        (re.compile(r"(?i)'?[a-z][a-z0-9_\-]*"), 'STRINGVALUE'),
    )

    # to count the number of newlines
    newline = '\n'
    newlines = re.compile(r"\n")

    def __init__(self, inputStr = None):
        """Initialises the lexer with the given input string.

        @param inputStr: An input string.
        @type inputStr: string
        """
        self._input = ''
        self._lineno = 1
        if inputStr:
            self.setInput(inputStr)

    def setInput(self, inputStr):
        """Resets the lexer by giving it a new input string.

        @param inputStr: An input string.
        @type inputStr: string
        """
        # preprocessing
        for subs in self.subs_pattern:
            inputStr = subs[0].sub(subs[1], inputStr)
        self._input = inputStr
        self._lineno = 1

    def token(self):
        """Returns the next found token in the input string.

        If the input string is empty, then None is returned.

        @return: Next token.
        @rtype: L{Token} or None
        """
        while self._input:
            # first check for full tokens
            for tk in self.full_tokens:
                match = tk[0].match(self._input)
                if match:
                    matched_str = match.group()
                    self._input = self._input[len(matched_str):]
                    # cound the number of newlines in the matched
                    # string to keep track of the line number
                    self._lineno += len(self.newlines.findall(matched_str))
                    return Token(tk[1], matched_str)
                
            # none of the full tokens matched
            # proceed with checking for single characters
            char = self._input[0]
            if char in self.separating_chars:
                self._input = self._input[1:]
                if char == self.newline:
                    self._lineno += 1
                if self.char_tokens.has_key(char):
                    return Token(self.char_tokens[char], char)
                # continue with next charater in input string
                continue

            # none of the separating characters matched
            # let's split the string and check for normal tokens
            sep_pos = -1
            # find the closest separating character
            for sep_char in self.separating_chars:
                pos = self._input.find(sep_char)
                if pos >= 0 and (sep_pos == -1 or pos < sep_pos):
                    sep_pos = pos
            # take the full string if no separating character was found
            if sep_pos == -1:
                sep_str = self._input
            else:
                sep_str = self._input[:sep_pos]
            # find the first fully matching token
            for tk in self.tokens:
                match = tk[0].match(sep_str)
                if match and len(match.group()) == len(sep_str):
                    matched_str = match.group()
                    self._input = self._input[len(matched_str):]
                    # cound the number of newlines in the matched
                    # string to keep track of the line number
                    self._lineno += len(self.newlines.findall(matched_str))
                    return Token(tk[1], matched_str)

            # no token matched: give error over single character
            char = self._input[0]
            self._input = self._input[1:]
            self.error(char)

        # the input string is empty
        return None

    def lineno(self):
        """Returns the current line number.

        @return: The current line number.
        @rtype: int
        """
        return self._lineno

    def error(self, char):
        """Report an illegal character.

        @param char: The illegal character.
        @type char: character
        """
        print "Line %d: Illegal character '%s' found" % (self._lineno, char)


# ----------------------------------------------------------------------------
# Parser
# ----------------------------------------------------------------------------

class ParseError(Exception):
    """An Exception that indicates a parse error.
    """
    pass


class LAPParser:
    """A recursive descent parser for .lap files.

    The parser takes a single input string that represents the plan
    file and creates a plan builder object that it then returns.

    If an error while parsing (or tokenising) is encountered,
    a ParseError is raised.
    """
    def __init__(self):
        """Initialises the parser.
        """
        self._lex = None
        self._t = None

    def parse(self, input_str):
        """Parses the given input and returns a plan builder object.

        @param input_str: The input string.
        @type input_str: string
        @return: The plan builder object representing the plan.
        @rtype: L{SPOSH.PlanBuilder}
        """
        self._lex = LAPLexer(input_str)
        return self.start()

    def nextToken(self):
        """Gets the next token from the lexer.
        """
        self._t = self._lex.token()
        #if self._t:
        #    print "%s: '%s'" % (self._t.token, self._t.value)

    def match(self, allowed_tokens):
        """Checks if the current token matches the allowed tokens.
        
        If there is no current token, then this method raises an Exception
        that indicates that we've reached the end of the input (unexpectedly).
        
        Otherwise it returns if the current token type matches any of the
        given token types.

        @param allowed_tokens: A list of allowed tokens.
        @type allowed_tokens: list of string
        @raise ParseError: If the is no current token.
        @return: If the current token type matches any of the allowed tokens.
        @rtype: boolean
        """
        if not self._t:
            raise ParseError, "Unexpected End Of File (EOF)"
        return (self._t.token in allowed_tokens)
    
    def error(self, msg):
        """Raises an error with the given message.
        
        This method raises a ParseError of type
        'Line xxx: [msg]'.
        
        @param msg: The error message.
        @type msg: string
        @raise ParseError: always
        """
        raise ParseError, "Line %d: %s" % (self._lex.lineno(), msg)

    def start(self):
        """The parser start symbol.

        When called, it parses the set input string and returns
        the created plan builder object.

        @return: A plan builder object representing the parsed plan.
        @rtype: L{SPOSH.PlanBuilder}
        """
        self.nextToken()
        return self.plan()

    def plan(self):
        """plan ::= "(" [ "(" <docstring> ]
                        ( ( "(" <competence> | <action-pattern> )*
                          "(" <drive-collection>
                          ( "(" <competence> | <action-pattern> )*
                        )
                        | ( "(" <competence> )
                        | ( "(" <action-pattern> )
                    ")"

        @return: A plan builder object representing the parsed plan.
        @rtype: L{SPOSH.PlanBuilder}
        """
        plan_builder = PlanBuilder()
        # this method cheats a bit by counting the action-pattern
        # and competences and also drive-collections to check when things are
        # allowed were.
        if not self.match(('LPAREN', )):
            self.error("Plan needs to start with '(' rather than '%s'" % \
                self._t.value)
        self.nextToken()
        # action pattern, competence, docstring, drive collection
        ap, c, d, dc = 0, 0, 0, 0
        while 1:
            if not self.match(('LPAREN', 'RPAREN')):
                self.error("Expected '(' as start of documentation / " \
                    "competence / action-pattern / drive-collection, or " \
                    "')' to end plan, instead of '%s'" % self._t.value)
            if self.match(('RPAREN', )):
                # end of plan
                self.nextToken()
                break
            self.nextToken()
            # check for documentation
            if self.match(('DOCUMENTATION', )):
                if ap + c + dc + d > 0:
                    self.error("Documentation only allowed as first " \
                        "element in plan")
                d += 1
                plan_builder.setDocstring(self.docstring())
                #print self.docstring()
            # check for competence
            elif self.match(('C', )):
                c += 1
                plan_builder.addCompetence(self.competence())
                #print self.competence()
            # check for action-pattern
            elif self.match(('AP', )):
                ap += 1
                plan_builder.addActionPattern(self.action_pattern())
                #print self.action_pattern()
            # check for drive-collection
            elif self.match(('DC', 'RDC', 'SDC', 'SRDC')):
                if dc > 0:
                    self.error("Only a single drive-collection allowed")
                dc += 1
                plan_builder.setDriveCollection(self.drive_collection())
                #print self.drive_collection()
            else:
                self.error("Expected docstring / competence / action " \
                    "pattern or drive collection instead of '%s'" % \
                    self._t.value)
        # the plan was closed
        if self._t:
            self.error("Illegal token '%s' after end of plan" % self._t.value)
        if dc == 0 and (ap + c) != 1:
            self.error("Illegal plan: A plan without a drive-collection " \
                "only allows for a SINLGE action-pattern OR a SINGLE " \
                "competence")
        # everything fine
        return plan_builder

    def docstring(self):
        """docstring ::= DOCUMENTATION COMMENT COMMENT COMMENT ")"

        @return: The three comments.
        @rtype: (string, string, string)
        """
        if not self.match(('DOCUMENTATION', )):
            self.error("Expected 'documentation' as start of docstring " \
                "instead of '%s'" % self._t.value)
        self.nextToken()
        docs = []
        for i in range(3):
            if not self.match(('COMMENT', )):
                self.error("Expected a comment of form \"...\" instead " \
                    "of '%s' in documentation" % self._t.value)
            docs.append(self._t.value[1:-1])
            self.nextToken()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' to end docstring instead of '%s'" % \
                self._t.value)
        self.nextToken()
        return docs
        
    
    def drive_collection(self):
        """drive-collection ::= <drive-collection-id> NAME
                                ( NIL | "(" <goal> | )
                                "(" DRIVES <drive-priorities> ")" ")"
        
        If no goal is given, None is returned for the goal.
        
        @return: The drive collection as 
            (id, name, goal, [priority1, priority2, ...])
        @rtype: (string, string, goal, [priorities, ...])
        """
        cid = self.drive_collection_id()
        if not self.match(('NAME', )):
            self.error("Expected a valid drive collection name instead " \
                "of '%s'" % self._t.value)
        name = self._t.value
        self.nextToken()
        # check if there is a goal and set it if given
        # ( NIL | "(" <goal> | ) "("
        goal = None
        if self.match(('NIL', )):
            # NIL "(" 
            self.nextToken()
            if not self.match(('LPAREN', )):
                self.error("Expected '(' after 'nil' instead of '%s' in " \
                    "drive collection '%s'" % (self._t.value, name))
            self.nextToken()
        else:
            # "(" [ <goal> "(" ]
            if not self.match(('LPAREN', )):
                self.error("Expected '(' after drive collection name " \
                  "instead of '%s' in drive collection '%s'" % \
                  (self._t.value, name))
            self.nextToken()
            # check if a goal is specified
            if self.match(('GOAL', )):
                # <goal> "("
                goal = self.goal()
                if not self.match(('LPAREN', )):
                    self.error("Expected '(' after goal instead of '%s' " \
                        "in drive collection '%s'" % (self._t.value, name))
                self.nextToken()
        # get the drive priorities
        if not self.match(('DRIVES', )):
            self.error("Expected 'drives' instead of '%s' in drive " \
                "collection '%s'" % (self._t.value, name))
        self.nextToken()
        priorities = self.drive_priorities()
        for i in range(2):
            if not self.match(('RPAREN', )):
                self.error("Expected ')' to end drive collection instead " \
                    "of '%s' in drive collection '%s'" % (self._t.value, name))
            self.nextToken()
        return (cid, name, goal, priorities)
    
    def drive_collection_id(self):
        """drive-collection-id ::= DC | RDC | SDC | SRDC
        
        @return: The drive collection id as a string.
        @rtype: string
        """
        if not self.match(('DC', 'RDC', 'SDC', 'SRDC')):
            self.error("Expected the drive collection type instead of '%s'" %
                self._t.value)
        cid = self._t.token
        self.nextToken()
        return cid
    
    def drive_priorities(self):
        """drive_priorities ::= <drive-elements>+

        @return: A list of drive priorities.
        @rtype: Sequence of objects as given by L{drive_elements}.
        """
        if not self.match(('LPAREN', )):
            self.error("Expected '(' that starts list of drive elements " \
                "instead of '%s'" % self._t.value)
        priorities = []
        while self.match(('LPAREN', )):
            priorities.append(self.drive_elements())
        return priorities
    
    def drive_elements(self):
        """drive-elements ::= "(" <drive-element>+ ")"
        
        @return: A sequence of drive elements as given by L{drive_element}
        @rtype: Sequence of objects given by L{drive_element}
        """
        if not self.match(('LPAREN', )):
            self.error("Expected '(' to start list of drive elements " \
                "instead of '%s'" % self._t.value)
        self.nextToken()
        if not self.match(('LPAREN', )):
            self.error("Expected '(' to start drive element instead " \
                "of '%s'" % self._t.value)
        elements = []
        while self.match(('LPAREN', )):
            elements.append(self.drive_element())
        if not self.match(('RPAREN', )):
            self.error("Expected ')' to end list of drive elements " \
                "instead of '%s'" % self._t.value)
        self.nextToken()
        return elements
    
    def drive_element(self):
        """drive-element ::= "(" NAME ( NIL | "(" <trigger> | ) NAME
                                 ( NIL | "(" <freq> | ) <opt-comment> ")"
         
        If no trigger is given, then None is returned for the trigger.
        If no frequency is given, then None is returned for the frequency.
        
        @return: The drive element as (name, trigger, triggerable, freq)
        @rtype: (string, trigger, string, long)
        """
        if not self.match(('LPAREN', )):
            self.error("Expected '(' to start drive element instead " \
                "of '%s'" % self._t.value)
        self.nextToken()
        if not self.match(('NAME', )):
            self.error("Expected valid drive element name instead of '%s'" % \
                self._t.value)
        name = self._t.value
        self.nextToken()
        # ( NIL | "(" <trigger> | ) NAME
        if not self.match(('NAME', 'LPAREN', 'NIL')):
            self.error("Expected name of triggerable, '(' or 'nil' " \
                "instead of '%s' in drive element '%s'" % \
                (self._t.value, name))
        # get trigger if there is one
        trigger = None
        if self.match(('NIL', 'LPAREN')):
            if self.match(('NIL', )):
                self.nextToken()
            else:
                self.nextToken()
                trigger = self.trigger()
            if not self.match(('NAME', )):
                self.error("Expected name of triggerable instead of '%s' " \
                    "in drive elements '%s'" % (self._t.value, name))
        # get triggerable (NAME)
        triggerable = self._t.value
        self.nextToken()
        # check for frequency
        # ( NIL | "(" <freq> | )
        freq = None
        if self.match(('LPAREN', 'NIL')):
            if self.match(('NIL', )):
                self.nextToken()
            else:
                self.nextToken()
                freq = self.freq()
        # <opt-comment> ")"
        self.opt_comment()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' instead of '%s' as the end of drive " \
                "element '%s'" % (self._t.value, name))
        self.nextToken()
        return (name, trigger, triggerable, freq)
    
    def competence(self):
        """competence ::= C NAME ( NIL | "(" <time> | )
                          ( NIL | "(" <goal | ) "(" ELEMENTS
                          <competence-priorities> ")" <opt-comment> ")"

        If no time is given, them time is set to None.
        If no goal is given, the goal is set to None.

        @return: The competence as (name, time, goal, priorities)
        @rtype: (string, time, goal, priorities)
        """
        # C NAME
        if not self.match(('C', )):
            self.error("Expected 'C' as start of competence instead " \
                "of '%s'" % self._t.value)
        self.nextToken()
        if not self.match(('NAME', )):
            self.error("Expected valid competence name instead " \
                "of '%s'" % self._t.value)
        name = self._t.value
        self.nextToken()
        # ( NIL | "(" <time> | ) ( NIL | "(" <goal> | ) "("
        # The branching below should be checked (might have missed a case)
        if not self.match(('LPAREN', 'NIL')):
            self.error("Expected '(' or 'nil' after competence name " \
                "instead of '%s' in competence '%s'" % (self._t.value, name))
        time, goal = None, None
        if self.match(('NIL', )):
            # NIL ( NIL | "(" <goal> | ) "("
            self.nextToken()
            if not self.match(('LPAREN', 'NIL')):
                self.error("Expected '(' or 'nil' after 'nil' for time " \
                    "instead of '%s' in competence '%s'" % \
                    (self._t.value, name))
            if self.match(('NIL', )):
                # NIL NIL "("
                self.nextToken()
                if not self.match(('LPAREN', )):
                    self.error("Expected '(' after 'nil' for goal instead " \
                        "of '%s' in competence '%s'" % (self._t.value, name))
                self.nextToken()
            else:
                # NIL "(" [ <goal> "(" ]
                self.nextToken()
                if self.match(('GOAL', )):
                    goal = self.goal()
                    if not self.match(('LPAREN', )):
                        self.error("Expected '(' after goal instead of " \
                            "'%s' in competence '%s'" % (self._t.value, name))
                    self.nextToken()
        else:
            # "(" ( <time> ( NIL | "(" <goal> | ) "(" | <goal> "(" | )
            self.nextToken()
            if self.match(('HOURS', 'MINUTES', 'SECONDS', 'NONE')):
                # "(" <time> ( NIL | "(" <goal> | ) "("
                time = self.time()
                if not self.match(('LPAREN', 'NIL')):
                    self.error("Expected '(' or 'nil' after time instead " \
                        "of '%s' in competence '%s'" % (self._t.value, name))
                if self.match(('NIL', )):
                    # "(" <time> NIL "("
                    self.nextToken()
                    if not self.match(('LPAREN', )):
                        self.error("Expected '(' after 'nil' for goal " \
                            "instead of '%s' in competence '%s'" % \
                            (self._t.value, name))
                    self.nextToken()
                else:
                    # "(" <time> "(" [ <goal> "(" ]
                    self.nextToken()
                    if self.match(('GOAL', )):
                        goal = self.goal()
                        if not self.match(('LPAREN', )):
                            self.error("Expected '(' after goal instead " \
                                "of '%s' in competence '%s'" % \
                                (self._t.value, name))
                        self.nextToken()
            elif self.match(('GOAL', )):
                # "(" <goal> "("
                goal = self.goal()
                if not self.match(('LPAREN', )):
                    self.error("Expected '(' after goal instead of '%s' " \
                        "in competence '%s'" % (self._t.value, name))
                self.nextToken()
        # competence priorities
        # ELEMENTS <competence-priorities> <opt-comment> ")"
        if not self.match(('ELEMENTS', )):
            self.error("Expected 'elements' as start of element instead " \
                "of '%s' in competence '%s'" % (self._t.value, name))
        self.nextToken()
        elements = self.competence_priorities()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' to end competence elements instead " \
                "of '%s' in competence '%s'" % (self._t.value, name))
        self.nextToken()
        self.opt_comment()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' to end competence instead of '%s' " \
                "in competence '%s'" % (self._t.value, name))
        self.nextToken()
        return (name, time, goal, elements)
    
    def competence_priorities(self):
        """competence-priorities ::= <competence-elements>+

        @return: A list of competence priorities.
        @rtype: Sequence of objects as given by L{competence_elements}.
        """
        if not self.match(('LPAREN', )):
            self.error("Expected '(' as start of a list of competence " \
                "elements instead of '%s'" % self._t.value)
        priorities = []
        while self.match(('LPAREN', )):
            priorities.append(self.competence_elements())
        return priorities
    
    def competence_elements(self):
        """competence-elements ::= "(" <competence-element>+ ")"
        
        @return: A sequence of competence elements as given by
            L{competence_element}
        @rtype: Sequence of objects given by L{competence_element}
        """
        if not self.match(('LPAREN', )):
            self.error("Expected '(' as start of a list of competence " \
                "elements instead of '%s'" % self._t.value)
        self.nextToken()
        # a competence element start with a '('
        if not self.match(('LPAREN', )):
            self.error("Expected '(' to start a competence element " \
                "instead of '%s'" % self._t.value)
        elements = []
        while self.match(('LPAREN', )):
            elements.append(self.competence_element())
        if not self.match(('RPAREN', )):
            self.error("Expected ')' as end of a list of competence " \
                "elements instead of '%s'" % self._t.value)
        self.nextToken()
        return elements
    
    def competence_element(self):
        """competence-element ::= "(" NAME ( NIL | "(" <trigger> | ) NAME
                                      ( NIL | INTNUM | )
                                      <opt-comment> ")"

        If no number of retires is given, then -1 is returned.

        @return: The competence element as
            (name, trigger, triggerable, maxRetries)
        @rtype: (string, trigger, string, int)
        """
        # "(" NAME
        if not self.match(('LPAREN', )):
            self.error("Expected '(' to start a competence element " \
                "instead of '%s'" % self._t.value)
        self.nextToken()
        if not self.match(('NAME', )):
            self.error("Expected competence element name instead of " \
                "'%s'" % self._t.value)
        name = self._t.value
        self.nextToken()
        # check for trigger
        # ( NIL | "(" <trigger> | )
        trigger = None
        if self.match(('NIL', )):
            self.nextToken()
        elif self.match(('LPAREN', )):
            self.nextToken()
            trigger = self.trigger()
        # NAME
        if not self.match(('NAME', )):
            self.error("Expected name of triggerable instead of '%s' in " \
                "competence '%s'" % (self._t.value, name))
        triggerable = self._t.value
        self.nextToken()
        # check for maxRetries
        # ( NIL | INTNUM | )
        retries = -1l
        if self.match(('NIL', )):
            self.nextToken()
        elif self.match(('NUMINT', )):
            retries = long(self._t.value)
            self.nextToken()
        # <opt-comment> ")"
        self.opt_comment()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' to end competence element instead " \
                "of '%s' in competence '%s'" % (self._t.value, name))
        self.nextToken()
        return (name, trigger, triggerable, retries)

    def action_pattern(self):
        """aption-pattern ::= AP NAME ( NIL | "(" <time> | )
                              "(" <action-pattern-elements> <opt-comment> ")"

        If no time is given, None is returned for the time.

        @return: The action pattern as (name, time, [name1, name2, ...])
        @rtype: (string, long, (string or full-sense, ...))
        """
        # AP NAME
        if not self.match(('AP', )):
            self.error("Expected 'AP' instead of '%s'" % self._t.value)
        self.nextToken()
        if not self.match(('NAME', )):
            self.error("'%s' is not a valid name for an action " \
                "pattern" % self._t.value)
        name = self._t.value
        self.nextToken()
        # ( NIL | "(" <time> | ) "("
        time = None
        if self.match(('NIL', )):
            # NIL "("
            self.nextToken()
            if not self.match(('LPAREN', )):
                self.error("Expected '(' after 'nil' for time instead " \
                    "of '%s' in action pattern '%s'" % (self._t.value, name))
            self.nextToken()
        elif self.match(('LPAREN', )):
            # "(" [ <time> "(" ]
            self.nextToken()
            if self.match(('HOURS', 'MINUTES', 'SECONDS', 'NONE')):
                # "(" <time> "("
                time = self.time()
                if not self.match(('LPAREN', )):
                    self.error("Expected '(' after time instead of '%s' " \
                        "in action pattern '%s'" % (self._t.value, name))
                self.nextToken()
        else:
            self.error("Expected '(' or 'nil' after action pattern name " \
                "instead of '%s' in action pattern '%s'" % \
                (self._t.value, name))
        # proceed with action pattern element list
        # <action-pattern-elements> <opt-comment> ")"
        elements = self.action_pattern_elements()
        self.opt_comment()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' instead of '%s' in action pattern " \
                "'%s'" % (self._t.value, name))
        self.nextToken()
        return (name, time, elements)

    def action_pattern_elements(self):
        """action-pattern-elements ::= ( <full-sense> | NAME )+ ")"

        @return: A list of action pattern elements.
        @rtype: sequence of strings and objects as returned by
            L{full_sense}
        """
        elements = []
        if not self.match(('LPAREN', 'NAME')):
            self.error("Expected an action pattern element name of '(' " \
                "instead of '%s'" % self._t.value)
        while self.match(('NAME', 'LPAREN')):
            if self.match(('LPAREN', )):
                elements.append(self.full_sense())
            else:
              elements.append(self._t.value)
              self.nextToken()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' to end action pattern instead of " \
                "'%s'" % self._t.value)
        self.nextToken()
        return elements
    
    def goal(self):
        """goal ::= GOAL <senses> ")"

        If the list of senses is empty, then None is returned.
        
        @return: A list of senses that were given as the goal
        @rtype: Seuquence of strings and 3-tuples
        """
        if not self.match(("GOAL", )):
            self.error("Expected 'goal' instead of '%s'" % self._t.value)
        self.nextToken()
        senses = self.senses()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' as the end of a goal instead of '%s'" % \
                self._t.value)
        self.nextToken()
        if senses:
            return senses
        else:
            return None

    def trigger(self):
        """trigger ::= TRIGGER <senses> ")"

        If the list of senses is empty, then None is returned.
        
        @return: A list of senses that were given as the trigger
        @rtype: Sequence of strings and 3-tuples
        """
        if not self.match(("TRIGGER", )):
            self.error("Expected 'trigger' instead of '%s'" % self._t.value)
        self.nextToken()
        senses = self.senses()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' as the end of a trigger instead " \
                "of '%s'" % self._t.value)
        self.nextToken()
        if senses:
            return senses
        else:
            return None
    
    def senses(self):
        """senses ::= ( NIL | "(" ( NAME | <full-sense> )+ ")" )

        If NIL is given, an empty list is returned.

        @return: A list of senses and full-senses
        @rtype: sequence of string and 3-tuple
        """
        if self.match(('NIL', )):
            self.nextToken()
            return []
        if not self.match(('LPAREN', )):
            self.error("Expected '(' instead of '%s'" % self._t.value)
        self.nextToken()
        elements = []
        while 1:
            if self.match(('RPAREN', )):
                break
            if not self.match(('NAME', 'LPAREN')):
                self.error("Expected either a sense-act name or '(' " \
                    "instead of '%s'" % self._t.value)
            # differentiate between sense-acts and senses
            if self.match(('NAME', )):
                elements.append(self._t.value)
                self.nextToken()
            else:
                elements.append(self.full_sense())
        # matches ')'
        self.nextToken()
        return elements

    def full_sense(self):
        """full-sense ::= "(" NAME [<value> [<predicate>]] ")"

        @return: The full sense, and None for the elements that
            are not specified.
        @rtype: sequence of string/None
        """
        if not self.match(('LPAREN', )):
            self.error("Expected '(' instead of '%s'" % self._t.value)
        self.nextToken()
        if not self.match(('NAME', )):
            self.error("Expected sense name instead of '%s'" % self._t.value)
        name = self._t.value
        self.nextToken()
        value, pred = None, None
        if not self.match(('RPAREN', )):
            value = self.value()
            if not self.match(('RPAREN', )):
                pred = self.predicate()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' instead of '%s'" % self._t.value)
        self.nextToken()
        return (name, value, pred)

    def value(self):
        """value ::= NUMINT | NUMFLOAT | NAME

        @return: The value as string.
        @rtype: string
        """
        if not self.match(('NUMINT', 'NUMFLOAT',
                           'NAME', 'STRINGVALUE', 'NIL')):
            self.error("Expected a valid sense value instead " \
                "of '%s'" % self._t.value)
        value = self._t.value
        self.nextToken()
        return value

    def predicate(self):
        """predicate ::= PREDICATE

        @return: The predicate as string.
        @rtype: string
        """
        if not self.match(('PREDICATE', )):
            self.error("Expected a valid sense predicate instead " \
               "of '%s'" % self._t.value)
        pred = self._t.value
        self.nextToken()
        return pred
        
    def freq(self):
        """freq ::= <freq-unit> <numfloat> ")"

        @return: frequency as period time.
        @rtype: long
        """
        unit = self.freq_unit()
        value = self.numfloat()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' instead of '%s'" % self._t.value)
        self.nextToken()
        # process the frequency unit
        if unit == 'HOURS':
            return long(3600000.0 * value)
        elif unit == 'MINUTES':
            return long(60000.0 * value)
        elif unit == 'SECONDS':
            return long(1000.0 * value)
        elif unit == 'HZ':
            return long(1000.0 / value)
        elif unit == 'PM':
            return long(60000.0 / value)
        else:
            return long(value)

    def freq_unit(self):
        """freq-unit ::= HOURS | MINUTES | SECONDS | HZ | PM | NONE

        @return: The token string of the frequency unit.
        @rtype: string
        """
        if not self.match(('HOURS', 'MINUTES', 'SECONDS', 'HZ', 'PM', 'NONE')):
            self.error("Expected a valid frequency unit instead " \
                "of '%s'" % self._t.value)
        unit = self._t.token
        self.nextToken()
        return unit

    def time(self):
        """time ::= <time-unit> <numfloat> ")"

        @return: time in milliseconds.
        @rtype: long
        """
        unit = self.time_unit()
        value = self.numfloat()
        if not self.match(('RPAREN', )):
            self.error("Expected ')' instead of '%s'" % self._t.value)
        self.nextToken()
        # process the time unit
        if unit == 'HOURS':
            return long(3600000.0 * value)
        elif unit == 'MINUTES':
            return long(60000.0 * value)
        elif unit == 'SECONDS':
            return long(1000.0 * value)
        else:
            return long(value)

    def time_unit(self):
        """time-unit ::= HOURS | MINUTES | SECONDS | NONE

        @return: The unit as token string.
        @rtype: string
        """
        if not self.match(('HOURS', 'MINUTES', 'SECONDS', 'NONE')):
            self.error("Expected a valid time unit instead of '%s'" % \
                self._t.value)
        unit = self._t.token
        self.nextToken()
        return unit

    def numfloat(self):
        """numfloat ::= NUMINT | NUMFLOAT

        @return: The number as float.
        @rtype: float
        """
        if not self.match(('NUMINT', 'NUMFLOAT')):
            self.error("Expected a floating-point number instead of '%s'" % \
                self._t.value)
        val = self._t.value
        self.nextToken()
        return float(val)

    def opt_comment(self):
        """opt-comment ::= COMMENT |

        @return: Nothing
        @rtype: None
        """
        if self.match(('COMMENT', )):
            self.nextToken()
        return None


# test lexer on file given as only argument
#f = open(sys.argv[1]).read()
#l = LAPLexer(f)
#while 1:
#    t = l.token()
#    if t:
#        print "%s: '%s'" % (t.token, t.value)
#    else:
#        break


# entering plans at the command line
# while 1:
#    try:
#        s = raw_input()
#    except EOFError:
#        break
#    try:
#        LAPParser(s)
#    except ParseError, msg:
#        print msg

# test parser on file given as only argument
#f = open(sys.argv[1]).read()
#try:
#    p = LAPParser()
#    p.parse(f)
#except ParseError, msg:
#    print "ParseError:", msg
