# Vehicle Routing

from InstanceVerolog2019 import InstanceVerolog2019

INSTANCE = 2
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
            ''' ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED'''
            self.DistanceTravelled = 0 # De afstand die is afgelegd tot de laatste request, in volgorde van de requests (dus nog niet geoptimaliseerd)

        def __repr__(self):
            return '%d %s' % (self.TechnicianID, ' '.join(map(str, self.RequestIDs)))
     
    class Day:    
        def __init__(self, dayNumber):
            self.DayNumber = dayNumber
            self.NumberOfTrucks = 0
            self.TruckRoutes = []
            self.NumberOfTechnicians = 0
            self.TechnicianRoutes = []     
            ''' ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED'''
            self.TechniciansWorking = [] # Dit houdt bij welke technicians al zijn ingedeeld op die dag
        
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
        self.number_matches = [] # list die aantal technicians geeft die matchen
        
        
        for technician in self.Instance.Technicians:
            self.TechnicianMatches[technician.ID] = []

        for request in self.Instance.Requests:
            self.RequestMatches[request.ID] = []
            for technician in self.Instance.Technicians:
                if technician.capabilities[request.machineID - 1]:
                    if 2 * self.Instance.calcDistance[request.customerLocID - 1][technician.locationID - 1] <= technician.maxDayDistance:
                        self.RequestMatches[request.ID].append(technician)
                        self.TechnicianMatches[technician.ID].append(request)
        
        ''' ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED ADDED'''
        for request in self.Instance.Requests:
            self.number_matches.append(len(self.RequestMatches[request.ID]))
            '''
            print(request.ID, end = ' - ')
            for technician in self.RequestMatches[request.ID]:
                print(technician.ID, end = ' ')
            print()
            '''

        
        ''' requests op volgorde zetten: de requests die door de meeste technicians kunnen worden geinstalleerd als laatste'''
        pairs = zip(self.number_matches,self.Instance.Requests)
        sorted_pairs = sorted(pairs, key=lambda pair: pair[0]) #sorteren op basis van aantal technicians die job kunnen doen
        
        self.sorted_requests = [x for y, x in sorted_pairs]

        '''       
        for technician in self.Instance.Technicians:
            print(technician.ID, end = ' - ')
            for request in self.TechnicianMatches[technician.ID]:
                print(request.ID, end = ' ')
            print()
        '''

        
    

    def progress(self):
        print('Request  Delivery  Installment  Idle time')
        for request in self.Instance.Requests:
            idleTime = 0
            if self.RequestInstallmentDays[request.ID] > self.RequestDeliveryDays[request.ID] and self.RequestDeliveryDays[request.ID] > 0:
                idleTime = self.RequestInstallmentDays[request.ID] - self.RequestDeliveryDays[request.ID] - 1
            print('%6d  %8d  %11d  %9d' % (request.ID, self.RequestDeliveryDays[request.ID], self.RequestInstallmentDays[request.ID], idleTime))
    
    
    def assign_trucks(self): # assigns een truck voor iedere opdracht, voor iedere opdracht een nieuwe. Meteen als de opdracht available is bezorgen
        for request in self.Instance.Requests:
            day = request.fromDay 
            c = len(self.Days[day-1].TruckRoutes) # zodat elke dag trucks worden genummerd als 1,2,...
            self.Days[day-1].TruckRoutes.append(self.TruckRoute(c+1)) #voor iedere request, een nieuwe truck. Truck wordt toegevoegd op dag day-1
            self.Days[day-1].TruckRoutes[-1].RequestIDs.append(request.ID) # Voeg request id toe aan laatste truckroute in de list
            
    def assign_technicians(self):
        uninstalled_requests = self.sorted_requests[:] # of gebruik self.Instance.Requests[:], niet op volgorde

        for day in range(1,self.Instance.Days+1):

            for request in uninstalled_requests[:]:
                feasible_technicians = []    
   
                if day>request.fromDay :

                    for technician in self.Instance.Technicians:
                        if technician.capabilities[request.machineID - 1]:
                            if technician.ID not in self.Days[day-1].TechniciansWorking:  #technician werkt deze dag nog niet
                                if 2 * self.Instance.calcDistance[request.customerLocID - 1][technician.locationID - 1] <= technician.maxDayDistance:
                                    feasible_technicians.append(technician)

                            else:
                                i = self.Days[day-1].TechniciansWorking.index(technician.ID) #als technician al gebruikt is, vindt dit de index van deze technician
                                if len(self.Days[day-1].TechnicianRoutes[i].RequestIDs) < technician.maxNrInstallations:
                                    
                                    a = self.getRequest(self.Days[day-1].TechnicianRoutes[i].RequestIDs[-1]).customerLocID-1 # tot nu toe laatste request voor technician op deze dag
                                    b = request.customerLocID - 1 # locatie van huidige request
                        
                                    if self.Days[day-1].TechnicianRoutes[i].DistanceTravelled + self.Instance.calcDistance[a][b] + self.Instance.calcDistance[b][technician.locationID - 1]<= technician.maxDayDistance:  
                                        feasible_technicians.append(technician) #distance travelled is de afstand tot de tot nu toe laatste request. 
                    
                    for technician in feasible_technicians[:]:
                        
                        # Heuristic: geef een technician vrij na 4 dagen, dan hoeft deze maar een dag vrij
                        if technician.ID in self.Days[day-2].TechniciansWorking:
                            if technician.ID in self.Days[day-3].TechniciansWorking:
                                if technician.ID in self.Days[day-4].TechniciansWorking:
                                    if technician.ID in self.Days[day-5].TechniciansWorking:
                                            feasible_technicians.remove(technician) #[f for f in  feasible_technicians if f!= technician]
                                                
                         
                    if  feasible_technicians:   #check if list is not  empty
                        #Heuristic: vind de technician waar zijn laatste stop het dichtste bij de huidige request is
                        
                        distances_to_request = [] # een list die de afstanden geeft van alle feasible technicians (vanaf hun laatste request) naar de huidige request
                        for feasible_technician in feasible_technicians:
                            if feasible_technician.ID not in self.Days[day-1].TechniciansWorking: #technician was nog niet aan het werk: voeg afstand van thuislocatie naar request locatie toe
                                distances_to_request.append(self.Instance.calcDistance[feasible_technician.locationID-1][request.customerLocID - 1])
                            else:
                                i = self.Days[day-1].TechniciansWorking.index(feasible_technician.ID) #als technician al gebruikt is, vindt dit de index van deze technician
                                for route in self.Days[day-1].TechnicianRoutes:
                                    if route.TechnicianID == feasible_technician.ID:
                                        last_request = self.getRequest(route.RequestIDs[-1]).customerLocID-1 #location of last request
                                        distances_to_request.append(self.Instance.calcDistance[last_request][request.customerLocID - 1])
                                        
                                        
                        pairs = zip(distances_to_request,feasible_technicians)
                        sorted_pairs = sorted(pairs, key=lambda pair: pair[0])    #sorteert de paren op basis van afstand tot request     
                        sorted_technicians = [x for y, x in sorted_pairs] # technician dichtste bij staat boven
                        
                        closest_technician = sorted_technicians[0]
                        
                        if closest_technician.ID  not in self.Days[day-1].TechniciansWorking:
                            self.Days[day-1].TechnicianRoutes.append(self.TechnicianRoute(closest_technician.ID)) #Assigns eerste feasible technician aan de job
                            
                            self.Days[day-1].TechnicianRoutes[-1].RequestIDs.append(request.ID)
                            self.Days[day-1].TechniciansWorking.append(closest_technician.ID)   
                            self.Days[day-1].TechnicianRoutes[-1].DistanceTravelled += self.Instance.calcDistance[closest_technician.locationID - 1 ][request.customerLocID - 1] 
                            
                            
                        else:
                            i = self.Days[day-1].TechniciansWorking.index(closest_technician.ID) #als technician al gebruikt is, vindt dit de index van deze technician
                            for route in self.Days[day-1].TechnicianRoutes:
                                if route.TechnicianID == closest_technician.ID:
                                    a = self.getRequest(route.RequestIDs[-1]).customerLocID-1
                                    route.RequestIDs.append(request.ID)
                                    b = request.customerLocID - 1
                                    route.DistanceTravelled += self.Instance.calcDistance[a][b] #+ self.Instance.calcDistance[b][closest_technician.locationID-1] #checken
                    
                        uninstalled_requests.remove(request)                            

        print("Uninstalled Requests:", [u.ID for u in uninstalled_requests])
  
    
        
def main():
    global problem, solution
    #instance_file = 'VSC2019_ORTEC_early_%02d.txt' % INSTANCE
    instance_file = 'STUDENT%03d.txt' % INSTANCE

    output_file = instance_file.replace('.txt', '-solution.txt')
    
    problem = InstanceVerolog2019(instance_file)
    
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
    
    problem.calculateDistances()
    
    solution = Solution(problem)
    
    #solution.progress()
    solution.matches()

    solution.assign_trucks()
    solution.assign_technicians()    

    solution.calculate()
    solution.writeSolution(output_file)
        

main()
