# simulation_project

# Problem Domain

We will model the elevators in Benedum during class time. This problem is interesting because elevator scheduling is an NP-Hard problem. In other words, it cannot be solved analytically in polynomial time. Furthermore, Benedum is a building where a large number of classes are held and the elevator traffic tends to correspond to the class schedule. This makes the Benedum elevators more worthwhile to model because we can better predict traffic patterns compared to a building like the Union where no classes are held. Waiting for elevators is a common occurrence in our daily lives, and we spend more time doing this than we likely realize. Making this as efficient as possible to reduce our average wait time would save us countless hours over the course of time. 

# Problems to solve

## Core Questions

1. Which elevator algorithm is most efficient (lowest average time for a unique person to get through the system)?
   Motivation: Important building block for problems that apply elevator wait times to other questions 
   Note: we will implement some common heuristics, as well as try to come up with our own versions if we have time
   
2. How many (what range of) floors does a person need to travel in order for using the elevator to take less time than the stairs?
   Motivation: Many people opt to take the stairs for classes/rooms on lower floors. To add extra motivation (or perhaps demotivation) it    would be interesting to see if taking the stairs results in a lower average time to get through the system.
   
3. When is the best day/time to try to use the elevators (lowest traffic/wait times)?
   Motivation: Due to the way classes are scheduled, there will be specific points during each day and even specific days during each week where elevator traffic is especially low. Knowing these times help enable us to determine how often choosing the elevator instead of the stairs will save you time. 
   
4. How is wait time related to floor origin/destination?
   Motivation: Cathedral of Learning and Benedum have elevators that do not go to every floor. If you are waiting for an elevator that services one of these floors, your wait time may be different than someone waiting for one of the elevators that ignores those floors. 

# Bonus Questions: If We Have Time

Answers to these questions may be interesting, but finding a good solution will be difficult. If we have time/data, we’ll try to address them.

1. What algorithms would be most resilient against riders that break elevator etiquette?  (Getting on when the elevator is going the wrong direction, pressing multiple destinations, exceeding weight limits)

2. How does elevators being aware of each other’s activities affect wait times/etc?

3. How is the algorithm efficiency affected by information supplied at request time
   Ex: up/down vs. known destination vs only know that someone is requesting vs etc

# Approach

## Acquiring Data

We e-mailed the area coordinator for facilities management in the Cathedral of Learning, to ask for access to any logged elevator data. Thus, if we get this data, we will not need so much manual collection of data, and we can address our problems within different buildings.

We also found data about the design standards from the facilities management along with their standards for elevator operation (wait times, speed, etc). We will be able to use this within validation.

We will base our traffic generation on when students have classes. We will build in a slight overhead for other people in the building, but will make a few simplifying assumptions regarding inter-floor travel within the building.
Assumptions:

* Students will arrive at the building according to some distribution (tbd) before class starts
* Students will leave the building according to some distribution (tbd) after class ends
* Student primarily constitute elevator traffic.
* People enter the building from the Ground/First floor in some consistent ratio.

We will gather data in order to estimate this ratio.

The data for these estimations will come from the class registrar within peoplesoft (data in shared drive).

## Model Components

* Queues for individual floors
    - Disorderly, more aggressive people push their way ahead in the queue
    - People are generated with randomized aggression levels
* Elevators with various algorithms
* States/Configuration:
    - Max capacity
    - Current Capacity
    - Current Floor
    - Floor Range
* Global Future event queue (Priority queue)
* Global Configuration Parameters
    - Elevator Travel Speed (Specified in Facilities Management Standards)
    - Walking Speed (for stairs, if necessary for simulation)
* Validation - How will you check to see if your model is functioning as expected?
    - Sanity Checks
    - People in vs People Out
    - Elevator Utilization
    - Basic Checks on statistics for wait times 
        + Range, average, stdev, median, etc
    - No starvation (person never gets off, person waits infinitely, etc.)
    - Checks against standardized design guidelines (specified by Pitt facilities management) applicable for Pitt’s buildings
        + Any significant deviations will be investigated


