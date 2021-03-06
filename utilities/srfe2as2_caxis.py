import readncnr3 as readncnr
import numpy as N
import scriptutil as SU
import re
import simple_combine
import copy
import os
import pylab
pi=N.pi
from matplotlib.mlab import griddata
import matplotlib.ticker as ticker
import sys
from numpy import ma
from mpfit import mpfit
from scipy.optimize import curve_fit
from findpeak3 import findpeak
from openopt import NLP
import scipy.optimize
import scipy.odr
import scipy.sandbox.delaunay as D
from mpl_toolkits.axes_grid.inset_locator import inset_axes




from math import fmod
import numpy

import matplotlib.cbook as cbook
import matplotlib.transforms as transforms
import matplotlib.artist as artist
import matplotlib.patches as patches
from matplotlib.path import Path
from matplotlib.ticker import MaxNLocator,MultipleLocator, FormatStrFormatter
pylab.rc("axes", linewidth=2.0)

class Ring(patches.Patch):
    """
    Ring patch.
    """
    def __str__(self):
        return "Ring(%g,%g,%g,%g)"%(self.r1,self.r2,self.theta1,self.theta2)

    def __init__(self,
                 center=(0,0),
                 r1=0,
                 r2=None,
                 theta1=0,
                 theta2=360,
                 **kwargs
                 ):
        """
        Draw a ring centered at *x*, *y* center with inner radius *r1* and
        outer radius *r2* that sweeps *theta1* to *theta2* (in degrees).

        Valid kwargs are:

        %(Patch)s
        """
        patches.Patch.__init__(self, **kwargs)
        self.center = center
        self.r1, self.r2 = r1,r2
        self.theta1, self.theta2 = theta1,theta2

        # Inner and outer rings are connected unless the annulus is complete
        delta=abs(theta2-theta1)
        if fmod(delta,360)<=1e-12*delta:
            theta1,theta2 = 0,360
            connector = Path.MOVETO
        else:
            connector = Path.LINETO

        # Form the outer ring
        arc = Path.arc(theta1,theta2)

        if r1 > 0:
            # Partial annulus needs to draw the outter ring
            # followed by a reversed and scaled inner ring
            v1 = arc.vertices
            v2 = arc.vertices[::-1]*float(r1)/r2
            v = numpy.vstack([v1,v2,v1[0,:],(0,0)])
            c = numpy.hstack([arc.codes,arc.codes,connector,Path.CLOSEPOLY])
            c[len(arc.codes)]=connector
        else:
            # Wedge doesn't need an inner ring
            v = numpy.vstack([arc.vertices,[(0,0),arc.vertices[0,:],(0,0)]])
            c = numpy.hstack([arc.codes,[connector,connector,Path.CLOSEPOLY]])

        v *= r2
        v += numpy.array(center)
        self._path = Path(v,c)
        self._patch_transform = transforms.IdentityTransform()
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd

    def get_path(self):
        return self._path









def grid(x,y,z):
    xmesh_step=.1
    ymesh_step=.5
    #mxrange=N.linspace(x.min(),x.max(),100)
    #yrange=N.linspace(y.min(),y.max(),100)
    #print xrange
    #print yrange
    #print x
    xi,yi=N.mgrid[x.min():x.max():xmesh_step,y.min():y.max():ymesh_step]
    #blah
    # triangulate data
    #tri = D.Triangulation(N.copy(x),N.copy(y))
    #print 'before interpolator'
    ## interpolate data
    #interp = tri.nn_interpolator(z)
    #print 'interpolator reached'
    #zi = interp(xi,yi)
    print 'xi',xi.shape
    print yi.shape
    zm=ma.masked_where(z<3000,z)
    x=copy.deepcopy(x[:,z<500.0])
    y=copy.deepcopy(y[:,z<500.0])
    z=copy.deepcopy(z[:,z<500.0])
    zi = griddata(x,y,z,xi,yi)
    print 'zi',zi.shape
    print xi
    print yi
    return xi,yi,zi



