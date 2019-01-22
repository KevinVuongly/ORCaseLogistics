# Vehicle Routing

from instance_toine import InstanceVerolog2019 # aangepast, bij class Request self.delivery_day toegevoegd
import numpy as np
import math
from gurobipy import *
import time as time

start = time.time()
#lastige instances: early 6, early 11

INSTANCE = 6
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
            self.scheduled_today = []
        
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
                    
                last = self.getRequest(route.RequestIDs[-1]).customerLocID
                self.TruckDistance +=  self.Instance.calcDistance[last-1][0]
                    
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
                  
                last = self.getRequest(route.RequestIDs[-1]).customerLocID
                technician_location = self.Instance.Technicians[route.TechnicianID - 1].locationID
                self.TechnicianDistance +=   self.Instance.calcDistance[last-1][technician_location-1]     
                        
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
    def assign_trucks(self): # assigns een truck voor iedere opdracht, voor iedere opdracht een nieuwe. Meteen als de opdracht available is bezorgen
        for request in self.Instance.Requests:
            day = request.fromDay 
            c = len(self.Days[day-1].TruckRoutes) # zodat elke dag trucks worden genummerd als 1,2,...
            self.Days[day-1].TruckRoutes.append(self.TruckRoute(c+1)) #voor iedere request, een nieuwe truck. Truck wordt toegevoegd op dag day-1
            self.Days[day-1].TruckRoutes[-1].RequestIDs.append(request.ID) # Voeg request id toe aan laatste truckroute in de list
    '''
    def assign_trucks(self):

        undelivered_requests = self.Instance.Requests[:]
        for day in range(1,self.Instance.Days+1):
            requests_today = []
            volume_today = 0
            for request in undelivered_requests:
                if  request.scheduled_delivery== day: # request.fromDay#
                    requests_today.append(request)
                    volume_today += request.amount*self.getMachine(request.machineID).size #volume van deze request
                    
            if len(requests_today)>0:
                arguments = self.distancesForTSP(requests_today)
                n = arguments[0] 
                distances = arguments[1]
                request_dict = arguments[2]
                
                tsp_sol = tsp(n,distances,request_dict)  #  TSP runnen met alle instances today, zodat je ongeveer weet welke bij elkaar in de buurt liggen
            
                for k in range(1,len(self.Instance.Requests)+1): # first try with as few trucks as possible            
                    if volume_today < self.Instance.TruckCapacity*k : # als het groter is is het sowieso niet mogelijk om over k trucks te verdelen    
                        request_sets = [] #partitie van de requests op deze dag
                        current_request_set = [] 
                        current_volume_set = 0
                        
                        #print(tsp_sol[0],"tsp")
                        avg_volume = math.ceil(volume_today/k) #guideline for how much to put into each truck.  
                        
                        for request in tsp_sol[0]: # in order of the tour, requests that are put in same truck will be "close"
                            if current_volume_set + request.amount*self.getMachine(request.machineID).size <= avg_volume:
                                current_request_set.append(request)
                                current_volume_set += request.amount*self.getMachine(request.machineID).size
                                
                                if request == tsp_sol[0][-1]: # als het laatst request is, voeg dan de set toe
                                    request_sets.append(current_request_set)    
                            else:
                                if current_volume_set + request.amount*self.getMachine(request.machineID).size <= self.Instance.TruckCapacity:
                                    current_request_set.append(request)    
                                    request_sets.append(current_request_set)
                                    
                                    current_request_set = []
                                    current_volume_set = 0
                                else:
                                    request_sets.append(current_request_set)
                                    current_request_set = [request]
                                    current_volume_set = request.amount*self.getMachine(request.machineID).size
                                    
                                    if request == tsp_sol[0][-1]: # als het laatst request is, voeg dan de set toe
                                        request_sets.append(current_request_set)       
    
                        #verdeel zo gelijk mogelijk het gewicht over de k routes
                        
                        #print("request sets",request_sets, "\n")
                        if len(request_sets) <= k: # dan is er een geldige partitie op basis van het volume
                            routes = []
                            
                            for request_set in request_sets:
                                if len(request_set)>0:
                                    
                                    route_distance = 0
                                    start = 1
                                    for request in request_set:
                                        destination = request.customerLocID
                                        
                                        route_distance += self.Instance.calcDistance[start - 1][destination - 1]    
                                        start = request.customerLocID
                                    last = request_set[-1].customerLocID
                                    route_distance += self.Instance.calcDistance[last-1][0]
                                    
                                    if route_distance <= self.Instance.TruckMaxDistance:
                                        routes.append(request_set)
                                        route_distance =0 
                                    else:
                                        break              
                            if len(routes)==len(request_sets): #only if all tours have feasible length
                                
                                for i in range(len(routes)):
                                    self.Days[day-1].TruckRoutes.append(self.TruckRoute(i+1)) 
                                    for request in routes[i]:
                                        self.Days[day-1].TruckRoutes[-1].RequestIDs.append(request.ID) # Voeg request id toe aan laatste truckroute in de list
                                        undelivered_requests.remove(request)
                                        request.delivery_day = day 
                                        
                                        
                                '''        
                                route_dict[day]= routes #route_dict aanmaken
                                for i in range(len(routes)):    
                                    for request in routes[i]:
                                        undelivered_requests.remove(request)'''
                                break
            
        if undelivered_requests == []:
            return True 
        else:
            return False
                     
      
        
    def assign_technicians(self):
        uninstalled_requests = self.sorted_requests[:] # of gebruik self.Instance.Requests[:], niet op volgorde

        for day in range(1,self.Instance.Days+1):

            for request in uninstalled_requests[:]:
                feasible_technicians = []    
   
                if day>request.delivery_day: #request.fromDay :
                    
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
                        
        if uninstalled_requests == []:
            return True 
        else:
            return False
                     
        
  
    
    # assume all requests fit into truck. 
    def distancesForTSP(self,requests):
        n = len(requests)+1

        #assign number from 1...n to each request
        request_dict = {}
        k = 1
        for request in requests:
            request_dict[request] = k
            k = k+1
        distances = {} #computes all distances

        for i in requests:
            for j in requests:
                distances [request_dict[i],request_dict[j]] =  self.Instance.calcDistance[i.customerLocID-1][j.customerLocID-1]
            distances [request_dict[i],0] = distances [0,request_dict[i]] =self.Instance.calcDistance[i.customerLocID-1][self.Instance.Locations[0].ID-1]
        distances[0,0] = 0   
        return n,distances,request_dict 
    
    def clean(self): # als deze functie wordt aangeroepen verwijdert deze eerst alle eerder ingevulde informatie 
        for day in range(1,self.Instance.Days+1):
            self.Days[day-1].TruckRoutes = []
            self.Days[day-1].TechniciansWorking = []
            self.Days[day-1].TechnicianRoutes= []
            
        for request in self.Instance.Requests:
            request.delivery_day = None 
            request.scheduled_delivery = None
    
    def spread_requests(self,nr_days): #tries to spread out the requests as evenly as possible, so that as few trucks as possible are necessary. Parameter days should be less than self.instance.days, but more than the last release date
        requests_per_day = math.ceil(len(self.Instance.Requests)/nr_days) # avg amount of requests per day
        
        
        amount_day = {} #dictionary that stores the days and # requests per day
        for day in range(1,nr_days+1):
            amount_day[day] =0
        
        for request in self.Instance.Requests:
            request.scheduled_delivery = request.fromDay
            self.Days[request.fromDay-1].scheduled_today.append(request)
            amount_day[request.fromDay] +=1
            
            
            
        for day in range(1,nr_days):
            while amount_day[day]>requests_per_day: # request has more than the average amount of requests 
                latest_due = 0
                latest_request = None
                for request in  self.Days[day-1].scheduled_today:#push request with latest due date. Push it to a day with least amount of requests, if toDay <= that day1
                    if request.toDay >latest_due:
                        latest_due = request.toDay
                        latest_request = request
                # push request with latest due date to next day
                if latest_due > day:
                    latest_request.scheduled_delivery = day+1
                    self.Days[day-1].scheduled_today.remove(latest_request)
                    self.Days[day].scheduled_today.append(latest_request)
                
                amount_day[day] -=1
                amount_day[day+1] +=1
                
        return amount_day
    
    

def tsp(n, distances,request_dict):  
    
    if n <= 2: # tsp alg werkt niet voor n=2
        TSP = []
        for i,j in request_dict.items():    
                    if 1==j:
                        TSP.append(i)    
        return TSP,2*distances[0,1]
        
    else: #functie van gurobi!
        def subtourelim(model, where):
          if where == GRB.callback.MIPSOL:
            selected = []
            # make a list of edges selected in the solution
            for i in range(n):
              sol = model.cbGetSolution([model._vars[i,j] for j in range(n)])
              selected += [(i,j) for j in range(n) if sol[j] > 0.5]
            # find the shortest cycle in the selected edge list
            tour = subtour(selected)
        
            if len(tour) < n:
              # add a subtour elimination constraint
              expr = 0
              for i in range(len(tour)):
                for j in range(i+1, len(tour)):
                  expr += model._vars[tour[i], tour[j]]
              model.cbLazy(expr <= len(tour)-1)
        
        def subtour(edges):
          visited = [False]*n
          cycles = []
          lengths = []
          selected = [[] for i in range(n)]
          for x,y in edges:
            selected[x].append(y)
          while True:
            current = visited.index(False)
            thiscycle = [current]
            while True:
              visited[current] = True
              neighbors = [x for x in selected[current] if not visited[x]]
              if len(neighbors) == 0:
                break
              current = neighbors[0]
              thiscycle.append(current)
            cycles.append(thiscycle)
            lengths.append(len(thiscycle))
            if sum(lengths) == n:
              break
          return cycles[lengths.index(min(lengths))]       
        
        m = Model()
        vars = {}
        
        for i in range(n):
            for j in range(n):
                vars[i,j] = m.addVar(obj=distances[i,j],vtype = GRB.BINARY)
                vars[j,i] = vars[i,j]
                m.update()
               
        for i in range(n):
            m.addConstr(quicksum(vars[i,j] for j in range(n))==2) # there is precisely one edge entering the location and one leaving
            m.addConstr(vars[i,i]==0)
            
        m.update()    
        m._vars = vars
        m.params.LazyConstraints=1
        m.optimize(subtourelim)
        TSP = []
        if m.status == GRB.Status.OPTIMAL:
            solution = m.getAttr('x', vars)
            edges = [(i,j) for i in range(n) for j in range(n) if solution[i,j]>0.5]
            final_tour = subtour(edges)
        
    
            for v in final_tour:
                for i,j in request_dict.items():    
                    if v==j:
                        TSP.append(i)    
    
    
            return TSP,m.ObjVal


def main():
    global problem, solution
    instance_file = 'instance/VSC2019_EX01.txt'
    #instance_file = 'instance/VSC2019_ORTEC_early_%02d.txt' % INSTANCE
    output_file ='solution//VSC2019_EX01-solution.txt'
    #instance_file = 'instance/STUDENT%03d.txt' % INSTANCE
    #output_file = 'solution/VSC2019_ORTEC_early_%02d-solution.txt' % INSTANCE
    #output_file = 'solution/STUDENT%03d-solution.txt' % INSTANCE 
    
    problem = InstanceVerolog2019(instance_file)
    problem.calculateDistances() 
    solution = Solution(problem)
    
    solution.matches()

    for k in reversed(range(1,solution.Instance.Days)):
        solution.spread_requests(k)
        if solution.assign_trucks():
            if solution.assign_technicians():
                break
                
                
    solution.calculate()
    solution.writeSolution(output_file)
    
    #print(solution.spread_requests())
    
    end = time.time()
    
    print(end-start)
main()
