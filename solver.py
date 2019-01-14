# Vehicle Routing

from InstanceVerolog2019 import InstanceVerolog2019

INSTANCE = 2

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
# step 4: assign request to truck routes.

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
            self.NumberOfTrucks = 0
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

        for technician in self.Instance.Technicians:
            self.TechnicianMatches[technician.ID] = []

        for request in self.Instance.Requests:
            self.RequestMatches[request.ID] = []
            for technician in self.Instance.Technicians:
                if technician.capabilities[request.machineID - 1]:
                    if 2 * self.Instance.calcDistance[request.customerLocID - 1][technician.locationID - 1] <= technician.maxDayDistance:
                        self.RequestMatches[request.ID].append(technician)
                        self.TechnicianMatches[technician.ID].append(request)

        for request in self.Instance.Requests:
            print(request.ID, end = ' - ')
            for technician in self.RequestMatches[request.ID]:
                print(technician.ID, end = ' ')
            print()

        for technician in self.Instance.Technicians:
            print(technician.ID, end = ' - ')
            for request in self.TechnicianMatches[technician.ID]:
                print(request.ID, end = ' ')
            print()


    def progress(self):
        print('Request  Delivery  Installment  Idle time')
        for request in self.Instance.Requests:
            idleTime = 0
            if self.RequestInstallmentDays[request.ID] > self.RequestDeliveryDays[request.ID] and self.RequestDeliveryDays[request.ID] > 0:
                idleTime = self.RequestInstallmentDays[request.ID] - self.RequestDeliveryDays[request.ID] - 1
            print('%6d  %8d  %11d  %9d' % (request.ID, self.RequestDeliveryDays[request.ID], self.RequestInstallmentDays[request.ID], idleTime))

def main():
    global problem, solution
    instance_file = 'data/STUDENT%03d.txt' % INSTANCE
    output_file = 'solution/STUDENT%03d-solution.txt' % INSTANCE
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

    """
    solution.Days[0].TruckRoutes.append(Solution.TruckRoute(1))
    solution.Days[0].TruckRoutes.append(Solution.TruckRoute(2))
    solution.Days[0].TruckRoutes[0].RequestIDs.append(7)
    solution.Days[0].TruckRoutes[0].RequestIDs.append(2)
#    solution.Days[0].TruckRoutes[0].RequestIDs.append(9)
    solution.Days[0].TruckRoutes[1].RequestIDs.append(12)
    solution.Days[2].TechnicianRoutes.append(Solution.TechnicianRoute(2))
#    solution.Days[2].TechnicianRoutes[0].RequestIDs.append(7)
#    solution.Days[2].TechnicianRoutes[0].RequestIDs.append(9)
    solution.Days[2].TechnicianRoutes[0].RequestIDs.append(2)
    """

    solution.calculate()
    solution.progress()
    solution.matches()

    solution.writeSolution(output_file)

if __name__ == "__main__":
    main()