def readfiles(flist,mon0=None):
    mydatareader=readncnr.datareader()
    #Qx=N.array([])
    #Qy=N.array([])
    #Qz=N.array([])
    #tth=N.array([])
    #Counts=N.array([])
    #T=N.array([])
    tth=[]
    Counts=[]
    Counts_err=[]
    T=[]
    i=0
    for currfile in flist:
        #print currfile
        mydata=mydatareader.readbuffer(currfile)
        #print mydata.data.keys()
        if i==0:
            if mon0==None:
                mon0=mydata.metadata['count_info']['monitor']
        #a=mydata.metadata['lattice']['a']
        #b=mydata.metadata['lattice']['b']
        #c=mydata.metadata['lattice']['c']
        mon=mydata.metadata['count_info']['monitor']
        wl=2.35916
        #c=2*wl/N.sin(N.deg2rad(N.array(tth))/2)
        #tth.append(2*wl/N.sin(N.deg2rad(N.array(mydata.data['a4'])/2)))
        tth.append(N.array(mydata.data['a4']))
        Counts.append(N.array(mydata.data['counts'])*mon0/mon)
        Counts_err.append(N.sqrt(N.array(mydata.data['counts']))*mon0/mon)
        #T.append(N.array(mydata.data['temp'])) #What we probably want
        Tave=N.array(mydata.data['temp']).mean()
        T.append(N.ones(tth[i].size)*Tave)
        #Qx=N.concatenate((Qx,N.array(mydata.data['qx'])*2*pi/a))
        #Qy=N.concatenate((Qy,N.array(mydata.data['qy'])*2*pi/b))
        #Qz=N.concatenate((Qz,N.array(mydata.data['qz'])*2*pi/c))
        #tth=N.concatenate((tth,N.array(mydata.data['a4'])))
        #Counts=N.concatenate((Counts,N.array(mydata.data['counts'])*mon0/mon))
        #T=N.concatenate((T,N.array(mydata.data['temp'])))

        i=i+1
    #xa,ya,za=prep_data2(Qx,Qy,Counts);
    #print 'xa',xa.min(),xa.max()
    #print 'qx',Qx.min(),Qx.max()
        #x,y,z=grid(Qx,Qz,Counts)
    return tth,T,Counts,Counts_err,mon0



def regrid(x,y,z):
    print len(x)
    currmax=x[0].max()
    currmin=x[0].min()
    for currx in x:
        currmax=max([currx.max(),currmax])
        currmin=min([currx.min(),currmin])

    step=N.abs(x[0][0]-x[0][1])
    print currmin, currmax,step
    proto_x=N.arange(currmin,currmax+step,step)
    print 'proto', proto_x
    for i in range(len(x)):
        currx=x[i]
        curry=y[i]
        currz=z[i]
        if len(currx)<len(proto_x):
            lendiff=len(proto_x)-len(currx)
            lenorig=len(x[i])
            x[i]=copy.deepcopy(proto_x)
            newy=N.array(proto_x[:])
            newy[:lenorig]=curry[:]
            newy[lenorig:]=N.ones(lendiff)*curry[-1] #set padded temps to the same value as the end of the actual array
            newz=ma.array(copy.deepcopy(proto_x[:]))
            newz[:lenorig]=currz[:]
            newz[lenorig:]=N.ones(lendiff)*N.nan #set padded counts to nan
            y[i]=copy.deepcopy(newy)
            z[i]=copy.deepcopy(newz)
            #print "min", x[i].min()





    #sys.exit()
    x=N.array(x).flatten()
    y=N.array(y).flatten()
    z=N.array(z).flatten()
    return x,y,z





def regrid2(x,y,z):
    print len(x)
    currmax=x[0].max()
    currmin=x[0].min()
    for currx in x:
        currmax=max([currx.max(),currmax])
        currmin=min([currx.min(),currmin])

    step=N.abs(x[0][0]-x[0][1])
    print currmin, currmax,step
    proto_x=N.arange(currmin,currmax+step,step)
    print 'proto', proto_x
    for i in range(len(x)):
        currx=x[i]
        curry=y[i]
        currz=z[i]
        if len(currx)<len(proto_x):
            lendiff=len(proto_x)-len(currx)
            lenorig=len(x[i])
            x[i]=copy.deepcopy(proto_x)
            newy=N.array(proto_x[:])
            newy[:lenorig]=curry[:]
            newy[lenorig:]=N.ones(lendiff)*curry[-1] #set padded temps to the same value as the end of the actual array
            newz=ma.array(copy.deepcopy(proto_x[:]))
            newz[:lenorig]=currz[:]
            newz_mask=N.zeros(newz.shape)
            newz[lenorig:]=N.ones(lendiff)*N.nan #set padded counts to nan
            newz_mask[lenorig:]=N.ones(lendiff)  #mask these values
            newz.mask=newz_mask
            y[i]=copy.deepcopy(newy)
            z[i]=copy.deepcopy(newz)
            #print "min", x[i].min()
        else:
            newz=ma.array(copy.deepcopy(proto_x[:]))
            newz[:]=currz[:]
            newz_mask=N.zeros(newz.shape)
            newz.mask=newz_mask
            z[i]=copy.deepcopy(newz)





    #sys.exit()
    #x=N.array(x).flatten()
    #y=N.array(y).flatten()
    #z=N.array(z).flatten()
    return x,y,z


