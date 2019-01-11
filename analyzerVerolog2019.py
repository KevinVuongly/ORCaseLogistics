#! /usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt

from InstanceVerolog2019 import InstanceVerolog2019 as InstanceVerolog2019
from SolutionVerolog2019 import SolutionVerolog2019 as SolutionVerolog2019

class Base(object):
    def GetIType(self):
        return 'txt'
    def GetType(self):
        return 'txt'
    def __str__(self):
        return '\n'.join( str(k) + ': ' + str(v) for k,v in sorted(self.__dict__.items()) )
    def SetFromArgument( self, args ):
        self.__dict__.update( (k,v) for k,v in args.__dict__.items() if v is not None )

class Files(Base):
    def __init__(self):
        Base.__init__(self)
        self.instance  = None
        self.solution  = None
        self.instances = []
        self.solutions = []
        self.names     = []
                
    def SetFromCommandLine( self, args ):
        def GetNofMask( fileMask ):
            return ( fileMask or '' ).count('*')
        
        def GetPathAndName( fileName ):
            import os.path
            return os.path.splitext(fileName)[0]
        
        def GetExtension( fileName ):
            import os.path
            return os.path.splitext(fileName)[1][1:]
        
        def GetPath( fileName ):
            import os.path
            return os.path.split(fileName)[0] + '/'

        def GetFile( fileName ):
            import os.path
            return os.path.split(fileName)[1] 
        
        def GetFiLeNameWithoutExtension( fileMask ):
            return GetFile( GetPathAndName(fileMask) )
        
        def GetAllFromMask( fileMask, nofMask ):
            import pathlib
            fileMask = str( pathlib.Path(fileMask) )
            import glob
            files = glob.glob( fileMask )
            listofparts = [ s.rsplit('\\') for s in files ]
            from operator import itemgetter
            listofparts = sorted(listofparts, key=itemgetter(nofMask,1))
            files = [ '/'.join(s) for s in listofparts ]
            names = [ GetFiLeNameWithoutExtension(s) for s in files ]
            return files, names
        
        def GetAll( solutionDescription, instancesFolder ):
            nofMask = GetNofMask( solutionDescription )
            if nofMask > 0:
                solutions, names = GetAllFromMask( solutionDescription, nofMask )
                instances = [ GetPath(instancesFolder) + name + '.txt' for name in names ]
            else:
                nofMask = GetNofMask( instancesFolder )
                if nofMask > 0:
                    instances, names = GetAllFromMask( instancesFolder, nofMask )
                    solutions = [ solutionDescription ] * len( instances )
                else:
                    solutions = [ solutionDescription ]
                    name = GetFiLeNameWithoutExtension(instancesFolder)
                    if len(name) == 0:
                        name = GetFiLeNameWithoutExtension(solutionDescription)
                    names = [ name ]
                    if instancesFolder is None or instancesFolder.endswith('.txt'):
                        instances = [ instancesFolder ]
                    else:
                        instances = [ GetPath(instancesFolder) + name + '.txt' ]
            return solutions, instances, names
        
        self.SetFromArgument( args )
        self.solutions, self.instances, self.names = GetAll( self.solution, self.instance )

