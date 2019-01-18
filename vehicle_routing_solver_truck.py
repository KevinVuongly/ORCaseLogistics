# Vehicle Routing

from InstanceVerolog2019 import InstanceVerolog2019
import itertools
from numpy import random

INSTANCE = 25
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
        def __init__(self, ID, day):
            self.TruckID = ID
            self.Day = day
            self.RequestIDs = []
            self.Distance = 0
            self.Volume = 0
            
        def __repr__(self):
            return '%d %s' % (self.TruckID, ' '.join(map(str, self.RequestIDs)))

    class TechnicianRoute:
        def __init__(self, ID):
            self.TechnicianID = ID
            self.RequestIDs = []

        def __repr__(self):
            return '%d %s' % (self.TechnicianID, ' '.join(map(str, self.RequestIDs)))

    class DaySchedule:
        def __init__(self, day):
            self.Day = day
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
            
    class Truck:
        def __init__(self, ID):
            self.ID = ID
            self.TruckRoutes = {}    # key is day number, value is a TruckRoute
        
    def __init__(self, instance):
        self.Instance = instance

        self.DaySchedules = [ self.DaySchedule(i + 1) for i in range(instance.Days) ]

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

            for daySchedule in self.DaySchedules:
                file.write('\n')
                file.write('DAY = %d\n' % daySchedule.Day)
                file.write('NUMBER_OF_TRUCKS = %d\n' % len(daySchedule.TruckRoutes))
                for route in daySchedule.TruckRoutes:
                    file.write('%s\n' % route)
                file.write('NUMBER_OF_TECHNICIANS = %d\n' % len(daySchedule.TechnicianRoutes))
                for route in daySchedule.TechnicianRoutes:
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
    
    def getTruck(self, ID):
        for truck in self.Trucks:
            if ID == truck.ID:
                return truck
        return False
    
    def calculateCosts(self):
        self.TruckDistance = 0
        self.NumberOfTruckDays = 0
        self.NumberOfTrucksUsed = 0
        self.NumberOfTechnicianDays = 0

        self.TechnicianDistance = 0
        self.TechniciansUsed = set()

        for daySchedule in self.DaySchedules:
            daySchedule.numberOfTrucks = len(daySchedule.TruckRoutes)
            self.NumberOfTruckDays += daySchedule.numberOfTrucks
            if daySchedule.numberOfTrucks > self.NumberOfTrucksUsed:
                self.NumberOfTrucksUsed = daySchedule.numberOfTrucks

            for route in daySchedule.TruckRoutes:
                start = 1
                home = start
                for requestID in route.RequestIDs:
                    if requestID == 0:    # 0 is not a requestID, but it means that the truck goes back to the depot
                        destination = 1   # 1 is the locationID of the depot
                    else:
                        self.RequestDeliveryDays[requestID] = daySchedule.Day
                        destination = self.getRequest(requestID).customerLocID
                    self.TruckDistance += self.Instance.calcDistance[start - 1][destination - 1]
                    start = destination
                self.TruckDistance += self.Instance.calcDistance[start - 1][home - 1]

            daySchedule.numberOfTechnicians = len(daySchedule.TechnicianRoutes)     # one technician does only one route per day max
            self.NumberOfTechnicianDays += daySchedule.numberOfTechnicians
            for route in daySchedule.TechnicianRoutes:
                self.TechniciansUsed.add(route.TechnicianID)
                start = self.Instance.Technicians[route.TechnicianID - 1].locationID
                home = start
                for requestID in route.RequestIDs:
                    self.RequestInstallmentDays[requestID] = daySchedule.Day
                    destination = self.getRequest(requestID).customerLocID
                    self.TechnicianDistance += self.Instance.calcDistance[start - 1][destination - 1]
                    start = destination
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
        
    def matches(self):
        self.RequestMatches = {}
        self.TechnicianMatches = {}
        self.CommonDeliveryDays = {}

        for technician in self.Instance.Technicians:
            self.TechnicianMatches[technician.ID] = []

        for request in self.Instance.Requests:
            self.RequestMatches[request.ID] = []
            shuffled = self.Instance.Technicians.copy()    # Technicians are being shuffled in random order
            random.shuffle(shuffled)
            for technician in shuffled:
                if technician.capabilities[request.machineID - 1]:
                    distance = self.Instance.calcDistance[request.customerLocID - 1][technician.locationID - 1]
                    i = 0
                    if 2 * distance <= technician.maxDayDistance:    # maxDayDistance constraint
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
            

    def overviewRequests(self):
        print('Request  Delivery  Installment  Idle time  Idle penalty  Amount  Idle cost')
        totalIdleCost = 0
        for request in self.Instance.Requests:
            idleTime = 0
            idleCost = 0
            if self.RequestInstallmentDays[request.ID] > self.RequestDeliveryDays[request.ID] and self.RequestDeliveryDays[request.ID] > 0:
                idleTime = self.RequestInstallmentDays[request.ID] - self.RequestDeliveryDays[request.ID] - 1
                idlePenalty = self.getMachine(request.machineID).idlePenalty
                idleCost = idleTime * idlePenalty * request.amount
                totalIdleCost += idleCost
            print('%6d  %8d  %11d  %9d  %12d  %6d  %9d' % (request.ID, self.RequestDeliveryDays[request.ID], self.RequestInstallmentDays[request.ID], idleTime, idlePenalty, request.amount, idleCost))
        print()
        print('Total idle costs', totalIdleCost)

    def assignRequestsToTechnicians(self):
        self.assignments = {}   # assigns requests to technicians

        for technician in self.Instance.Technicians:
            self.assignments[technician.ID] = set()
            
        for request in self.Instance.Requests:
            technicianID, distance = self.RequestMatches[request.ID][0]
            self.assignments[technicianID].add(request)
    
    def findBestRoute(self, home, locations):
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
                position = schedule[day].RequestIDs.index(request.ID)
                schedule[day].RequestIDs.remove(request.ID)
                locations = set()
                for requestID in schedule[day].RequestIDs:
                    locations.add(self.getRequest(requestID).customerLocID)
                route, distance = self.findBestRoute(schedule[day].Technician.locationID, locations)
                schedule[day].Distance = distance
                costs = self.scheduleCosts(schedule)
                if costs <= bestCosts:
                    bestCosts = costs
                    removeRequestFromDay = day
                    newRoute = route
                    newDistance = distance
                schedule[day].RequestIDs.insert(position, request.ID)
                schedule[day].Distance = oldDistance
                
        schedule[removeRequestFromDay].RequestIDs.remove(request.ID)
        requestIDs = []
        for location in newRoute:
            for requestID in schedule[removeRequestFromDay].RequestIDs:
                if self.getRequest(requestID).customerLocID == location:
                    requestIDs.append(requestID)
        schedule[removeRequestFromDay].RequestIDs = requestIDs
        schedule[removeRequestFromDay].Distance = newDistance   
                
    def addToSchedule(self, schedule, request):
        bestCosts = -1
        for day in range(request.fromDay + 1, 1 + self.Instance.Days):
            if len(schedule[day].RequestIDs) < schedule[day].Technician.maxNrInstallations:   # maxNrInstallations constraint
                # add request to day, calculate costs and remove request from the day
                schedule[day].RequestIDs.append(request.ID)
                locations = set()
                for requestID in schedule[day].RequestIDs:
                    locations.add(self.getRequest(requestID).customerLocID)
                route, distance = self.findBestRoute(schedule[day].Technician.locationID, locations)
                if distance <= schedule[day].Technician.maxDayDistance:    # maxDayDistance constraint
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
        
        if bestCosts < 0:
            return False
        
        schedule[addRequestToDay].RequestIDs.append(request.ID)
        requestIDs = []
        for location in bestRoute:
            for requestID in schedule[addRequestToDay].RequestIDs:
                req = self.getRequest(requestID)
                if req.customerLocID == location:
                    requestIDs.append(req.ID)
        schedule[addRequestToDay].RequestIDs = requestIDs
        schedule[addRequestToDay].Distance = newDistance
        return True
        
    
    def makeTechnicianDaySchedules(self):
        failedRequests = []
        self.TechnicianDaySchedules = {}
        self.InstalledOnDay = {}
        
        days = range(2, 1 + self.Instance.Days)
        for technician in self.Instance.Technicians:
            schedule = {}
            restDays = []
            numberOfConsecutiveDaysWorked = 0
            for day in days:
                daySchedule = self.TechnicianDaySchedule(technician, day)
                schedule[day] = daySchedule
                
                if day not in restDays:
                    requests = []    # find request that are assigned to the technician and that can be delivered on the day before
                    requestIDs = []
                    for request in self.assignments[technician.ID]:
                        if request.fromDay + 1 <= day <= request.toDay + 1:
                            requests.append(request)
                    if len(requests) <= technician.maxNrInstallations:   # maxNrInstallations constraint
                        locations = set()
                        for request in requests:
                            locations.add(request.customerLocID)
                        route, distance = self.findBestRoute(technician.locationID, locations)
                        if distance <= technician.maxDayDistance:
                            for location in route:
                                for request in requests:
                                    if request.customerLocID == location:
                                        requestIDs.append(request.ID)
                        else:
                            distance = 0
                    daySchedule.RequestIDs = requestIDs
                    daySchedule.Distance = distance
                    if len(daySchedule.RequestIDs) == 0:
                        numberOfConsecutiveDaysWorked = 0
                    else:
                        numberOfConsecutiveDaysWorked += 1
                        # check if the requests on the day before all fit on today's schedule too
                        if day > 2 and len(schedule[day - 1].RequestIDs) > 0:
                            if set(schedule[day - 1].RequestIDs).issubset(set(requestIDs)):
                                numberOfConsecutiveDaysWorked = 1
                                schedule[day - 1].RequestIDs = []
                                schedule[day - 1].Distance = 0
                            elif set(requestIDs).issubset(set(schedule[day - 1].RequestIDs)):
                                numberOfConsecutiveDaysWorked = 0
                                schedule[day].RequestIDs = []
                                schedule[day].Distance = 0
                        if numberOfConsecutiveDaysWorked == 5:
                            restDays = [ day + 1, day + 2 ]
                    
            double, missing = self.checkSchedule(schedule, technician)
            for request in double:
                self.removeFromSchedule(schedule, request)
            for request in missing:
                if not self.addToSchedule(schedule, request):
                    failedRequests.append(request)
                    print('Failed', request)
            
            double, missing = self.checkSchedule(schedule, technician)
            
            for day in days:
                for requestID in schedule[day].RequestIDs:
                    self.InstalledOnDay[requestID] = day

                if len(schedule[day].RequestIDs) > 0:
                    technicianRoute = self.TechnicianRoute(technician.ID)
                    technicianRoute.RequestIDs = schedule[day].RequestIDs
                    self.DaySchedules[day - 1].TechnicianRoutes.append(technicianRoute)
                    #print(technician.ID, day, schedule[day].RequestIDs, schedule[day].Distance)
                
            #print('Costs: %d' % self.scheduleCosts(schedule))
            #print()
            self.TechnicianDaySchedules[technician.ID] = schedule
                        
        return failedRequests
            
    def makeTruckRoutes(self):
        # one truck delivers one request per route
        self.Trucks = []
        for request in self.Instance.Requests:
            deliveryDay = min(request.toDay, self.InstalledOnDay[request.ID]) - 1

            schedule = self.DaySchedules[deliveryDay - 1]
            truckID = len(schedule.TruckRoutes) + 1

            if truckID <= len(self.Trucks):
                truck = self.Trucks[truckID - 1]
            else:
                truck = self.Truck(truckID)
                self.Trucks.append(truck)
                
            truckRoute = self.TruckRoute(truckID, deliveryDay)
            truckRoute.RequestIDs = [ request.ID ]
            truckRoute.Distance = 2 * self.Instance.calcDistance[0][request.customerLocID - 1]
            truck.TruckRoutes[deliveryDay] = truckRoute
            
            volume = self.getMachine(request.machineID).size * request.amount
            truckRoute.Volume = volume
            schedule.TruckRoutes.append(truckRoute)
    
    def printTruckRoutes(self):
        print('Truck capacity: %d' % self.Instance.TruckCapacity)
        print('Truck max distance: %d' % self.Instance.TruckMaxDistance)
        for day in range(1, self.Instance.Days):
            print()
            print('Day %d' % day)
            print('    Truck  Distance  Volume  Cost per volume  Requests')
            for truck in self.Trucks:
                for d, truckRoute in truck.TruckRoutes.items():
                    if d == day:
                        print('     %-5d  %-8d  %-6d  %12.2f     %s' % (truck.ID, truckRoute.Distance, truckRoute.Volume, truckRoute.Distance / truckRoute.Volume, truckRoute.RequestIDs))
            
    
    def combineTruckRoutes(self, truckRoute, truckRoutes):
        bestImprovement = False
        costsRoute = truckRoute.Distance * self.Instance.TruckDistanceCost

        depot = 1
        locations = set()
        for requestID in truckRoute.RequestIDs:
            locations.add(self.getRequest(requestID).customerLocID)

        for otherTruckRoute in truckRoutes:
            if truckRoute != otherTruckRoute and truckRoute.Volume + otherTruckRoute.Volume <= self.Instance.TruckCapacity:
                costsOtherRoute = otherTruckRoute.Distance * self.Instance.TruckDistanceCost
                newLocations = locations.copy()
                for requestID in otherTruckRoute.RequestIDs:
                    newLocations.add(self.getRequest(requestID).customerLocID)
                route, distance = self.findBestRoute(depot, newLocations)
                costsNewRoute = distance * self.Instance.TruckDistanceCost
                improvement = self.Instance.TruckDayCost + costsRoute + costsOtherRoute - costsNewRoute
                if distance < self.Instance.TruckMaxDistance and improvement > bestImprovement:
                    bestImprovement = improvement
                    bestOtherTruckRoute = otherTruckRoute 
                    bestRoute = route
                    bestDistance = distance
        if bestImprovement != False:
            truckRoutes.remove(truckRoute)
            
            truck = self.getTruck(truckRoute.TruckID)
            del truck.TruckRoutes[truckRoute.Day]
            if len(truck.TruckRoutes) == 0:
                self.Trucks.remove(truck)
            
            requestIDs = []
            for location in bestRoute:
                for requestID in truckRoute.RequestIDs + bestOtherTruckRoute.RequestIDs:
                    if self.getRequest(requestID).customerLocID == location:
                        requestIDs.append(requestID)
                        
            bestOtherTruckRoute.RequestIDs = requestIDs
            bestOtherTruckRoute.Distance = bestDistance
            bestOtherTruckRoute.Volume += truckRoute.Volume

        
    def improveTruckRoutesPerDay(self):
        for day in range(1, self.Instance.Days):
            routes = []
            for truck in self.Trucks:
                for d, truckRoute in truck.TruckRoutes.items():
                    if d == day:
                        costPerVolume = truckRoute.Distance / truckRoute.Volume
                        position = 0
                        for route in routes:
                            if costPerVolume < route.Distance / route.Volume:
                                position += 1
                            else:
                                break
                        routes.insert(position, truckRoute)
            
            for route in routes:
                if route.Volume < self.Instance.TruckCapacity:
                    self.combineTruckRoutes(route, routes)
                    #print(' %d - %0.2f' % (route.TruckID, route.Distance / route.Volume))


    def solve(self):
        self.matches()
        self.assignRequestsToTechnicians()
        failedRequests = self.makeTechnicianDaySchedules()
        
        if len(failedRequests) > 0:
            print('Failed to install:', [request.ID for request in failedRequests])
        
        for request in failedRequests:
            pass
            # stuur request naar alle capabele technicians en vraag aan elke technician de extra kosten die de hij/zij moet maken 
            # kies de goedkoopste
            # later doen
        
        self.makeTruckRoutes()
        
        #self.printTruckRoutes()
        
        self.calculateCosts()
        
        best = 1e20
        while (self.TotalCost < best):
            best = self.TotalCost
            self.improveTruckRoutesPerDay()
            
            for day in range(1, self.Instance.Days):
                daySchedule = self.DaySchedules[day - 1]
                daySchedule.TruckRoutes = []
                for truck in self.Trucks:
                    if day in truck.TruckRoutes.keys():
                        daySchedule.TruckRoutes.append(truck.TruckRoutes[day])

            self.calculateCosts()
            
        self.printTruckRoutes()
        
        
        self.calculateCosts()
        
        #self.overviewRequests()
        
        print()
        print('Total costs is', self.TotalCost)

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
    