def fitpeak(x,y,yerr):
    maxval=x.max()
    minval=x.min()
    diff=y.max()-y.min()-y.mean()
    sig=y.std()
    print 'diff',diff,'std',sig
    if diff-1*sig>0:
        #the difference between the high and low point and
        #the mean is greater than 3 sigma so we have a signal
        p0=findpeak(x,y,2)
        print 'p0',p0
        #Area center width Bak area2 center2 width2
        center1=p0[0]
        width1=p0[1]
        center2=p0[2]
        width2=p0[3]
        sigma=width/2/N.sqrt(2*N.log(2))
        ymax=maxval-minval
        area=ymax*(N.sqrt(2*pi)*sigma)
        print 'ymax',ymax
        pin=[area,center1,width1,0,area,center2,width2]





        if 1:
            p = NLP(chisq, pin, maxIter = 1e3, maxFunEvals = 1e5)
            #p.lb=lowerm
            #p.ub=upperm
            p.args.f=(x,y,yerr)
            p.plot = 0
            p.iprint = 1
            p.contol = 1e-5#3 # required constraints tolerance, default for NLP is 1e-6

# for ALGENCAN solver gradtol is the only one stop criterium connected to openopt
# (except maxfun, maxiter)
# Note that in ALGENCAN gradtol means norm of projected gradient of  the Augmented Lagrangian
# so it should be something like 1e-3...1e-5
            p.gradtol = 1e-5#5 # gradient stop criterium (default for NLP is 1e-6)
    #print 'maxiter', p.maxiter
    #print 'maxfun', p.maxfun
            p.maxIter=50
