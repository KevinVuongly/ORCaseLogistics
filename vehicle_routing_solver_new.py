# Vehicle Routing
from InstanceVerolog2019 import InstanceVerolog2019
from SolutionVerolog2019 import SolutionVerolog2019
import christofides
import itertools
from numpy import random

RUN_ALL_INSTANCES = True
INSTANCE = 6
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
# Step 1: assign requests to technicians
# step 2: make technician schedules
# step 4: let trucks deliver before installment
# step 5: improve schedules
#
# subproblem is Travelers Salesmen Problem
##############


class Solution:
    class TruckRoute: 
        def __init__(self):
            self.RequestIDs = []  #Volgorde van requests voor deze truckroute
            self.Distance = 0 #Afgelegde afstand
            self.Volume = 0   #Gebruikte volume

    class TechnicianRoute:
        def __init__(self, technician):
            """
            Parameters:
                technician (InstanceVerolog2019.Technician)
            """
            self.TechnicianID = technician.ID 
            self.Technician = technician 
            self.Distance = 0
            self.RequestIDs = []
            
    class DaySchedule:
        def __init__(self):
            self.NumberOfTrucks = 0
            self.TruckRoutes = []
            self.NumberOfTechnicians = 0
            self.TechnicianRoutes = []
        
    def __init__(self, instance):
        """
        Parameters:
            instance (InstanceVerolog2019)
        """
        self.Instance = instance #de instantie van het probleem 2019

        self.TotalCost = 0
        self.DaySchedules = [ self.DaySchedule() for i in range(instance.Days) ] #Maak een lijst van dayschedules

        self.RequestDeliveryDays = {} #voor elke request onthoudt welke dag bezorgd is
        self.RequestInstallmentDays = {} #voor elke request onthouden welke dag de machine(s) geinstalleerd wordt/worden

        for request in instance.Requests:
            self.RequestDeliveryDays[request.ID] = 0 #dag 0 betekent dat de request nog niet is bezorgd
            self.RequestInstallmentDays[request.ID] = 0 #dag 0 betekent dat de machine(s) van de request nog niet is/zijn geinstalleerd
       
        instance.calculateDistances() #afstand berekend aan de hand van x en y coordinaten (afgerond naar boven)
        
        self.Success = self.solve() #start het algoritme voor het oplossen van het gehele probleem en geeft aan of het gelukt is of niet

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

            for day in range(1, 1 + self.Instance.Days):
                daySchedule = self.getDaySchedule(day)
                file.write('\n')
                file.write('DAY = %d\n' % day)
                file.write('NUMBER_OF_TRUCKS = %d\n' % len(daySchedule.TruckRoutes))
                truckID = 0
                for truckRoute in daySchedule.TruckRoutes:
                    truckID += 1
                    file.write('%d %s\n' % (truckID, ' '.join(map(str, truckRoute.RequestIDs))))
                file.write('NUMBER_OF_TECHNICIANS = %d\n' % len(daySchedule.TechnicianRoutes))
                for technicianRoute in daySchedule.TechnicianRoutes:
                    file.write('%d %s\n' % (technicianRoute.TechnicianID, ' '.join(map(str, technicianRoute.RequestIDs))))

        except IOError:
            print('Error opening %s' %filename)

    def getMachine(self, ID):
        """ geeft machine met het opgegeven ID """
        for machine in self.Instance.Machines:
            if ID == machine.ID:
                return machine
        return False

    def getRequest(self, ID):
        """ geeft request met het opgegeven ID """
        for request in self.Instance.Requests:
            if ID == request.ID:
                return request
        return False

    def getTechnician(self, ID):
        """ geeft technician met het opgegeven ID """
        for technician in self.Instance.Technicians:
            if ID == technician.ID:
                return technician
        return False
    
    def getDaySchedule(self, day):
        """ geeft dagschema van de opgegeven dag """
        return self.DaySchedules[day - 1]
       
    def calculateCosts(self):
        self.TruckDistance = 0
        self.NumberOfTruckDays = 0
        self.NumberOfTrucksUsed = 0
        self.NumberOfTechnicianDays = 0

        self.TechnicianDistance = 0
        self.TechniciansUsed = set()

        for day in range(1, 1 + self.Instance.Days):  #gaat alle dagen langs
            daySchedule = self.getDaySchedule(day) #pakt de schedule van de dag
            daySchedule.numberOfTrucks = len(daySchedule.TruckRoutes)  #berekent het aantal trucks dat is gebruikt voor die dag
            self.NumberOfTruckDays += daySchedule.numberOfTrucks #totaal aantal truckdays
            if daySchedule.numberOfTrucks > self.NumberOfTrucksUsed: 
                self.NumberOfTrucksUsed = daySchedule.numberOfTrucks

            for route in daySchedule.TruckRoutes: #bepaald de afstand van de route
                start = 1
                home = start
                for requestID in route.RequestIDs:
                    if requestID == 0:    # 0 is not a requestID, but it means that the truck goes back to the depot
                        destination = 1   # 1 is the locationID of the depot
                    else:
                        self.RequestDeliveryDays[requestID] = day
                        destination = self.getRequest(requestID).customerLocID
                    self.TruckDistance += self.Instance.calcDistance[start - 1][destination - 1]
                    start = destination
                self.TruckDistance += self.Instance.calcDistance[start - 1][home - 1]

            daySchedule.numberOfTechnicians = len(daySchedule.TechnicianRoutes)     # one technician does only one route per day max
            self.NumberOfTechnicianDays += daySchedule.numberOfTechnicians #number of technician days
            for route in daySchedule.TechnicianRoutes:
                self.TechniciansUsed.add(route.TechnicianID) #hier onthoud je welke technicians er gebruikt zijn
                start = self.Instance.Technicians[route.TechnicianID - 1].locationID #lengte van de route van een technician
                home = start
                for requestID in route.RequestIDs: #bepaalt de afstand die de technician aflegt
                    self.RequestInstallmentDays[requestID] = day
                    destination = self.getRequest(requestID).customerLocID
                    self.TechnicianDistance += self.Instance.calcDistance[start - 1][destination - 1] # technician distance wordt hier berekend voor alle technicians samen
                    start = destination
                self.TechnicianDistance += self.Instance.calcDistance[start - 1][home - 1]

        self.NumberOfTechniciansUsed = len(self.TechniciansUsed)

        #berekent de Idle Machine Costs
        self.IdleMachineCosts = 0
        for request in self.Instance.Requests:
            if 0 < self.RequestDeliveryDays[request.ID] < self.RequestInstallmentDays[request.ID]:
                idleTime = self.RequestInstallmentDays[request.ID] - self.RequestDeliveryDays[request.ID] - 1
                idlePenalty = self.getMachine(request.machineID).idlePenalty
                self.IdleMachineCosts += idleTime * idlePenalty * request.amount
        
        #totale kosten
        self.TotalCost = self.Instance.TruckDistanceCost * self.TruckDistance \
                       + self.Instance.TruckDayCost * self.NumberOfTruckDays \
                       + self.Instance.TruckCost * self.NumberOfTrucksUsed \
                       + self.Instance.TechnicianDistanceCost * self.TechnicianDistance \
                       + self.Instance.TechnicianDayCost * self.NumberOfTechnicianDays \
                       + self.Instance.TechnicianCost * self.NumberOfTechniciansUsed \
                       + self.IdleMachineCosts
        
    def matches(self):
        """
        Voor elke request wordt een lijst gemaakt van technicians die geschikt zijn.
        De lijst is gesorteerd op afstand tussen de technicians en de locatie van de request.
        """
        self.RequestMatches = {}    # key is request ID, value is a list of tuples (technicians, distance) for technicians capable for the request
        for request in self.Instance.Requests:            
            self.RequestMatches[request.ID] = []
            shuffled = self.Instance.Technicians.copy()    # Technicians are being shuffled in random order
            random.shuffle(shuffled) #hier wordt random geshuffled, kan zijn dat twee technicians op gelijke afstand zijn, dan heeft de laatste voorang.
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
                        self.RequestMatches[request.ID].insert(i, (technician, distance))

    def overviewRequests(self): 
        """
        Print een tabel van de bezorgdag en installatie dag van elke request en andere informatie (voor checks tussendoor). (zie kolommen)
        """
        print('Request  Delivery  Installment  Idle time  Idle penalty  Amount  Idle cost')
        totalIdleCost = 0
        for request in self.Instance.Requests:
            idleTime = 0
            idlePenalty = self.getMachine(request.machineID).idlePenalty
            idleCost = 0
            if 0 < self.RequestDeliveryDays[request.ID] < self.RequestInstallmentDays[request.ID]:
                idleTime = self.RequestInstallmentDays[request.ID] - self.RequestDeliveryDays[request.ID] - 1
                idleCost = idleTime * idlePenalty * request.amount
                totalIdleCost += idleCost
            print('%6d  %8d  %11d  %9d  %12d  %6d  %9d' % (request.ID, self.RequestDeliveryDays[request.ID], self.RequestInstallmentDays[request.ID], idleTime, idlePenalty, request.amount, idleCost))
        print()
        print('Total idle costs', totalIdleCost)

    def assignRequestsToTechnicians(self):
        """
        Geeft elke request aan de dichtstbijzijnde technician. Als twee technicians dezelfde afstand hebben dan is de toewijzing afhankelijk van de random shuffeling, die eerder is gedaan. 
        Het kan zijn dat een technician meer requests krijgt toegewezen dan past in zijn rooster. 
        """     
        self.assignments = {}   # assigns requests to technicians 

        for technician in self.Instance.Technicians:
            self.assignments[technician.ID] = []
            
        for request in self.Instance.Requests:
            technician, distance = self.RequestMatches[request.ID][0]   # technician first in list is closest to the request location (the list is sorted by distance)
            self.assignments[technician.ID].append(request)
     
    def getDistance(self, route):
        """ berekent de afstand van een route (lijst van locaties) """
        distance = 0
        start = route[0]
        for destination in route[1:]:
            distance += self.Instance.calcDistance[start - 1][destination - 1]
            start = destination
        return distance
        
    def findBestRoute(self, home, locations):
        if len(locations) > 6:
            vertices = list(locations)
            if home in vertices:
                vertices.remove(home)
            vertices = [ home ] + vertices
            distances = [[ self.Instance.calcDistance[i - 1][j - 1] for i in vertices] for j in vertices ]
            path, length = christofides.tsp(0, distances)
            route = [ vertices[i] for i in path[1:] ]
            if len(route) > len(locations):
                route = route[:-1]
            return route, length
        
        bestDistance = 40000    # around the earth
        bestRoute = ()
        checkedRoutes = []
        for permutation in itertools.permutations(locations):
            if permutation[::-1] not in checkedRoutes:
                distance = self.getDistance([home] + list(permutation) + [home])
                if distance < bestDistance:
                    bestDistance = distance
                    bestRoute = permutation
                checkedRoutes.append(permutation)       
        return bestRoute, bestDistance


    def checkSchedule(self, schedule, technician):
        """ Kijkt welke requests dubbel worden uitgevoerd door de technician en welke nog niet worden uitgevoerd """
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
    
    def removeFromSchedule(self, technician, schedule, request):
        """
        Verwijdert een request van de schedule van de technician en de afstand wordt bepaald van de requests die overblijven.
        De request zit nu op twee of meerdere dagen in het schema van de technician. We kijken op welke dag de grootste besparing kan worden behaald en daarna verwijderen de request.
        """
        best = -1e20
        home = technician.locationID
        for day in range(2, 1 + self.Instance.Days):
            if request.ID in schedule[day].RequestIDs:
                # remove request from day, calculate costs and add request back to the day
                locations = set([ self.getRequest(requestID).customerLocID for requestID in schedule[day].RequestIDs if requestID != request.ID ])
                route, distance = self.findBestRoute(home, locations)
                if distance <= technician.maxDayDistance:
                    reductionDistance = schedule[day].Distance - distance
                    savedCosts = reductionDistance * self.Instance.TechnicianDistanceCost
                    if len(schedule[day].RequestIDs) == 1:
                        savedCosts += self.Instance.TechnicianDayCost  # savedTechnicianDay
                    if day > request.toDay:
                        minimumIdleTime = day - request.toDay - 1
                        savedCosts += minimumIdleTime * self.getMachine(request.machineID).idlePenalty  # idle costs
                    if savedCosts >= best:
                        best = savedCosts
                        removeRequestFromDay = day
                        newRoute = route
                        newDistance = distance
                    
        schedule[removeRequestFromDay].RequestIDs.remove(request.ID)
        requestIDs = []
        for location in newRoute:
            for requestID in schedule[removeRequestFromDay].RequestIDs:
                if self.getRequest(requestID).customerLocID == location:
                    requestIDs.append(requestID)
        schedule[removeRequestFromDay].RequestIDs = requestIDs
        schedule[removeRequestFromDay].Distance = newDistance
                
    def needRestDay(self, schedule, day):
        """ 
        Kijkt of het nog een lege dag is in de schedule van de technician, die opgevuld mag worden. 
        Rekening houdend met de maximaal 5 dagen achtereen volgend.
        Moet gevolgd worden door twee dagen rust.
        """
        workDays = [ d for d in schedule.keys() if len(schedule[d].RequestIDs) > 0 ]
        if day in workDays:
            return False
        i = 1
        while day - i in workDays:
            i += 1
        j = 1
        while day + j in workDays:
            j += 1
        working = i + j - 1
        if working > 5:
            return True
        twoDaysRestAfter = day + j + 1 not in workDays
        if working == 5 and not twoDaysRestAfter:
            return True
        workedFiveDaysBefore = all(d in workDays for d in range(day - 6, day - 1))
        if workedFiveDaysBefore:
            return True
        return False
        
    def addToSchedule(self, technician, schedule, request):
        """
        Voegt een request toe aan het schema van een technician. Gekeken wordt op welke dag dit het beste kan zodanig dat het past in de bestaande routes.
        We letten op afstand en mogelijke idle tijd
        """
        best = 1e20
        installed = False
        days = range(request.fromDay + 1, 1 + self.Instance.Days)
        for day in days:
            if not self.needRestDay(schedule, day) and len(schedule[day].RequestIDs) < technician.maxNrInstallations:   # maxNrInstallations constraint
                # add request to day, calculate costs and remove request from the day
                locations = set()
                locations.add(request.customerLocID)
                for requestID in schedule[day].RequestIDs:
                    locations.add(self.getRequest(requestID).customerLocID)
                route, distance = self.findBestRoute(technician.locationID, locations)
                if distance <= technician.maxDayDistance:
                    extraDistance = distance - schedule[day].Distance
                    extraCosts = extraDistance * self.Instance.TechnicianDistanceCost
                    if len(schedule[day].RequestIDs) == 0:
                        extraCosts += self.Instance.TechnicianDayCost  # extraTechnicianDay
                    if day > request.toDay:
                        minimumIdleTime = day - request.toDay - 1
                        extraCosts += minimumIdleTime * self.getMachine(request.machineID).idlePenalty  # idle costs
                    if extraCosts <= best:
                        best = extraCosts
                        addRequestToDay = day
                        bestRoute = route
                        installed = True
            
        if installed:               
            requestIDs = []
            for location in bestRoute:
                for requestID in schedule[addRequestToDay].RequestIDs + [request.ID]:
                    req = self.getRequest(requestID)
                    if req.customerLocID == location:
                        requestIDs.append(req.ID)
            schedule[addRequestToDay].RequestIDs = requestIDs
            schedule[addRequestToDay].Distance += extraDistance

        return installed
        
    
    def makeTechnicianSchedules(self):
        failedRequests = []
        self.TechnicianSchedules = {}
        self.InstalledOnDay = {}
        for request in self.Instance.Requests:
            self.InstalledOnDay[request.ID] = 0
        
        days = range(2, 1 + self.Instance.Days)
        for technician in self.Instance.Technicians:
            schedule = {}
            for day in days:
                daySchedule = self.TechnicianRoute(technician)
                schedule[day] = daySchedule
                
                if not self.needRestDay(schedule, day):
                    requests = []    # find request that are assigned to the technician and that can be delivered on the day before
                    requestIDs = []
                    for request in self.assignments[technician.ID]:
                        if request.fromDay + 1 <= day <= request.toDay + 1:
                            requests.append(request)
                    distance = 0
                    if 0 < len(requests) <= technician.maxNrInstallations:   # maxNrInstallations constraint
                        locations = set()
                        for request in requests:
                            locations.add(request.customerLocID)
                        route, distance = self.findBestRoute(technician.locationID, locations)
                        if distance <= technician.maxDayDistance:
                            for location in route:
                                for request in requests:
                                    if request.customerLocID == location:
                                        requestIDs.append(request.ID)
                    daySchedule.RequestIDs = requestIDs
                    daySchedule.Distance = distance
                    # check if the requests on the day before all fit on today's schedule too
                    if day > 2 and len(schedule[day - 1].RequestIDs) > 0:
                        if set(schedule[day - 1].RequestIDs).issubset(set(requestIDs)):
                            schedule[day - 1].RequestIDs = []
                            schedule[day - 1].Distance = 0
                        elif set(requestIDs).issubset(set(schedule[day - 1].RequestIDs)):
                            schedule[day].RequestIDs = []
                            schedule[day].Distance = 0
                    
            double, missing = self.checkSchedule(schedule, technician)
            for request in double:
                self.removeFromSchedule(technician, schedule, request)
            
            for request in missing:
                if not self.addToSchedule(technician, schedule, request):
                    failedRequests.append((technician, request))
            
            self.TechnicianSchedules[technician.ID] = schedule
                        
        return failedRequests
            
    def makeTruckRoutes(self):
        # one truck delivers one request per route
        for request in self.Instance.Requests:
            if self.InstalledOnDay[request.ID] > 0:
                deliveryDay = min(request.toDay, self.InstalledOnDay[request.ID] - 1)
                daySchedule = self.getDaySchedule(deliveryDay)
                       
                truckRoute = self.TruckRoute()
                truckRoute.RequestIDs = [ request.ID ]
                truckRoute.Distance = 2 * self.Instance.calcDistance[0][request.customerLocID - 1]
                
                volume = self.getMachine(request.machineID).size * request.amount
                truckRoute.Volume = volume
                daySchedule.TruckRoutes.append(truckRoute)
    
    def printTruckRoutes(self):
        print('Truck capacity: %d' % self.Instance.TruckCapacity)
        print('Truck max distance: %d' % self.Instance.TruckMaxDistance)
        for day in range(1, self.Instance.Days):
            print()
            print('Day %d' % day)
            print('    Truck  Distance  Volume  Cost per volume  Requests')
            truckID = 0
            for truckRoute in self.getDaySchedule(day).TruckRoutes:
                truckID += 1
                print('     %-5d  %-8d  %-6d  %12.2f     %s' % (truckID, truckRoute.Distance, truckRoute.Volume, truckRoute.Distance / truckRoute.Volume, truckRoute.RequestIDs))
                
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
                if distance <= self.Instance.TruckMaxDistance and improvement > bestImprovement:
                    bestImprovement = improvement
                    bestOtherTruckRoute = otherTruckRoute 
                    bestRoute = route
                    bestDistance = distance
        if bestImprovement != False:
            truckRoutes.remove(truckRoute)
            
            requestIDs = []
            for location in bestRoute:
                for requestID in truckRoute.RequestIDs + bestOtherTruckRoute.RequestIDs:
                    if self.getRequest(requestID).customerLocID == location:
                        requestIDs.append(requestID)
                        
            bestOtherTruckRoute.RequestIDs = requestIDs
            bestOtherTruckRoute.Distance = bestDistance
            bestOtherTruckRoute.Volume += truckRoute.Volume

        
    def improveTruckRoutesPerDay(self, day):
        truckRoutes = self.getDaySchedule(day).TruckRoutes
        for truckRoute in truckRoutes:
            if truckRoute.Volume < self.Instance.TruckCapacity:
                self.combineTruckRoutes(truckRoute, truckRoutes)

    def improveTruckRoutes(self):
        self.calculateCosts()
        best = self.TotalCost + 1
        while (self.TotalCost < best):
            best = self.TotalCost
            for day in range(1, self.Instance.Days):
                self.improveTruckRoutesPerDay(day)
            
            self.calculateCosts()

    def installRequest(self, request, occupied = False):
        # fit request in a schedule of a capable technician
        bestTechnician = None
        for technician, distance in self.RequestMatches[request.ID]:
            if occupied is not False and technician != occupied:
                schedule = self.TechnicianSchedules[technician.ID]
                if self.addToSchedule(technician, schedule, request):
                    return True
        if bestTechnician is None:
            return False
        return True
                
        
    def solve(self):
        success = True

        self.matches()
        self.assignRequestsToTechnicians()
        failedRequests = self.makeTechnicianSchedules()
        
        for technician, request in failedRequests:
            # stuur request naar alle capabele technicians en vraag aan elke technician de extra kosten die de hij/zij moet maken 
            # kies de goedkoopste
            if not self.installRequest(request, occupied = technician):
                print(request.ID, 'has not been assigned to a technician')
                success = False
        
        for technician in self.Instance.Technicians:
            schedule = self.TechnicianSchedules[technician.ID]
            for day in range(2, 1 + self.Instance.Days):
                for requestID in schedule[day].RequestIDs:
                    self.InstalledOnDay[requestID] = day

                if len(schedule[day].RequestIDs) > 0:
                    technicianRoute = self.TechnicianRoute(technician)
                    technicianRoute.RequestIDs = schedule[day].RequestIDs
                    self.DaySchedules[day - 1].TechnicianRoutes.append(technicianRoute)
                    #print(technician.ID, day, schedule[day].RequestIDs, schedule[day].Distance)
                
            #print('Technician %d schedule costs: %d' % (technician.ID, self.scheduleCosts(schedule)))
            #print()
        
        self.makeTruckRoutes()
        #self.printTruckRoutes()

        self.improveTruckRoutes()
        #self.printTruckRoutes()
        
        #self.overviewRequests()
        
        if self.TotalCost == 0:
            self.calculateCosts()
        
        print('Total costs is for', self.Instance.Name, 'is', self.TotalCost)
        return success

