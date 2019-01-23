# Vehicle Routing

from InstanceCreator import InstanceCreator
from queue import PriorityQueue

""" TO VALIDATE, USE python SolutionVerolog2019.py -i data/STUDENT002.txt –s solution/STUDENT002-solution.txt """
# Restrictions

# All requests must be delivered
# All requests must be installed
# Each installment has to be after delivery
# Max capacity of truck may not be exceeded
# Max distance of truck may not be exceeded
# Max distance for each technician
# Max number of installments for each technician
# Technician can only handle certain machines
# Technicians need two days off after 5 days of working
# Technicians need one day off after 4 days of working

# Sort requests with on top the ones that are least flexible (technicians)
# Sort technicians with on top the ones that are least flexible

# Step 1: assign requests to technicians, distribute equally (switching if needed)
# Step 2: assign days to requests, start with the ones that are least flexible (time window)
#         as late as possible, restrictions: technician days off, technician max day distance

# step 3: assign request to delivery days, distribute as equally as possible
# step 4: assign request to truck routes

# step 5: calculate total costs

# improve

# subproblem is Travelers Salesmen Problem


class Solution:
    class TruckRoute:
        def __init__(self, ID):
            self.TruckID = ID
            self.RequestIDs = []

        def __repr__(self):
            return '%d %s' % (self.TruckID, ' '.join(map(str, self.RequestIDs)))

    class TechnicianRoute:
        def __init__(self, ID):
            self.TechnicianID = ID
            self.RequestIDs = []

        def __repr__(self):
            return '%d %s' % (self.TechnicianID, ' '.join(map(str, self.RequestIDs)))

    class Day:
        def __init__(self, dayNumber):
            self.DayNumber = dayNumber
            self.TruckRoutes = []
            self.NumberOfTechnicians = 0
            self.TechnicianRoutes = []

    def __init__(self, instance):
        self.Instance = instance

        self.Days = []
        for i in range(self.Instance.Days):
            self.Days.append(self.Day(i + 1))

        self.RequestDeliveryDays = {}
        self.RequestInstallmentDays = {}

        for request in self.Instance.Requests:
            self.RequestDeliveryDays[request.ID] = 0
            self.RequestInstallmentDays[request.ID] = 0

        self.depot = 1

        self.numberOfTrucks = [0 for days in range(self.Instance.Days)]
        self.capacityUsedTrucks = [[] for days in range(self.Instance.Days)]
        self.distanceMadeTrucks = [[] for days in range(self.Instance.Days)]
        self.currentLocationTrucks = [[] for days in range(self.Instance.Days)]

        self.distanceMadeTechnicians = [[0 for maxTechnicians in range(len(self.Instance.Technicians))] for days in range(self.Instance.Days)]
        self.currentLocationTechnicians = [[self.Instance.Technicians[Technician].locationID for Technician in range(len(self.Instance.Technicians))] for days in range(self.Instance.Days)]
        self.numberOfInstallationsTechnicians = [[0 for maxTechnicians in range(len(self.Instance.Technicians))] for days in range(self.Instance.Days)]

    def writeSolution(self, filename):
        try:
            file = open(filename, 'w')
            file.write('DATASET = %s\n' % self.Instance.Dataset)
            file.write('NAME = %s\n' % self.Instance.Name)
            file.write('\n')
            file.write('TRUCK_DISTANCE = %d\n' % self.TruckDistance)
            file.write('NUMBER_OF_TRUCK_DAYS = %d\n' % self.NumberOfTruckDays)
            file.write('NUMBER_OF_TRUCKS_USED = %d\n' % self.NumberOfTrucksUsed)
            file.write('TECHNICIAN_DISTANCE = %d\n' % self.TechnicianDistance)
            file.write('NUMBER_OF_TECHNICIAN_DAYS = %d\n' % self.NumberOfTechnicianDays)
            file.write('NUMBER_OF_TECHNICIANS_USED = %d\n' % self.NumberOfTechniciansUsed)
            file.write('IDLE_MACHINE_COSTS = %d\n' % self.IdleMachineCosts)
            file.write('TOTAL_COST = %d\n' % self.TotalCost)

            numbers = range(1, len(self.Days) + 1)
            for i, day in zip(numbers, self.Days):
                file.write('\n')
                file.write('DAY = %d\n' % i)
                file.write('NUMBER_OF_TRUCKS = %d\n' % len(day.TruckRoutes))
                for route in day.TruckRoutes:
                    file.write('%s\n' % route)
                file.write('NUMBER_OF_TECHNICIANS = %d\n' % len(day.TechnicianRoutes))
                for route in day.TechnicianRoutes:
                    file.write('%s\n' % route)


        except IOError:
            print('Error opening %s' %filename)

    def getMachine(self, ID):
        for machine in self.Instance.Machines:
            if ID == machine.ID:
                return machine
        return False

    def getRequest(self, ID):
        for request in self.Instance.Requests:
            if ID == request.ID:
                return request
        return False

    def calculate(self):
        self.TruckDistance = 0
        self.NumberOfTruckDays = 0
        self.NumberOfTrucksUsed = 0
        self.NumberOfTechnicianDays = 0

        self.TechnicianDistance = 0
        self.TechniciansUsed = set()

        for day in self.Days:
            day.numberOfTrucks = len(day.TruckRoutes)
            self.NumberOfTruckDays += day.numberOfTrucks
            if day.numberOfTrucks > self.NumberOfTrucksUsed:
                self.NumberOfTrucksUsed = day.numberOfTrucks

            for route in day.TruckRoutes:
                start = 1
                route.RequestIDs.append(0)
                for requestID in route.RequestIDs:
                    if requestID == 0:    # 0 is not a requestID, but it means that the truck goes back to the depot
                        destination = 1   # 1 is the locationID of the depot
                    else:
                        self.RequestDeliveryDays[requestID] = day.DayNumber
                        destination = self.getRequest(requestID).customerLocID
                    self.TruckDistance += self.Instance.calcDistance[start - 1][destination - 1]
                    start = destination
                route.RequestIDs.pop()

            day.numberOfTechnicians = len(day.TechnicianRoutes)     # one technician does only one route per day max
            self.NumberOfTechnicianDays += day.numberOfTechnicians
            for route in day.TechnicianRoutes:
                self.TechniciansUsed.add(route.TechnicianID)
                start = self.Instance.Technicians[route.TechnicianID - 1].locationID
                for requestID in route.RequestIDs:
                    self.RequestInstallmentDays[requestID] = day.DayNumber
                    destination = self.getRequest(requestID).customerLocID
                    self.TechnicianDistance += self.Instance.calcDistance[start - 1][destination - 1]
                    start = destination
                # head home
                home = self.Instance.Technicians[route.TechnicianID - 1].locationID
                self.TechnicianDistance += self.Instance.calcDistance[start - 1][home - 1]

        self.NumberOfTechniciansUsed = len(self.TechniciansUsed)

        self.IdleMachineCosts = 0
        for request in self.Instance.Requests:
            if self.RequestInstallmentDays[request.ID] > self.RequestDeliveryDays[request.ID] and self.RequestDeliveryDays[request.ID] > 0:
                machineID = request.machineID
                idleTime = self.RequestInstallmentDays[request.ID] - self.RequestDeliveryDays[request.ID] - 1
                idlePenalty = self.getMachine(machineID).idlePenalty
                self.IdleMachineCosts += idleTime * idlePenalty * request.amount

        self.TotalCost = self.Instance.TruckDistanceCost * self.TruckDistance \
                       + self.Instance.TruckDayCost * self.NumberOfTruckDays \
                       + self.Instance.TruckCost * self.NumberOfTrucksUsed \
                       + self.Instance.TechnicianDistanceCost * self.TechnicianDistance \
                       + self.Instance.TechnicianDayCost * self.NumberOfTechnicianDays \
                       + self.Instance.TechnicianCost * self.NumberOfTechniciansUsed \
                       + self.IdleMachineCosts

    def matchesTrucks(self, day):
        self.shortestPath = PriorityQueue()

        for request in self.Instance.Requests:
            if request.shipped == False and request.fromDay <= day <= request.toDay:
                for truck in self.Days[day - 1].TruckRoutes:
                    currentLocationTruck = self.currentLocationTrucks[day - 1][truck.TruckID - 1]

                    if self.distanceMadeTrucks[day - 1][truck.TruckID - 1] + \
                    self.Instance.calcDistance[currentLocationTruck - 1][request.customerLocID - 1] + \
                    self.Instance.calcDistance[request.customerLocID - 1][self.depot - 1] <= self.Instance.TruckMaxDistance \
                    and self.capacityUsedTrucks[day - 1][truck.TruckID - 1] + request.amount * self.getMachine(request.machineID).size \
                    <= self.Instance.TruckCapacity:

                        distance = self.Instance.calcDistance[currentLocationTruck - 1][request.customerLocID - 1]
                        volume = request.amount * self.getMachine(request.machineID).size
                        self.shortestPath.put((distance - volume + request.ID, [distance, volume, truck.TruckID, request]))

        if self.shortestPath.empty():
            return False
        else:
            return True

    def assignTrucks(self, day, maxTrucks):
        """
        Assign requests to trucks on given day
        """

        # assign request to very first truck
        noTrucksQueue = PriorityQueue()

        for request in self.Instance.Requests:
            if request.fromDay <= day <= request.toDay:
                if request.shipped == False:

                    dist = self.Instance.calcDistance[self.depot - 1][request.customerLocID - 1]
                    vol = request.amount * self.getMachine(request.machineID).size
                    noTrucksQueue.put((dist - vol + request.ID, [dist, vol, request]))

        requestToDo = noTrucksQueue.qsize()

        if requestToDo > 0:
            [score, [distance, volume, request]] = list(noTrucksQueue.get())
            self.numberOfTrucks[day - 1] += 1
            truckID = self.numberOfTrucks[day - 1]
            self.Days[day - 1].TruckRoutes.append(self.TruckRoute(truckID))
            self.Days[day - 1].TruckRoutes[truckID - 1].RequestIDs.append(request.ID)

            self.capacityUsedTrucks[day - 1].append(volume)
            self.distanceMadeTrucks[day - 1].append(distance)
            self.currentLocationTrucks[day - 1].append(request.customerLocID)

            request.shipped = True
            requestToDo -= 1

        while requestToDo > 0:

            matches = self.matchesTrucks(day)

            # assign request to an existing truck
            if matches:

                [score, [distance, volume, truckID, request]] = list(self.shortestPath.get())

                self.Days[day - 1].TruckRoutes[truckID - 1].RequestIDs.append(request.ID)

                self.capacityUsedTrucks[day - 1][truckID - 1] += volume
                self.distanceMadeTrucks[day - 1][truckID - 1] += distance
                self.currentLocationTrucks[day - 1][truckID - 1] = request.customerLocID

                request.shipped = True
                requestToDo -= 1

            # assign request to a new truck if possible e.g. less than maximum number of trucks given
            else:
                if self.numberOfTrucks[day - 1] < maxTrucks:

                    while request.shipped == True:
                        [score, [distance, volume, request]] = list(noTrucksQueue.get())

                    self.numberOfTrucks[day - 1] += 1
                    truckID = self.numberOfTrucks[day - 1]
                    self.Days[day - 1].TruckRoutes.append(self.TruckRoute(truckID))
                    self.Days[day - 1].TruckRoutes[truckID - 1].RequestIDs.append(request.ID)

                    self.capacityUsedTrucks[day - 1].append(volume)
                    self.distanceMadeTrucks[day - 1].append(distance)
                    self.currentLocationTrucks[day - 1].append(request.customerLocID)

                    request.shipped = True
                    requestToDo -= 1
                else:
                    break

    def matchesTechnician(self, day):
        self.TechnicianMatches = {}

        for technician in self.Instance.Technicians:
            if technician.used:
                self.TechnicianMatches[technician] = PriorityQueue()

        for technician in self.Instance.Technicians:
            for request in self.Instance.Requests:
                if request.delivered and request.installed == False:
                    if technician.forcedBreak == 0 and technician.used:
                        if technician.capabilities[request.machineID - 1]:
                            currentLocationTechnician = self.currentLocationTechnicians[day - 1][technician.ID - 1]

                            if self.numberOfInstallationsTechnicians[day - 1][technician.ID - 1] < technician.maxNrInstallations \
                            and self.distanceMadeTechnicians[day - 1][technician.ID - 1] + \
                            self.Instance.calcDistance[currentLocationTechnician - 1][request.customerLocID - 1] + \
                            self.Instance.calcDistance[request.customerLocID - 1][technician.locationID - 1] \
                            <= technician.maxDayDistance:
                                distance = self.Instance.calcDistance[currentLocationTechnician - 1][request.customerLocID - 1]
                                score = distance - self.distanceMadeTechnicians[day - 1][technician.ID - 1] - 0.001 * request.ID
                                self.TechnicianMatches[technician].put((score, [distance, request]))

        noMatches = [technician for technician, matches in self.TechnicianMatches.items() if matches.empty()]
        for technician in noMatches:
            del self.TechnicianMatches[technician]

        if not self.TechnicianMatches:
            return False

        self.greedyTechnicianMatch = PriorityQueue()
        for technician, matches in self.TechnicianMatches.items():
            [score, [distance, request]] = list(matches.get())

            self.greedyTechnicianMatch.put((score, [distance, technician, request]))

        return True

    def assignTechnicians(self, day):
        """
        Assign requests to technicians on given day
        """

        # the total distance of a technician to all unassigned request(used as heuristic!!)
        self.totalDistance = {}
        for technician in self.Instance.Technicians:
            self.totalDistance[technician] = 0

        for technician in self.Instance.Technicians:
            for request in self.Instance.Requests:
                if request.delivered and request.installed == False:
                    self.totalDistance[technician] += self.Instance.calcDistance[technician.locationID - 1][request.customerLocID - 1]

        # initialize dict of working technicians on given day
        workingTechnicians = {}

        # calculate amount of requests to install
        requestsToInstall = 0
        for request in self.Instance.Requests:
            if request.delivered and request.installed == False:
                requestsToInstall += 1

        # remember for all technicians if they have worked yesterday
        for technician in self.Instance.Technicians:
            if technician.workedToday:
                technician.workedYesterday = True
                technician.workedToday = False
            else:
                technician.workedYesterday = False
                technician.consecutiveDays = 0

        if requestsToInstall > 0:
            # assign very first request of the day to a technician

            self.closestRequest = PriorityQueue()
            for technician in self.Instance.Technicians:
                for request in self.Instance.Requests:
                    # try to assign first request to a technician that has worked earlier before
                    if technician.used and technician.forcedBreak == 0 and technician.capabilities[request.machineID - 1] and request.delivered and request.installed == False:
                        dist = self.Instance.calcDistance[technician.locationID - 1][request.customerLocID - 1]
                        score = self.totalDistance[technician] + dist - technician.maxDayDistance - 0.001 * request.ID
                        self.closestRequest.put((score, [dist, technician, request]))

            # not a single technician has worked before
            if self.closestRequest.empty():

                self.firstRequest = PriorityQueue()

                for technician in self.Instance.Technicians:
                    for request in self.Instance.Requests:
                        if technician.capabilities[request.machineID - 1] and request.delivered and request.installed == False:
                            dist = self.Instance.calcDistance[technician.locationID - 1][request.customerLocID - 1]
                            score = self.totalDistance[technician] + dist - technician.maxDayDistance - 0.001 * request.ID
                            self.firstRequest.put((score, [dist, technician, request]))

                [score, [distance, technician, request]] = list(self.firstRequest.get())

            # assign first request to a technician that has worked before
            else:
                [score, [distance, technician, request]] = list(self.closestRequest.get())

            if technician.workedToday == False:
                technician.workedToday = True
                technician.consecutiveDays += 1
                technician.used = True

            self.distanceMadeTechnicians[day - 1][technician.ID - 1] += distance
            self.currentLocationTechnicians[day - 1][technician.ID - 1] = request.customerLocID
            self.numberOfInstallationsTechnicians[day - 1][technician.ID - 1] += 1
            problem.Requests[request.ID - 1].installed = True
            requestsToInstall -= 1

            if technician.ID not in workingTechnicians:
                workingTechnicians[technician.ID] = [request.ID]
            else:
                workingTechnicians[technician.ID].append(request.ID)

            """
            Assign rest of the requests on given day
            """

            while requestsToInstall > 0:
                matches = self.matchesTechnician(day)

                # assign request to a technician that has worked before
                if matches:
                    [score, [distance, technician, request]] = list(self.greedyTechnicianMatch.get())

                # assign request to a new technician
                else:
                    self.assignNewTechnician = PriorityQueue()

                    for technician in self.Instance.Technicians:
                        for request in self.Instance.Requests:
                            if technician.used == False and technician.capabilities[request.machineID - 1] and request.delivered and request.installed == False:
                                dist = self.Instance.calcDistance[technician.locationID - 1][request.customerLocID - 1]
                                score = dist - technician.maxDayDistance - 0.001 * request.ID
                                self.assignNewTechnician.put((score, [dist, technician, request]))
                    if self.assignNewTechnician.qsize() > 0:
                        [score, [distance, technician, request]] = list(self.assignNewTechnician.get())
                        technician.used = True
                    else:
                        break

                if technician.workedToday == False:
                    technician.workedToday = True
                    technician.consecutiveDays += 1
                    technician.used = True

                self.distanceMadeTechnicians[day - 1][technician.ID - 1] += distance
                self.currentLocationTechnicians[day - 1][technician.ID - 1] = request.customerLocID
                self.numberOfInstallationsTechnicians[day - 1][technician.ID - 1] += 1
                problem.Requests[request.ID - 1].installed = True
                requestsToInstall -= 1

                if technician.ID not in workingTechnicians:
                    workingTechnicians[technician.ID] = [request.ID]
                else:
                    workingTechnicians[technician.ID].append(request.ID)

            # add routes of working technicians to the given day
            for key, value in sorted(workingTechnicians.items()):
                self.Days[day - 1].TechnicianRoutes.append(self.TechnicianRoute(key))
                for request in value:
                    self.Days[day - 1].TechnicianRoutes[-1].RequestIDs.append(request)

        # set shipped requests to delivered for the following day
        for request in self.Instance.Requests:
            if problem.Requests[request.ID - 1].shipped == True:
                problem.Requests[request.ID - 1].delivered = True


        # force technician a break of 2 days if they have worked for 5 consecutive days
        for technician in self.Instance.Technicians:
            if technician.forcedBreak > 0:
                technician.forcedBreak -= 1

            if technician.consecutiveDays == 5:
                technician.forcedBreak = 2
                technician.consecutiveDays = 0


    def progress(self):
        print('Request  Delivery  Installment  Idle time')
        for request in self.Instance.Requests:
            idleTime = 0
            if self.RequestInstallmentDays[request.ID] > self.RequestDeliveryDays[request.ID] and self.RequestDeliveryDays[request.ID] > 0:
                idleTime = self.RequestInstallmentDays[request.ID] - self.RequestDeliveryDays[request.ID] - 1
            print('%6d  %8d  %11d  %9d' % (request.ID, self.RequestDeliveryDays[request.ID], self.RequestInstallmentDays[request.ID], idleTime))