#    p.maxfun=100

    #p.df_iter = 50
            p.maxTime = 4000
    #r=p.solve('scipy_cobyla')
        #r=p.solve('scipy_lbfgsb')
            #r = p.solve('algencan')
            print 'ralg'
            r = p.solve('ralg')
            print 'done'
            pfit=r.xf
            print 'pfit openopt',pfit
            print 'r dict', r.__dict__
        if 1:
            print 'mpfit'
            p0=pfit
            parbase={'value':0., 'fixed':0, 'limited':[0,0], 'limits':[0.,0.]}
            parinfo=[]
            for i in range(len(p0)):
                parinfo.append(copy.deepcopy(parbase))
            for i in range(len(p0)):
                parinfo[i]['value']=p0[i]
            fa = {'x':x, 'y':y, 'err':yerr}
            #parinfo[1]['fixed']=1
            #parinfo[2]['fixed']=1
            m = mpfit(myfunct_res, p0, parinfo=parinfo,functkw=fa)
            if (m.status <= 0):
                print 'error message = ', m.errmsg
            params=m.params
            pfit=params
            perror=m.perror
            #chisqr=(myfunct_res(m.params, x=th, y=counts, err=counts_err)[1]**2).sum()
            chisqr=chisq(pfit,x,y,yerr)
            dof=m.dof
            #Icalc=gauss(pfit,th)
            #print 'mpfit chisqr', chisqr
        ycalc=gauss(pfit,x)

        if 1:
            width_x=N.linspace(p0[0]-p0[1],p0[0]+p0[1],100)
            width_y=N.ones(width_x.shape)*(maxval-minval)/2
            pos_y=N.linspace(minval,maxval,100)
            pos_x=N.ones(pos_y.shape)*p0[0]
            if 0:

                pylab.errorbar(th,counts,counts_err,marker='s',linestyle='None',mfc='black',mec='black',ecolor='black')
                pylab.plot(width_x,width_y)
                pylab.plot(pos_x,pos_y)
                pylab.plot(x,ycalc)
                pylab.show()

    else:
        #fix center
        #fix width
        print 'no peak'
        #Area center width Bak
        area=0
        center=x[len(x)/2]
        width=(x.max()-x.min())/5.0  #rather arbitrary, but we don't know if it's the first.... #better to use resolution
        Bak=y.mean()
        p0=N.array([area,center,width,Bak],dtype='float64')  #initial conditions
        parbase={'value':0., 'fixed':0, 'limited':[0,0], 'limits':[0.,0.]}
        parinfo=[]
        for i in range(len(p0)):
            parinfo.append(copy.deepcopy(parbase))
        for i in range(len(p0)):
            parinfo[i]['value']=p0[i]
        fa = {'x':x, 'y':y, 'err':yerr}
        parinfo[1]['fixed']=1
        parinfo[2]['fixed']=1
        m = mpfit(myfunct_res, p0, parinfo=parinfo,functkw=fa)
        if (m.status <= 0):
            print 'error message = ', m.errmsg
        params=m.params
        pfit=params
        perror=m.perror
        #chisqr=(myfunct_res(m.params, x=th, y=counts, err=counts_err)[1]**2).sum()
        chisqr=chisq(pfit,x,y,yerr)
        dof=m.dof
        ycalc=gauss(pfit,x)
        #print 'perror',perror
        if 0:
            pylab.errorbar(x,y,yerr,marker='s',linestyle='None',mfc='black',mec='black',ecolor='black')
            pylab.plot(x,ycalc)
            pylab.show()

    print 'final answer'
    print 'perror', 'perror'
    #If the fit is unweighted (i.e. no errors were given, or the weights
    #   were uniformly set to unity), then .perror will probably not represent
    #the true parameter uncertainties.

    #   *If* you can assume that the true reduced chi-squared value is unity --
    #   meaning that the fit is implicitly assumed to be of good quality --
    #   then the estimated parameter uncertainties can be computed by scaling
    #   .perror by the measured chi-squared value.

    #      dof = len(x) - len(mpfit.params) # deg of freedom
    #      # scaled uncertainties
    #      pcerror = mpfit.perror * sqrt(mpfit.fnorm / dof)

    print 'params', pfit
    print 'chisqr', chisqr  #note that chisqr already is scaled by dof
    pcerror=perror*N.sqrt(m.fnorm / m.dof)#chisqr
    print 'pcerror', pcerror

    integrated_intensity=N.abs(pfit[0])
    integrated_intensity_err=N.abs(pcerror[0])
    ycalc=gauss(pfit,x)
    print 'perror',perror
    if 1:
        pylab.figure()
        pylab.errorbar(x,y,yerr,marker='s',linestyle='None',mfc='black',mec='black',ecolor='black')
        pylab.plot(x,ycalc)
        #qstr=str(qnode.q['h_center'])+','+str(qnode.q['k_center'])+','+str(qnode.q['l_center'])
        #pylab.title(qstr)
        pylab.show()

    return pfit,perror,pcerror,chisq



def gauss(p,x):
    #Area center width Bak area2 center2 width2

    #p=[p0,p1,p2,p3]


    x0=p[1]
    width=p[2]
    sigma=width/2/N.sqrt(2*N.log(2))
    area=N.abs(p[0])/N.sqrt(2*pi)/sigma
    background=N.abs(p[3])
    center2=p[5]
    width2=p[6]
    sigma2=width2/2/N.sqrt(2*N.log(2))
    area2=N.abs(p[3])/N.sqrt(2*pi)/sigma2
    y=background+area*N.exp(-(0.5*(x-x0)*(x-x0)/sigma/sigma))
    y=y+area2*N.exp(-(0.5*(x-center2)*(x-center2)/sigma2/sigma2))
    return y



def chisq(p,a3,I,Ierr):
    Icalc=gauss(p,a3)
    #print I.shape
    #print Ierr.shape
    #print a3.shape
    #print Icalc.shape
    Ierr_temp=copy.deepcopy(Ierr)
    zero_loc=N.where(Ierr==0)[0]
    if len(zero_loc)!=0:
        Ierr_temp[zero_loc]=1.0
    chi=((I-Icalc)/Ierr_temp)**2
    return chi.sum()/(len(I)-len(p))


def myfunct_res(p, fjac=None, x=None, y=None, err=None):
    # Parameter values are passed in "p"
    # If fjac==None then partial derivatives should not be
    # computed.  It will always be None if MPFIT is called with default
    # flag.
    model = gauss(p, x)
    # Non-negative status value means MPFIT should continue, negative means
    # stop the calculation.
    status = 0
    Ierr_temp=copy.deepcopy(err)
    zero_loc=N.where(err==0)[0]
    if len(zero_loc)!=0:
        Ierr_temp[zero_loc]=1.0
    return [status, (y-model)/Ierr_temp]