def main(parameters):

    def GetInstanceData( instance ):
        days = np.arange( instance.Days )
        weights = np.array( [ 0,
                              1,
                              instance.TechnicianDayCost,
                              instance.TechnicianCost,
                              instance.TruckDayCost,
                              instance.TruckCost,
                              instance.TechnicianDistanceCost,
                              instance.TruckDistanceCost ] )
        labels = ["TotalCost", "IdleMachineCost", "NrTechnicianDays", "NrTechniciansUsed", "NrTruckDays", "NrTrucksUsed", "TechnicianDistance", "TruckDistance"]
        return days, weights, labels
    
    def GetCummulativeValues(solution):
        parts = np.array( [ solution.calcCost.CostCumulative,
                            solution.calcCost.IdleMachineCostCumulative,
                            solution.calcCost.NrTechnicianDaysCumulative,
                            solution.calcCost.NrTechniciansUsedCumulative,    
                            solution.calcCost.NrTruckDaysCumulative,
                            solution.calcCost.NrTrucksUsedCumulative,
                            solution.calcCost.TechnicianDistanceCumulative,
                            solution.calcCost.TruckDistanceCumulative ] )
        return parts
    
    def DrawWeights( weights, labels, name, ax ):
        w   = weights[1:]
        pos = range(len(w)) 
            
        ax.barh(pos, w )
        ax.set_yticks( pos )
        ax.set_yticklabels(labels[1:])
        ax.invert_yaxis()  # labels read top-to-bottom
        ax.set_xlabel('Weights')
        ax.set_title(name)
        for i, v in enumerate(w):
            if 3*v > max(w):
                ax.text(v, i, str(v)+" ", color='white', va='center', ha="right", fontweight='bold')
            else:
                ax.text(v, i, " "+str(v), color='blue', va='center', fontweight='bold')
    
    def DrawCosts( parts, labels, ticks, ticklabels, name, label, ax ):
        ax.stackplot(ticks, parts[1:,:], labels = labels[1:], baseline='zero')
        ax.set_xticks( ticks )
        ax.set_xticklabels( ticklabels )
        ax.legend(loc=2, prop={'size': 'medium'})
        ax.set_xlabel(label)
        ax.grid(which='both')
        return ax
    
    def Draw(days,weights,parts,labels,name,sol):
        fig = plt.figure()
        fig.set_size_inches( 18, 6 )
          
        ticks = np.arange(0, len(parts[0]), 1)
        ticklabels = ["{:02d}".format(x) for x in ticks+1]
        
        ax1 = plt.subplot(2,3,(1,2))
        ax2 = plt.subplot(2,3,(3,6))
        ax3 = plt.subplot(2,3,(4,5))
    
        DrawWeights( weights, labels, name, ax2 )
        DrawCosts( np.dot( np.diag(weights), parts ), labels, ticks, ticklabels, name, 'Weighted', ax1 )
        DrawCosts( parts, labels, ticks, ticklabels, name, 'Vanilla', ax3 )
           
        plt.tight_layout()
        return fig, ticks, ticklabels
    
    for i,sol in enumerate( parameters.solutions ):
        instance = InstanceVerolog2019( parameters.instances[i], parameters.GetIType() )    
        if not sol is None:
            solution = SolutionVerolog2019( sol, instance, parameters.GetType() )
            name = sol
        else:
            solution = None
            name = parameters.instances[i]
        if not solution == None and not solution.isValid():
            print( sol + ' invalid for ' + parameters.names[i] )
            print( '\t' + '\n\t'.join(solution.errorReport) )
            if len(solution.warningReport) > 0:
                print( '\t' + '\n\t'.join(solution.warningReport) )
        else:
            print( name )
            if parameters.verbose or parameters.show or parameters.pdf:
                figures = []
                days, weights, labels = GetInstanceData(instance)
                if not solution is None:
                    parts = GetCummulativeValues(solution)
                    fig, ticks, ticklabels = Draw( days, weights, parts, labels, name, sol )
                    figures.append(fig)
                    fig, ax = plt.subplots()
                    fig.set_size_inches( 18, 5 )
                    figures.append(fig)
                    DrawCosts( np.dot( np.diag(weights), parts ), labels, ticks, ticklabels, name, 'Weighted', ax )
                    fig, ax = plt.subplots()
                    fig.set_size_inches( 18, 5 )
                    figures.append(fig)
                    DrawCosts( parts, labels, ticks, ticklabels, name, 'Vanilla', ax )
                fig, ax = plt.subplots()
                fig.set_size_inches( 13, 5 )
                figures.append(fig)
                DrawWeights( weights, labels, name, ax )

                if parameters.verbose:
                    print('\t' + '\n\t'.join(str(solution.calcCost).split('\n')))
                    np.set_printoptions(edgeitems=5,infstr='inf', linewidth=200, nanstr='nan', precision=0, suppress=False, threshold=100, formatter=None )
                    print( parts )
                if parameters.show:
                    plt.show()
                if parameters.pdf:
                    from matplotlib.backends.backend_pdf import PdfPages
                    with PdfPages( name + '.pdf' ) as pdf:    
                        for fig in figures:                    
                            pdf.savefig(fig)

                for fig in figures:                    
                    plt.close(fig)
              

if __name__ == '__main__':    
    try:
        import argparse
        parameters = Files()
        
        parser = argparse.ArgumentParser( description='Read and analyze a instance or solution file.' )
        parser.add_argument( '--solution', '-s', metavar='SOLUTION_FILE', help='The solution file or mask of several files' )
        parser.add_argument( '--instance', '-i', metavar='INSTANCE_FILE', help='The single instance file of folder in case of several solutions' )
        parser.add_argument( '--pdf', action='store_true', help='save figure to pdf' )
        parser.add_argument( '--show', action='store_true', help='show figure in console' )
        parser.add_argument( '--verbose', action='store_true', help='show commulative costs as text in the console' )
    
        parameters.SetFromCommandLine( parser.parse_args() )
        
        if not parameters.instance is None:
            main(parameters)
    except SystemExit:
        print()
    except:
        raise