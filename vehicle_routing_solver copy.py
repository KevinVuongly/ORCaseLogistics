# Vehicle Routing

from InstanceVerolog2019 import InstanceVerolog2019
import itertools
from numpy import random

INSTANCE = 2
TEST_FILE = False

SEED = 18319894

# InstanceVerolog2019
#  Dataset, Name
#  Days, TruckCapacity, TruckMaxDistance
#  TruckDistanceCost, TruckDayCost, TruckCost, TechnicianDistanceCost, TechnicianDayCost, TechnicianCost

# Machines, Requests, Locations, Technicians

# Machine    - ID, size, idlePenalty
# Request    - ID, customerLocID, fromDay, toDay, machineID, amount
# Location   - ID, X, Y
# Technician - ID, locationID, maxDayDistance, maxNrInstallations, capabilities

# ReadDistance
# calcDistance
    

##############
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
#
# Sort requests with on top the ones that are least flexible (technicians)
# Sort technicians with on top the ones that are least flexible
#
# Step 1: assign requests to technicians, distribute equally (switching if needed)
# Step 2: assign days to requests, start with the ones that are least flexible (time window)
#         as late as possible, restrictions: technician days off, technician max day distance
#
# step 3: assign request to delivery days, distribute as equally as possible
# step 4: assign request to truck routes
#
# step 5: calculate total costs
#
# improve
#
# subproblem is Travelers Salesmen Problem
##############


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
            self.NumberOfTrucks = 0
            self.TruckRoutes = []
            self.NumberOfTechnicians = 0
            self.TechnicianRoutes = []

    class TechnicianDaySchedule:
        def __init__(self, technician, day):
            self.Technician = technician
            self.Day = day
            self.Distance = 0
            self.RequestIDs = []
        
    def __init__(self, instance):
        self.Instance = instance

        self.Days = [ self.Day(i + 1) for i in range(instance.Days) ]

        self.RequestDeliveryDays = {}
        self.RequestInstallmentDays = {}

        for request in instance.Requests:
            self.RequestDeliveryDays[request.ID] = 0
            self.RequestInstallmentDays[request.ID] = 0
       
        instance.calculateDistances()
        
        self.solve()


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

    def getTechnician(self, ID):
        for technician in self.Instance.Technicians:
            if ID == technician.ID:
                return technician
        return False
    
    def calculateCosts(self):
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
                for requestID in route.RequestIDs:
                    if requestID == 0:    # 0 is not a requestID, but it means that the truck goes back to the depot
                        destination = 1   # 1 is the locationID of the depot
                    else:
                        self.RequestDeliveryDays[requestID] = day.DayNumber
                        destination = self.getRequest(requestID).customerLocID
                    self.TruckDistance += self.Instance.calcDistance[start - 1][destination - 1]
                    start = destination

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

        self.NumberOfTechniciansUsed = len(self.TechniciansUsed)

        self.IdleMachineCosts = 0
        for request in self.Instance.Requests:
            if self.RequestInstallmentDays[request.ID] > self.RequestDeliveryDays[request.ID] and self.RequestDeliveryDays[request.ID] > 0:
                machineID = request.machineID
                idleTime = self.RequestInstallmentDays[request.ID] - self.RequestDeliveryDays[request.ID] - 1
                idlePenalty = self.getMachine(machineID).idlePenalty
                self.IdleMachineCosts += idleTime * idlePenalty

        self.TotalCost = self.Instance.TruckDistanceCost * self.TruckDistance \
                       + self.Instance.TruckDayCost * self.NumberOfTruckDays \
                       + self.Instance.TruckCost * self.NumberOfTrucksUsed \
                       + self.Instance.TechnicianDistanceCost * self.TechnicianDistance \
                       + self.Instance.TechnicianDayCost * self.NumberOfTechnicianDays \
                       + self.Instance.TechnicianCost * self.NumberOfTechniciansUsed \
                       + self.IdleMachineCosts          

    def matches(self):
        self.RequestMatches = {}
        self.TechnicianMatches = {}
        self.CommonDeliveryDays = {}

        for technician in self.Instance.Technicians:
            self.TechnicianMatches[technician.ID] = []

        for request in self.Instance.Requests:
            self.RequestMatches[request.ID] = []
            shuffled = self.Instance.Technicians.copy()
            random.shuffle(shuffled)
            for technician in shuffled:
                if technician.capabilities[request.machineID - 1]:
                    distance = self.Instance.calcDistance[request.customerLocID - 1][technician.locationID - 1]
                    i = 0
                    if 2 * distance <= technician.maxDayDistance:
                        for tech, dist in self.RequestMatches[request.ID]:
                            if distance > dist:
                                i += 1
                            else:
                                break
                        self.RequestMatches[request.ID].insert(i, (technician.ID, distance))
                        
                        for req, dist in self.TechnicianMatches[technician.ID]:
                            if distance > dist:
                                i += 1
                            else:
                                break
                        self.TechnicianMatches[technician.ID].insert(i, (request.ID, distance))
        
            self.CommonDeliveryDays[request.ID] = {}
            for other_request in self.Instance.Requests:
                if request != other_request:
                    commonDays = range(max(request.fromDay, other_request.fromDay), 1 + min(request.toDay, other_request.toDay))
                    if len(commonDays) > 0:
                        self.CommonDeliveryDays[request.ID][other_request.ID] = commonDays
                    else:
                        minimimIdleTime = max(request.fromDay, other_request.fromDay) - min(request.toDay, other_request.toDay)
                        self.CommonDeliveryDays[request.ID][other_request.ID] = minimimIdleTime