def prep_data2(xt,yt,zorigt,interpolate_on=True):
#    Data=pylab.load(r'c:\resolution_stuff\1p4K.iexy')
    #Data=pylab.load(filename)
    #xt=Data[:,2]
    #yt=Data[:,3]
    #zorigt=Data[:,0]
    xt=N.array(xt).flatten()
    yt=N.array(yt).flatten()
    zorigt=N.array(zorigt).flatten()

    x=xt[:,zorigt>0.0]
    y=yt[:,zorigt>0.0]
    z=zorigt[:,zorigt>0.0]
#    zorig=ma.array(zorigt)
    print 'reached'
    threshold=0.0;
#    print zorigt < threshold
#    print N.isnan(zorigt)
#    z = ma.masked_where(zorigt < threshold , zorigt)
    print 'where masked ', z.shape
#should be commented out--just for testing
##    x = pylab.randn(Nu)/aspect
##    y = pylab.randn(Nu)
##    z = pylab.rand(Nu)
##    print x.shape
##    print y.shape
    # Grid
    print x.min()
    print x.max()
    print y.min()
    print y.max()
    print x.shape
    xmesh_step=0.02
    ymesh_step=0.5
    xi,yi=N.mgrid[x.min():x.max():xmesh_step,y.min():y.max():ymesh_step]
    #blah
    # triangulate data
    tri = D.Triangulation(N.copy(x),N.copy(y))
    print 'before interpolator'
    # interpolate data
    interp = tri.nn_interpolator(z)
    print 'interpolator reached'
    zi = interp(xi,yi)
    # or, all in one line
    #    zi = Triangulation(x,y).nn_interpolator(z)(xi,yi)
#    return x,y,z
    if interpolate_on==False:
        #print "off"
        #print xi.shape
        #print N.reshape(x,(15,31))
        xi=N.reshape(x,(15,31))
        yi=N.reshape(y,(15,31))
        zi=N.reshape(z,(15,31))
        #print zi2-zi
        #blah
        print "interpolation off"
    return xi,yi,zi

def prep_data3(xt,yt,zt):
#    Data=pylab.load(r'c:\resolution_stuff\1p4K.iexy')
    #Data=pylab.load(filename)
    #xt=Data[:,2]
    #yt=Data[:,3]
    #zorigt=Data[:,0]
    xt=N.array(xt).flatten()
    yt=N.array(yt).flatten()
    zt=N.array(zt).flatten()
    xi = N.linspace(xt.min(),xt.max(),2*len(xt)/45)
    yi = N.linspace(yt.min(),yt.max(),2*len(yt)/45)
    print 'gridding'
    zi = griddata(xt,yt,zt,xi,yi)
    print 'gridded'
    return xi,yi,zi


