#! /usr/bin/env python

from InstanceVerolog2019 import InstanceVerolog2019 as InstanceVerolog2019
from SolutionVerolog2019 import SolutionVerolog2019 as SolutionVerolog2019

from analyzerVerolog2019 import Files

class Defaults(Files):
    def __init__(self):
        Files.__init__(self)
        self.nofDaySteps  = 10
        self.smallSize    = 25
        self.mediumSize   = 4*self.smallSize
        self.largeSize    = 4*self.mediumSize
        self.extraMargin  = 10
        self.inchH        = 13
        self.inchV        = 8
        self.fps          = 8
        
# https://brushingupscience.wordpress.com/2016/06/21/matplotlib-animations-the-easy-way/
def Film( instance, solution, name, parameters ):
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    import warnings
    import matplotlib.cbook
    warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)
    
    def myround(x, base=5):
        return int( base * round(float(x)/base) )   
    
    class Update(object):
        def __init__(self, ax, instance, solution, parameters ):
            self.parameters = parameters

            self.ax         = ax
            self.instance   = instance
            self.solution   = solution
            
            self.X = np.array( [loc.X for loc in instance.Locations], dtype=float )
            self.Y = np.array( [loc.Y for loc in instance.Locations], dtype=float )
            
            self.depotLocId     = 0
            self.requestLocIds  = np.array( [r.customerLocID for r in instance.Requests] ) - 1
            self.techLocIds     = np.array( [t.locationID for t in self.instance.Technicians] ) - 1

            # https://stackoverflow.com/questions/22408237/named-colors-in-matplotlib
            self.sizes                  = self.parameters.smallSize * np.ones( len(self.X) )
            self.sizes[self.techLocIds] = self.parameters.mediumSize
            self.sizes[0]               = self.parameters.largeSize
            self.linewidths             = 2 * np.ones( len(self.X) )
            self.colors                 = ['limegreen'] * len(self.sizes)
            self.colors                 = ['gold' if id in self.techLocIds else color for id,color in enumerate(self.colors) ]
            self.colors[0]              = 'aquamarine'
            self.edgecolors             = ['tomato'] * len(self.sizes)
            self.edgecolors[0]          = 'darkcyan'
            
            self.waitingFor = np.zeros( len(self.X) )

            em = self.parameters.extraMargin
            self.ax.set_xlim(myround( min(self.X)-em ), myround( max(self.X)+em ))
            self.ax.set_ylim(myround( min(self.Y)-em ), myround( max(self.Y)+em ))
 
            self.maxTruckRoutes      = 0
            self.maxTechnicianRoutes = 0   
            if not solution is None:
                self.maxTruckRoutes      = max( [ len(day.TruckRoutes) for day in solution.Days] )
                self.maxTechnicianRoutes = max( [ len(day.TechnicianRoutes) for day in solution.Days] )
            
            self.artists = []
            self.artists.append( ax.text( 0.05, 0.9, '', transform = ax.transAxes, family = 'monospace', zorder = 4, color='blue', bbox=dict(facecolor='yellow', alpha=0.2) ) )
            self.artists.append( ax.scatter( self.X, self.Y, zorder = 3 ) )
            
            from matplotlib.collections import PatchCollection
            if parameters.actionRadius:
                from matplotlib.patches import Circle
                lo = self.techLocIds
                ar = [ t.maxDayDistance/2 for t in self.instance.Technicians ]
                order = reversed( np.argsort(ar) )
                circles = [ Circle( ( self.X[lo[i]], self.Y[lo[i]] ), ar[i] ) for i in order ]
                self.artists.append( ax.add_collection( PatchCollection( circles, zorder = 0 ) ) )
            else:
                self.artists.append( ax.add_collection( PatchCollection( [], zorder = 0 ) ) )

            self.text   = 0
            self.points = 1
            self.radius = 2
            
            self.firstTruckRoute = len( self.artists )
            for i in range(self.maxTruckRoutes):
                self.artists.append( ax.plot( [], [], linewidth=6, zorder = 1 )[0] )

            self.firstTechnicianRoute = len( self.artists )
            for i in range(self.maxTechnicianRoutes):
                self.artists.append( ax.plot( [], [], linewidth=2, zorder = 2 )[0] )
          
        def frames(self):
            import itertools
            nofDays = self.instance.Days
            if solution is None:
                return [f for f in itertools.product(*[ range(nofDays), range(1) ])]
            else:
                perDay = max( [ t.maxDayDistance for t in self.instance.Technicians ] + [ self.instance.TruckMaxDistance ] )
                step = myround( perDay / self.parameters.nofDaySteps )
                return [f for f in itertools.product(*[ range(nofDays), range(0,myround(perDay+step),step) ])]
        
        def init(self):
            self.artists[ self.text ].set_text('')
            
            self.artists[ self.points ].set_sizes( self.sizes )
            self.artists[ self.points ].set_color( self.colors )
            self.artists[ self.points ].set_edgecolors( self.edgecolors )
            self.artists[ self.points ].set_linewidths( self.linewidths )
            
            self.artists[ self.radius ].set_facecolor( (0,1,0,0.08) )
            self.artists[ self.radius ].set_edgecolor( (0,0,1,0.5) )
            self.artists[ self.radius ].set_linestyle( '--' )

            if not solution is None:
                for i in range( self.firstTruckRoute, self.firstTruckRoute + self.maxTechnicianRoutes + self.maxTruckRoutes ):
                    self.artists[ i ].set_data( [], [] )
            
            return self.artists
    
        def RouteCoordinatesFromRequests( self, requests, includeDepot = True ):
            requests = np.array(requests)-1
            aux = self.requestLocIds[ requests ]
            aux[ requests < 0 ] = 0
            if not includeDepot:
                aux = aux[ aux > 0 ]
            return aux
        
        def RouteCoordinatesFromRequestsUpToStep( self, requests, home, step ):
            
            def partial( X, Y, limit ):
                def distance( x, y ):
                    from scipy.spatial import distance
                    import math
                    return int( math.ceil( distance.euclidean(x,y) ) )
                
                points = [ (x,y) for x, y in zip(X, Y) ]
                segments = np.append( 0, [ distance(p1,p2) for p1, p2 in zip(points, points[1:]) ] )
                cs = np.cumsum(segments, dtype=int)
                idx, = np.where( cs <= limit )
                if len(idx) < len(X):
                    last = idx[-1]
                    theta = ( limit - cs[last] ) * 1.0 / segments[last+1]
                    if theta > 0: 
                        X[last+1] = X[last] + theta * ( X[last+1] - X[last] )
                        Y[last+1] = Y[last] + theta * ( Y[last+1] - Y[last] )
                        idx = np.append( idx, last+1 )
                    X = X[ idx ]
                    Y = Y[ idx ]
                return X,Y
                
            route = self.RouteCoordinatesFromRequests( requests )
            route = np.append( home, route )
            route = np.append( route, home )
            return partial( self.X[ route ], self.Y[ route ], step )

        def __call__(self, day_and_step):
            i,step = day_and_step
            self.artists[ self.text ].set_text( '{:>5d}@{:<3d}'.format(step, i+1 ) )
            
            active = list( set( [ r.customerLocID-1 for r in instance.Requests if r.fromDay <= i+1 <= r.toDay ] ) )
            
            import copy            
            sizes = copy.copy( self.sizes )
            sizes[active] = self.parameters.largeSize
            self.artists[ self.points ].set_sizes( sizes )
            
            if not solution is None:
                day = self.solution.Days[i]
                if step == 0:
                    delivered = sum( [ truck.Route for truck in day.TruckRoutes ], [] )
                    installed = sum( [ technician.Route for technician in day.TechnicianRoutes ], [] )
        
                    delivered = self.RouteCoordinatesFromRequests( np.array( np.unique( delivered ), dtype=int ), False )
                    installed = self.RouteCoordinatesFromRequests( np.array( np.unique( installed ), dtype=int ) )
    
                    self.waitingFor[ installed ] = 0
                    self.waitingFor[ self.waitingFor>0 ] = self.waitingFor[ self.waitingFor>0 ] + 1
                    self.waitingFor[ delivered ] = 1
                    
                    widths = copy.copy( self.linewidths )
                    widths[self.waitingFor>0] = 2 * ( self.waitingFor[self.waitingFor>0] + 1 )
                    self.artists[ self.points ].set_linewidths( widths )

                for i in range( self.firstTruckRoute, self.firstTruckRoute + self.maxTechnicianRoutes + self.maxTruckRoutes ):
                    self.artists[ i ].set_data( [], [] )
                
                for i,truck in enumerate(day.TruckRoutes):
                    self.artists[ self.firstTruckRoute + i ].set_data( self.RouteCoordinatesFromRequestsUpToStep( truck.Route, 0, step ) )
                     
                for i,technician in enumerate(day.TechnicianRoutes):
                    person = self.instance.Technicians[technician.ID - 1]
                    self.artists[ self.firstTechnicianRoute + i ].set_data( self.RouteCoordinatesFromRequestsUpToStep( technician.Route, person.locationID-1, step ) )
                
            return self.artists
        
    if parameters.xkcd:
        from matplotlib import rcParams
        saved_state = rcParams.copy()
        plt.xkcd()
        
    fig = plt.figure()
    plt.axis( 'equal' )
    ax  = plt.axes()
    ud  = Update( ax, instance, solution, parameters )
    
    fig.set_size_inches( ud.parameters.inchH, ud.parameters.inchV )
    ani = animation.FuncAnimation( fig, ud, frames = ud.frames(), init_func = ud.init, blit = True )
    
    name = name.rsplit('.', 1)[0]
    
    # install http://www.imagemagick.org/script/download.php#windows for ffmpeg and other writers. 
    if ud.parameters.mp4:    
        FFwriter = animation.FFMpegWriter( fps=ud.parameters.fps, extra_args=['-vcodec', 'libx264'] )
        ani.save( name + '.mp4', writer = FFwriter )    

    if ud.parameters.html:    
        ani.save( name + ".htm", writer="html" )
     
    if ud.parameters.pdf:    
        from matplotlib.backends.backend_pdf import PdfPages
        with PdfPages( name + '.pdf' ) as pdf:    
            ud.init()
            for f in ud.frames():
                ud(f)
                plt.show()
                pdf.savefig(fig)
    
    plt.show()
    plt.close()
    
    if parameters.xkcd:
        from matplotlib import rcParams
        rcParams.update( saved_state )
        