#        for request in self.Instance.Requests:
#            print(request.ID, end = ' - ')
#            for technician, distance in self.RequestMatches[request.ID]:
#                print((technician.ID, distance), end = ' ')
#            print()
#            
#        print()
#        for technician in self.Instance.Technicians:
#            print(technician.ID, end = ' - ')
#            for requestID, distance in self.TechnicianMatches[technician.ID]:
#                print((requestID, distance), end = ' ')
#            print()
#        
#        
#        print()
#        for i in range(10):
#            print(i + 1, end = ' - ')
#            for j in range(10):
#                if max(i, j) < len(self.Instance.Requests) and i != j:
#                    print(self.CommonDeliveryDays[i + 1][j + 1], end = ' ')
#            print()
            

    def progress(self):
        print('Request  Delivery  Installment  Idle time')
        for request in self.Instance.Requests:
            idleTime = 0
            if self.RequestInstallmentDays[request.ID] > self.RequestDeliveryDays[request.ID] and self.RequestDeliveryDays[request.ID] > 0:
                idleTime = self.RequestInstallmentDays[request.ID] - self.RequestDeliveryDays[request.ID] - 1
            print('%6d  %8d  %11d  %9d' % (request.ID, self.RequestDeliveryDays[request.ID], self.RequestInstallmentDays[request.ID], idleTime))


    def assignRequestsToTechnicians(self):
        self.assignments = {}   # assigns requests to technicians

        for technician in self.Instance.Technicians:
            self.assignments[technician.ID] = set()
            
        for request in self.Instance.Requests:
            technicianID, distance = self.RequestMatches[request.ID][0]
            self.assignments[technicianID].add(request)
    
    def bestRoute(self, home, locations):
        # has to be changed if number of locations is large
        bestDistance = 40000    # around the earth
        bestRoute = ()
        checkedRoutes = []
        for permutation in itertools.permutations(locations):
            if permutation[::-1] not in checkedRoutes:
                distance = 0
                start = home
                for destination in permutation:
                    distance += self.Instance.calcDistance[start - 1][destination - 1]
                    start = destination
                distance += self.Instance.calcDistance[start - 1][home - 1]
                if distance < bestDistance:
                    bestDistance = distance
                    bestRoute = permutation
                checkedRoutes.append(permutation)
        return bestRoute, bestDistance
    
    def scheduleCosts(self, schedule):
        costs = 0
        technicianUsed = False
        for day in range(2, 1 + self.Instance.Days):
            if len(schedule[day].RequestIDs) > 0:
                technicianUsed = True
                costs += self.Instance.TechnicianDayCost
                costs += self.Instance.TechnicianDistanceCost * schedule[day].Distance
                for requestID in schedule[day].RequestIDs:
                    request = self.getRequest(requestID)
                    if day > request.toDay + 1:
                        idleDays = request.toDay + 1 - day
                        costs += idleDays * self.getMachine(request.machineID).idlePenalty * request.amount
        if technicianUsed:
            costs += self.Instance.TechnicianCost
        return costs
    
    def checkSchedule(self, schedule, technician):
        missing = []
        double = []
        for request in self.assignments[technician.ID]:
            count = 0
            for day in range(2, 1 + self.Instance.Days):
                if request.ID in schedule[day].RequestIDs:
                    count += 1
                    if count > 1:
                        double.append(request)
            if count == 0:
                missing.append(request)
        return double, missing
    
    def removeFromSchedule(self, schedule, request):
        bestCosts = self.scheduleCosts(schedule)
        for day in range(2, 1 + self.Instance.Days):
            if request.ID in schedule[day].RequestIDs:
                # remove request from day, calculate costs and add request back to the day
                oldDistance = schedule[day].Distance
                schedule[day].RequestIDs.remove(request.ID)
                locations = set()
                for requestID in schedule[day].RequestIDs:
                    locations.add(self.getRequest(requestID).customerLocID)
                route, distance = self.bestRoute(schedule[day].Technician.locationID, locations)
                schedule[day].Distance = distance
                costs = self.scheduleCosts(schedule)
                if costs <= bestCosts:
                    bestCosts = costs
                    removeRequestFromDay = day
                    newDistance = distance
                schedule[day].RequestIDs.append(request.ID)
                schedule[day].Distance = oldDistance
        schedule[removeRequestFromDay].RequestIDs.remove(request.ID)
        schedule[removeRequestFromDay].Distance = newDistance
                
    def addToSchedule(self, schedule, request):
        bestCosts = -1
        for day in range(request.fromDay + 1, 1 + self.Instance.Days):
            if len(schedule[day].RequestIDs) < schedule[day].Technician.maxNrInstallations:
                # add request to day, calculate costs and remove request from the day
                schedule[day].RequestIDs.append(request.ID)
                locations = set()
                for requestID in schedule[day].RequestIDs:
                    locations.add(self.getRequest(requestID).customerLocID)
                route, distance = self.bestRoute(schedule[day].Technician.locationID, locations)
                if distance <= schedule[day].Technician.maxDayDistance:
                    oldDistance = schedule[day].Distance
                    schedule[day].Distance = distance
                    costs = self.scheduleCosts(schedule)
                    if bestCosts < 0 or costs <= bestCosts:
                        bestCosts = costs
                        addRequestToDay = day
                        newDistance = distance
                        bestRoute = route
                    schedule[day].Distance = oldDistance
                schedule[day].RequestIDs.remove(request.ID)
            
        schedule[addRequestToDay].RequestIDs.append(request.ID)
        requestIDs = []
        for location in bestRoute:
            for requestID in schedule[addRequestToDay].RequestIDs:
                req = self.getRequest(requestID)
                if req.customerLocID == location:
                    requestIDs.append(req.ID)
        schedule[addRequestToDay].RequestIDs = requestIDs
        schedule[addRequestToDay].Distance = newDistance
        
    
    def makeTechnicianDaySchedules(self):
        self.TechnicianDaySchedules = {}
        days = range(2, 1 + self.Instance.Days)
        for technician in self.Instance.Technicians:
            schedule = {}
            for day in days:
                # requests onthouden in schedule of alleen de IDs, wat is beter?
                requests = []
                requestIDs = []
                for request in self.assignments[technician.ID]:
                    if request.fromDay + 1 <= day <= request.toDay + 1:
                        requests.append(request)
                if len(requests) <= technician.maxNrInstallations:
                    locations = set()
                    for request in requests:
                        locations.add(request.customerLocID)
                    route, distance = self.bestRoute(technician.locationID, locations)
                    if distance <= technician.maxDayDistance:
                        for location in route:
                            for request in requests:
                                if request.customerLocID == location:
                                    requestIDs.append(request.ID)
                    else:
                        distance = 0
                daySchedule = self.TechnicianDaySchedule(technician, day)
                daySchedule.RequestIDs = requestIDs
                daySchedule.Distance = distance
                schedule[day] = daySchedule
                if day > 2 and set(schedule[day - 1].RequestIDs).issubset(set(requestIDs)):
                    schedule[day - 1].RequestIDs = []
                    schedule[day - 1].Distance = 0
                    
            double, missing = self.checkSchedule(schedule, technician)
            for request in double:
                self.removeFromSchedule(schedule, request)
            for request in missing:
                self.addToSchedule(schedule, request)

            for day in days:
                if len(schedule[day].RequestIDs) > 0:
                    technicianRoute = self.TechnicianRoute(technician.ID)
                    technicianRoute.RequestIDs = schedule[day].RequestIDs
                    self.Days[day - 1].TechnicianRoutes.append(technicianRoute)
                    print(technician.ID, day, schedule[day].RequestIDs, schedule[day].Distance)
                
            print('Costs: %d' % self.scheduleCosts(schedule))
            self.TechnicianDaySchedules[technician.ID] = schedule
            
    
    def solve(self):
        self.matches()
        self.assignRequestsToTechnicians()
        self.makeTechnicianDaySchedules()
        
        self.calculateCosts()

if __name__ == "__main__":    
    random.seed(SEED)

    if TEST_FILE:
        instance_file = 'data/STUDENT%03d.txt' % INSTANCE
        output_file = 'solution/STUDENT%03d-solution.txt' % INSTANCE
    else:
        instance_file = 'VSC2019_ORTEC_early_%02d.txt' % INSTANCE
        output_file = instance_file.replace('.txt', '-solution.txt')
        
    problem = InstanceVerolog2019(instance_file)
    solution = Solution(problem)
    solution.writeSolution(output_file)
    