if __name__=='__main__':


    if 1:
        myfilebase='ordp10'
        mydirectory=r'C:\CaFe4As\Bt9\CaFe4As3\May11_2009'
        mydirectory=r'C:\srfeas\Feb27_2009'
        myfilebase='split0'
        myend='bt9'
        myfilebaseglob=myfilebase+'*.'+myend
        filerange1=range(1,10)
        #filerange1.append(7)
        #filerange1.append(8)
        #filerange1.append(9)
        filerange2=range(10,46)
        filerange3=range(45,52)
        #mydirectory=r'C:\srfeas\SrFeAsNi\Ni0p08\2009-04-diffraction'
        #file_range=(35,51)
        #myfilebase='SrFeA0'
        flist=[]

        for i in filerange1:
            currfile=os.path.join(mydirectory,myfilebase+str(0)+str(i)+r"."+myend)
            print 'currfile',currfile
            flist.append(currfile)
        for i in filerange2:
            currfile=os.path.join(mydirectory,myfilebase+str(i)+r"."+myend)
            print 'currfile',currfile
            flist.append(currfile)


        #flist = SU.ffind(mydirectory, shellglobs=(myfilebaseglob,))
        #SU.printr(flist)
        tth,T,counts,counts_err,mon0=readfiles(flist)
        #wl=2.35916
        #c=2*wl/N.sin(N.deg2rad(N.array(tth))/2)

        #p,perror,pcerror,chisq=fitpeak(tth[0],counts[0],counts_err[0])
        #print 'p',p,perror,pcerror, chisq
        #sys.exit()
        new_tth,new_T,new_counts=regrid2(tth,T,counts)
        #new_tth,new_T,new_counts=prep_data3(tth,T,counts)
        #x,y,z=grid(new_tth,new_T,new_counts)
        x=N.array(new_tth)
        y=N.array(new_T)
        z=ma.array(new_counts)

        #QX,QZ=N.meshgrid(qx,qz)
        cmap=pylab.cm.jet
        #import matplotlib.ticker as ticker
        zmin, zmax = z.min(), z.max()
        locator = ticker.MaxNLocator(10) # if you want no more than 10 contours
        locator.create_dummy_axis()
        locator.set_bounds(zmin, zmax)
        levs = locator()
        levs=N.linspace(zmin,zmax,10)
        #levs=N.concatenate((levs,[3000]))
        ax=pylab.subplot(1,1,1)
        #mycontour=pylab.pcolor(N.array(tth).flatten(),N.array(T).flatten(),N.array(counts).flatten())
        #mycontour=pylab.contourf(x,y,z,levs)#,
        mycontour=pylab.pcolormesh(x,y,z)
        #cmap = pylab.cm.RdBu_r
        cmap=pylab.cm.binary
        #cmap = pylab.cm.PiYG
        mycontour.set_cmap(cmap)
        pylab.xlabel(r'$2\theta$',fontsize=18)
        pylab.ylabel('T (K) ', fontsize=18)
        pylab.axhline(y=220,color='black',linewidth=3.2)

        fontsize=16
        ax = pylab.gca()
        for tick in ax.xaxis.get_major_ticks():
            tick.label1.set_fontsize(fontsize)
        for tick in ax.yaxis.get_major_ticks():
            tick.label1.set_fontsize(fontsize)
        mycbar=pylab.colorbar()
        #levs.set_bounds(zmin, zmax)
        #mycontour=pylab.contourf(x,y,z,35,extent=(17,19.6,y.min(),y.max()))#,cmap=pylab.cm.jet)
        #pylab.axis('equal')

        #pylab.pcolor(qx,qz,counts)
        #mycontour.set_clim(vmin=160, vmax=500)
        #mycbar=pylab.colorbar()

        #mycbar.set_clim(vmin=160, vmax=500)
        #pylab.text(.1,.8,'(a)',fontsize=20,transform=ax.transAxes)
        pylab.xlim((43.55,46.5))
        pylab.ylim((195,250))
        #pylab.show()
        #sys.exit()

    if 1:
        #ax2=pylab.subplot(2,1,2)
        ax2 = inset_axes(ax,
                        width="30%", # width = 30% of parent_bbox
                        height="30%", # height : 1 inch
                        loc=1)
        if 1:
            res=N.loadtxt(r'c:\srfeas\caxis.txt')
            T=res[:,0]
            th=res[:,1]
            th_err=res[:,2]
            wavelength=2.35916
            dspacing=4
            c=dspacing*wavelength/N.sin(N.radians(th/2))/2
            cerr=((dspacing*wavelength/2)*th_err/2)*N.abs(1./N.sin(N.radians(th/2))*1./N.tan(N.radians(th/2)))
            if 0:
                ax2.errorbar(T,c,yerr=cerr,fmt='s',color='black')
            if 1:
                ax2.errorbar(T,th,yerr=th_err,fmt='s',color='black')
            ax2.xaxis.set_major_locator(MaxNLocator(5))
            #ax2.yaxis.set_major_locator(MaxNLocator(4))
            pylab.xlabel(r'T (K)',fontsize=10)
            if 0:
                pylab.ylabel(r'c $(\AA)$', fontsize=10)
            if 1:
                pylab.ylabel(r'$2\theta$',fontsize=10)

            pylab.xlim((193,251))
            if 0:
                pylab.ylim((12.2,12.40))

        if 0:
            ax2.errorbar(tth[0],counts[0],yerr=counts_err[0],fmt='s',color='black',label='250 K')
            ax2.xaxis.set_major_locator(MaxNLocator(4))
            #ax2.plot(tth[-1],counts[-1],'o',color='blue')
            #pylab.text(.6,.7,'T=250 K',fontsize=10,transform=ax2.transAxes)
            pylab.xlabel(r'$2\theta$',fontsize=10)
            ax2.errorbar(tth[34],counts[34],yerr=counts_err[34],fmt='o',color='red',label='200 K')
            pylab.ylabel('Intensity (arb. units)', fontsize=10)
            #ax2.legend(numpoints=1)


            pylab.xlim((43.55,46.5))
    if 0:
        ax2 = inset_axes(ax,
                        width="30%", # width = 30% of parent_bbox
                        height="30%", # height : 1 inch
                        loc=4)
        ax2.errorbar(tth[34],counts[34],yerr=counts_err[34],fmt='s',color='red')
        ax2.xaxis.set_major_locator(MaxNLocator(4))
        #ax2.plot(tth[-1],counts[-1],'o',color='blue')
        pylab.text(.6,.7,'T=200 K',fontsize=10,transform=ax2.transAxes)
        pylab.xlabel(r'$2\theta$',fontsize=10)
        pylab.ylabel('Intensity (arb. units)', fontsize=10)


        pylab.xlim((43.55,46.5))

    if 1:
        #print 'T',T[0],T[-1]
        pylab.savefig(r'c:\srfeas\formfactor_paper\srfe2_fig3t.eps')
        pylab.show()
        #pylab.savefig(r'c:\srfeas\formfactor_paper\srfe2_fig3.png')



    if 0:
        mydirectory=r'C:\srfeas\Feb27_2009'
        myfilebase='split0'
        myend='bt9'
        myfilebaseglob=myfilebase+'*.'+myend
        filerange1=range(1,5)
        filerange1.append(7)
        filerange1.append(8)
        filerange1.append(9)
        filerange2=range(45,52)
        #mydirectory=r'C:\srfeas\SrFeAsNi\Ni0p08\2009-04-diffraction'
        #file_range=(35,51)
        #myfilebase='SrFeA0'
        flist=[]

        #for i in filerange1:
        #    currfile=os.path.join(mydirectory,myfilebase+str(0)+str(i)+r"."+myend)
        #    print 'currfile',currfile
        #    flist.append(currfile)
        for i in filerange2:
            currfile=os.path.join(mydirectory,myfilebase+str(i)+r"."+myend)
            print 'currfile',currfile
            flist.append(currfile)


        #flist = SU.ffind(mydirectory, shellglobs=(myfilebaseglob,))
        #SU.printr(flist)
        tth,T,counts,counts_err,mon0=readfiles(flist,mon0=mon0)
        new_tth,new_T,new_counts=regrid2(tth,T,counts)
        #x,y,z=grid(new_tth,new_T,new_counts)
        x=N.array(new_tth)
        y=N.array(new_T)
        z=ma.array(new_counts)

        #QX,QZ=N.meshgrid(qx,qz)
        cmap=pylab.cm.jet
        #import matplotlib.ticker as ticker
        if 0:
            zmin, zmax = 160, 500
            locator = ticker.MaxNLocator(10) # if you want no more than 10 contours
            locator.create_dummy_axis()
            locator.set_bounds(zmin, zmax)
            levs = locator()
        #levs=10
        #levs=N.linspace(zmin,zmax,10)
        #levs=N.concatenate((levs,[3000]))
        ax2=pylab.subplot(1,2,2)
        #print 'hi'
        #mycontour=pylab.contourf(x,y,z,levs)#,
        mycontour=ax2.pcolormesh(x,y,z)
        cmap = pylab.cm.RdBu_r
        #cmap = pylab.cm.PiYG
        mycontour.set_cmap(cmap)
        pylab.axhline(y=220,color='white',linewidth=3.2)
        pylab.xlabel(r'$2\theta$',fontsize=14)
        #pylab.ylabel('T (K) ')
        #levs.set_bounds(zmin, zmax)
        #mycontour=pylab.contourf(x,y,z,35,extent=(17,19.6,y.min(),y.max()))#,cmap=pylab.cm.jet)
        #pylab.axis('equal')

        #pylab.pcolor(qx,qz,counts)
        #mycontour.set_clim(vmin=160, vmax=500)
        mycbar=pylab.colorbar()

        #mycbar.set_clim(vmin=160, vmax=500)
        ax2.text(.1,.9,'(b)',fontsize=20,transform=ax2.transAxes)
        pylab.xlim((43.5,46.5))
        pylab.ylim((195,250))
        ax2.yaxis.set_major_formatter(pylab.NullFormatter())
        ax2.yaxis.set_major_locator(pylab.NullLocator())
        pylab.show()