def main(parameters):
    for i,sol in enumerate( parameters.solutions ):
        instance = InstanceVerolog2019( parameters.instances[i], parameters.GetIType() )   
        if sol is not None:
            solution = SolutionVerolog2019( sol, instance, parameters.GetType() )
            name = sol
        else:
            solution = None
            name = parameters.instances[i]
        Film( instance, solution, name, parameters )

import argparse
if __name__ == '__main__':    
    try:
        parameters = Defaults()
        
        parser = argparse.ArgumentParser( description='Read and visualize instance, maybe with solution file.' )
        parser.add_argument( '--solution', '-s', metavar='SOLUTION_FILE', help='The solution file' )
        parser.add_argument( '--instance', '-i', metavar='INSTANCE_FILE', help='The instance file' )
        parser.add_argument( '--xkcd', action='store_true', help='draw in xkcd style' )
        parser.add_argument( '--nofDaySteps', type=int, help='Provide number of day steps, default %s' % parameters.nofDaySteps )
        parser.add_argument( '--smallSize', type=int, help='Provide small size of locations, default %s' % parameters.smallSize )
        parser.add_argument( '--mediumSize', type=int, help='Provide medium size of locations, default %s' % parameters.mediumSize )
        parser.add_argument( '--largeSize', type=int, help='Provide large size of locations, default %s' % parameters.largeSize )
        parser.add_argument( '--extraMargin', type=int, help='Provide extra margin to plot, default %s' % parameters.extraMargin )
        parser.add_argument( '--inchH', type=int, help='Provide horizontal size in inches, default %s' % parameters.inchH )
        parser.add_argument( '--inchV', type=int, help='Provide vertical size in inches, default %s' % parameters.inchV )
        parser.add_argument( '--fps', type=int, help='Provide number of frames per second for mp4, default %s' % parameters.fps )
        parser.add_argument( '--actionRadius', action='store_true', help='show action radius of technicians' )
        parser.add_argument( '--mp4', action='store_true', help='animate to mp4' )
        parser.add_argument( '--html', action='store_true', help='animate to html' )
        parser.add_argument( '--pdf', action='store_true', help='animate to multipage pdf' )
    
        parameters.SetFromCommandLine( parser.parse_args() )
                
        if not parameters.instance is None:
            main(parameters)
    except SystemExit:
        print()
    except:
        raise