# Experimental Design

1. Which elevator algorithm is most efficient (lowest average time for a unique person to get through the system)?

To evaluate this question, we will run a simulation of a week in Benedum under our different elevator routing algorithms multiple times.  We will initially try for 25 times, then see if the computing time allows for a greater number of trials.  For each trial, we will export to a csv file the time it took each user to move through the system and their initial wait time for an elevator.  No other data about the the trials will be required for analysis.  In a separate script, we will read the csv files back in and compute the averagefor each algorithm.  The algorithm with the lowest will be deemed most efficient and used as the baseline for subsequent problems.

In order to assess the validity of our algorithms, we will run several one-day trials where we track users movements through the system, ensuring that nobody is stranded on the elevator, that people travel to the correct destination, that weight limits are not exceeded and that there are no outliers with excessive wait times.  We will also compare our accepted most-efficient algorithm against the facilities management minimum standards; that the average wait time for an elevator on lobby floors is 0-20 seconds, that 80% or more wait times are within that range and that less than 2% of wait times are greater than 26.6 seconds.  We will also compare those numbers to data collected at the elevator lobbies to ensure these numbers are reasonable.

2. How many (what range of) floors does a person need to travel in order for using the elevator to take less time than the stairs?

To evaluate this problem, we will model a single day in Benedum using our most efficient elevator algorithm determined in problem one.  For each user in the system, we will model how long it would take them to walk from their starting floor to destination.  We will then export to a csv file the number of floors traveled, the time it took them to travel through the system using the elevator and the walking time.  We will conduct at least 25 trials, more trials if time allows.  In a separate script, we will read in the csv files and determine the percentage of journeys for each number of floors traveled where the walking travel time was less than the elevator travel time.  We will output a report with that percentage where walking more more time efficient at least half of the time.
VALIDATION

3. When is the best day/time to try to use the elevators (lowest traffic/wait times)?

To evaluate this problem, we will model a week in Benedum using our most efficient elevator algorithm determined in problem one.  For each journey through the system, we will record the start time, the maximum number of people who shared an elevator during this journey and the wait time for an elevator to arrive.  We will export that data into a csv file.  In a separate script we will read in the data and determine the average number of max elevator passengers and average wait time for fifteen minute blocks of time.
ANALYSIS + VALIDATION

4. How is wait time related to floor origin/destination?
	
To evaluate this problem, we will model a single day in Benedum using our most efficient algorithm as determined in problem one. For floor, we will keep track of how long a person must wait on that floor in order to gain access to an elevator. We will export this data to a .csv file and analyze the averages for each floor over each run. 
	For the null hypothesis, we expect the wait times to be the same for each floor. We will run a t-test for each floor (total average across all trials) and compare it against the observed average of the entire system as well as the standards listed in the Design standards we found. For validation, we will make sure that there is no starvation (no person waits infinitely or no person stays on the elevator forever). 

# Work Plan
an initial assignment of who will do what by when. It’s fine if your work plan changes later on, depending on progress (Project end date is 4/29).

* 3/22 - Finish proposal
* 3/28 - Finishing physical data collection
    - 9:30-10:30 Lauren, Alec, Data collection Benedum
    - 1:00-2:00PM - Terry and Cory collection Benedum
    - Walking Stairs timing (any)
* 4/4 - Finish building components of simulation 
    - Elevator
    - Person
    - Floor Queues
    - FEL
    - Unit Testing - PyUnit
* 4/11 - Elevator Algorithms Implemented, run experiments
* 4/18 - Write Code to Analyze Experimental Results, re-run experiments if* necessary
* 4/25 - Report Written and Checked
* 4/29 - Project due (Presentation) (Profit)


# References/Useful Resources

* http://www.facmgmt.pitt.edu/designm/DIVISION-H.pdf
* http://www.tinyepiphany.com/2009/12/elevator-algorithms.html
* http://www.columbia.edu/~cs2035/courses/ieor4405.S13/p14.pdf

