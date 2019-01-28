    def distances_creator(self,requests,homeID): # input: een verzameling requests, en een ID (kan depot ID zijn (0) of een locationID voor technician)
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
            distances [request_dict[i],0] = distances [0,request_dict[i]] =self.Instance.calcDistance[i.customerLocID-1][homeID]
        distances[0,0] = 0   
        return n,distances,request_dict 
    
    
        def merge_routes(self): #merges routes, without going back to depot
        for day in range(1,self.Instance.Days+1):
            unconsidered = self.Days[day-1].TruckRoutes[:]
            
            for route_a in unconsidered:
                weight_a = 0
                unconsidered.remove(route_a)
                
                for requestID in route_a.RequestIDs:
                    request = self.getRequest(requestID)
                    weight_a += request.amount*self.getMachine(request.machineID).size
                    
                for route_b in unconsidered:
                    weight_b = 0
                    
                    for requestID in route_b.RequestIDs:
                        request = self.getRequest(requestID)
                        weight_b += request.amount*self.getMachine(request.machineID).size
                        
                    if weight_a + weight_b <=self.Instance.TruckCapacity:
                        mergedIDs = route_a.RequestIDs + route_b.RequestIDs
                        mergedRequests = []
                        
                        for ID in mergedIDs:
                            mergedRequests.append(self.getRequest(ID))
                        arg = self.distances_creator(mergedRequests,0)
                        merged_tour = tsp(arg[0],arg[1],arg[2])
                        
                        if merged_tour[1]<= self.Instance.TruckMaxDistance:
                            self.Days[day-1].TruckRoutes.remove(route_a)
                            
                            self.Days[day-1].TruckRoutes.remove(route_b)
                            
                    
                            unconsidered.remove(route_b)
                            
                            self.Days[day-1].TruckRoutes.append(self.TruckRoute(route_a.TruckID)) #maak nieuwe truckroute, met ID van a
                            self.Days[day-1].TruckRoutes[-1].RequestIDs = mergedIDs
                    
                            unconsidered.append(self.Days[day-1].TruckRoutes[-1]) 
                            break
                    
def tsp(n, distances,request_dict):  
    
    if n <= 2: # tsp alg werkt niet voor n=2
        TSP = []
        for i,j in request_dict.items():    
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