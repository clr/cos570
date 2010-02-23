package simplebot;

import cz.cuni.pogamut.Client.Agent;
import java.util.logging.Level;
import java.util.ArrayList;
import java.util.logging.Level;

import cz.cuni.pogamut.MessageObjects.*;

/**
 * This is the simplest bot ever :-)
 * <p><p>
 * It picks a navigation point at random and tries to get there.
 * <p><p>
 * Check the user log for informations, observe how it is running.
 * 
 * @author Jimmy
 */
public class Main extends Agent {

    /** Creates a new instance of agent. */
    public Main() {
    }
    NavPoint chosenNavigationPoint = null;

    /**
     * Main method of the bot's brain - we're going to do some thinking about
     * the situation we're in (how it's unfair to be the bot in the gloomy world
     * of UT2004 :-).
     * <p>
     * Check out the javadoc for this class - there you find a basic concept
     * of this bot.
     */
    protected void doLogic() {
        // marking next iteration
        log.fine("doLogic iteration");

        // if don't have any navigation point chosen
        if (chosenNavigationPoint == null) {
            // let's pick one at random
            chosenNavigationPoint = memory.getKnownNavPoints().get(
                    random.nextInt(memory.getKnownNavPoints().size()));
        }
        // here we're sure the chosenNavigationPoint is not null
        // call method iteratively to get to the navigation point
        if (!gameMap.safeRunToLocation(chosenNavigationPoint.location)) {
            // if safeRunToLocation() returns false it means
            if (Triple.distanceInSpace(memory.getAgentLocation(), chosenNavigationPoint.location) < 100) {
                // 1) we're at the navpoint
                log.info("I've successfully arrived at navigation point!");
            } else {
                // 2) something bad happens
                log.info("Darn the path is broken :(");
            }
            // nullify chosen navigation point and chose it during the
            // next iteration of the logic
            chosenNavigationPoint = null;
        }
    }

    /**
     * NOTE: this method MUST REMAIN DEFINED + MUST REMAIN EMPTY, due to technical reasons.
     */
    public static void main(String[] Args) {
    }
}