def checkSolution(instance_file, solution_file, skipExtraDataCheck = False):
    Instance = InstanceVerolog2019(instance_file)
    if not Instance.isValid():
        print('File %s is an invalid instance file\nIt contains the following errors:' % instance)
        print( '\t' + '\n\t'.join(Instance.errorReport) )
        return
    Solution = SolutionVerolog2019(solution_file, Instance)   
    if Solution.isValid():
        print('Solution %s is a valid solution' % solution_file)
        if skipExtraDataCheck:
            res = Solution.areGivenValuesValid()
            if res[0]:
                print('The given solution information is correct')
            else:
                print(res[1])
        print('\t' + '\n\t'.join(str(Solution.calcCost).split('\n')))
        if len(Solution.warningReport) > 0:
            print('There were warnings:')
            print( '\t' + '\n\t'.join(Solution.warningReport) )
    else:
        print('File %s is an invalid solution file\nIt contains the following errors:' % solution_file)
        print( '\t' + '\n\t'.join(Solution.errorReport) )
        if len(Solution.warningReport) > 0:
            print('There were also warnings:')
            print( '\t' + '\n\t'.join(Solution.warningReport) )
    print()            


if __name__ == "__main__":    
    if TEST_FILE:
        instance_file = 'data/STUDENT%03d.txt' % INSTANCE
        output_file = 'solution/STUDENT%03d-solution.txt' % INSTANCE
    else:
        if RUN_ALL_INSTANCES:
            for instance in range(1, 26):
                random.seed(SEED)
                christofides.resetRandom(seed = 1)
                instance_file = 'VSC2019_ORTEC_early_%02d.txt' % instance
                output_file = instance_file.replace('.txt', '-solution.txt')
                Solution(InstanceVerolog2019(instance_file)).writeSolution(output_file)          
                checkSolution(instance_file, output_file)
        else:
            random.seed(SEED)
            christofides.resetRandom(seed = 1)
            instance_file = 'VSC2019_ORTEC_early_%02d.txt' % INSTANCE
            output_file = instance_file.replace('.txt', '-solution.txt')
        
            problem = InstanceVerolog2019(instance_file)
            solution = Solution(problem)
            solution.writeSolution(output_file)
            checkSolution(instance_file, output_file)