def main():
    global problem, solution
    if official == "Y":
        instance_file = 'data/VSC2019_ORTEC_early_%02d.txt' % INSTANCE
        output_file = 'solution/VSC2019_ORTEC_early_%02d-solution.txt' % INSTANCE
    else:
        instance_file = 'data/STUDENT%03d.txt' % INSTANCE
        output_file = 'solution/STUDENT%03d-solution.txt' % INSTANCE

    # InstanceVerolog2019
    #  Dataset, Name
    #  Days, TruckCapacity, TruckMaxDistance
    #  TruckDistanceCost, TruckDayCost, TruckCost, TechnicianDistanceCost, TechnicianDayCost, TechnicianCost

    # Machines, Requests, Locations, Technicians

    # Machine    - ID, size, idlePenalty
    # Request    - ID, customerLocID, fromDay, toDay, machineID, amount
    # Location   - ID, X, Y
    # Technician - ID, locationID, maxDayDistance, maxNrInstallation, capabilities

    # ReadDistance
    # calcDistance

    """
    Start of algorithm
    """
    maxTrucks = 1
    feasible = False

    while feasible == False:
        installedRequests = 0

        problem = InstanceCreator(instance_file)
        problem.calculateDistances()
        solution = Solution(problem)

        for day in range(1, solution.Instance.Days + 1):
            solution.assignTrucks(day, maxTrucks)
            solution.assignTechnicians(day)

        for request in solution.Instance.Requests:
            if request.installed == False:
                maxTrucks += 1
                break
            else:
                installedRequests += 1

        if installedRequests == len(solution.Instance.Requests):
            feasible = True

    solution.calculate()
    solution.writeSolution(output_file)

if __name__ == "__main__":
    INSTANCE = int(input("which instance? "))
    official = input("Official data?(Y/N) ")
    main()
