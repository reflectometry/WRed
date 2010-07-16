'''
Alex Yee

Edit History
7/8/2010: Stared work on code. Added the star method, compliments of Dr. Ratcliff II, and completed the calcB method.
7/9/2010: Wrote the calcUB and UBtestrun methods. Used previous experiment data to confirm the results of the calcUB method
           Also wrote the calcIdealAngles method to calculate chi and phi for the special case when omega = 0.
7/13/2010: Created and tested the calcIdealAngles2, which employs scipy's fsolve to solve 6 equations for phi, chi, omega1, omega2, theta1 and theta2
'''

import numpy as N 
import scipy
import scipy.optimize
from openopt import NLSP

def star(a,b,c,alpha,beta,gamma):
   "Calculate unit cell volume, reciprocal cell volume, reciprocal lattice parameters"
   alpha=N.radians(alpha)
   beta=N.radians(beta)
   gamma=N.radians(gamma)
   V=2*a*b*c*\
   N.sqrt(N.sin((alpha+beta+gamma)/2)*\
           N.sin((-alpha+beta+gamma)/2)*\
           N.sin((alpha-beta+gamma)/2)*\
           N.sin((alpha+beta-gamma)/2))
   Vstar=(2*N.pi)**3/V;
   astar=2*N.pi*b*c*N.sin(alpha)/V
   bstar=2*N.pi*a*c*N.sin(beta)/V
   cstar=2*N.pi*b*a*N.sin(gamma)/V
   alphastar=N.arccos((N.cos(beta)*N.cos(gamma)-\
                            N.cos(alpha))/ \
                           (N.sin(beta)*N.sin(gamma)))
   betastar= N.arccos((N.cos(alpha)*N.cos(gamma)-\
                            N.cos(beta))/ \
                           (N.sin(alpha)*N.sin(gamma)))
   gammastar=N.arccos((N.cos(alpha)*N.cos(beta)-\
                            N.cos(gamma))/ \
                           (N.sin(alpha)*N.sin(beta)))
   V=V
   alphastar=N.degrees(alphastar)
   betastar=N.degrees(betastar)
   gammastar=N.degrees(gammastar)
   return astar,bstar,cstar,alphastar,betastar,gammastar

def calcB(astar,bstar,cstar,alphastar,betastar,gammastar,c, alpha):
   "Calculates the B matrix using the crystal dimensions calculated in the 'star' method"
   alphastar = N.radians(alphastar)
   betastar = N.radians(betastar)
   gammastar = N.radians(gammastar)
   alpha = N.radians(alpha)
   
   Bmatrix=N.array([[astar, bstar*N.cos(gammastar), cstar*N.cos(betastar)],
                    [0, bstar*N.sin(gammastar), -cstar*N.sin(betastar)*N.cos(alpha)],
                    [0, 0, cstar]],'Float64') #check the third element
   #print(Bmatrix)
   return Bmatrix

def calcUB(h1, k1, l1, h2, k2, l2, omega1, chi1, phi1, omega2, chi2, phi2, Bmatrix):
   "Calculates the UB matrix using 2 sets of observations (h#, k#, l#) and their respective angle measurements in degrees (omega#, chi#, phi#)"
   #Convertiung angles given in degrees to radians
   omega1 = N.radians(omega1)
   chi1 = N.radians(chi1)
   phi1 = N.radians(phi1)
   omega2 = N.radians(omega2)
   chi2 = N.radians(chi2)
   phi2 = N.radians(phi2)
   
   hmatrix1 = N.array([h1, k1, l1])
   hmatrix2 = N.array([h2, k2, l2])
   h1c = N.dot(Bmatrix, hmatrix1) 
   h2c = N.dot(Bmatrix, hmatrix2)
   h3c = N.cross(h1c, h2c)
   
   ''' Making the orthogonal unit-vectors t#c:
   t1c is parallel to h1c
   t3c is orthogonal to both t1c and t2c, and thus is parallel to h3c
   t2c must be orthogonal to both t1c and t2c
   '''
   t1c = h1c / N.sqrt(N.power(h1c[0], 2) + N.power(h1c[1], 2) + N.power(h1c[2], 2))
   t3c = h3c / N.sqrt(N.power(h3c[0], 2) + N.power(h3c[1], 2) + N.power(h3c[2], 2))
   t2c = N.cross(t3c, t1c)
   Tc = N.array([t1c, t2c, t3c]).T
   realU=N.array([[ -5.28548868e-01,   8.65056241e-17,  -6.63562568e-16],
                  [ -0.00000000e+00,   4.86909792e-01,   2.90030482e-16],
                  [  0.00000000e+00,   0.00000000e+00,  -1.26048191e-01]])
   
   #calculating u_phi 
   u1p = N.array([N.cos(omega1)*N.cos(chi1)*N.cos(phi1) - N.sin(omega1)*N.sin(phi1),
                N.cos(omega1)*N.cos(chi1)*N.sin(phi1) + N.sin(omega1)*N.cos(phi1),
                N.cos(omega1)*N.sin(chi1)],'Float64')
   u2p = N.array([N.cos(omega2)*N.cos(chi2)*N.cos(phi2) - N.sin(omega2)*N.sin(phi2),
                N.cos(omega2)*N.cos(chi2)*N.sin(phi2) + N.sin(omega2)*N.cos(phi2),
                N.cos(omega2)*N.sin(chi2)],'Float64')
   u3p = N.cross(u1p, u2p)
   
   ''' Making orthogonal unit-vectors t#p
   Tp should be exactaly superimposed on Tc
   t#p is created the same way t#c was, except using u#p instead of h#c
   '''
   t1p = u1p / N.sqrt(u1p[0]**2 + u1p[1]**2 + u1p[2]**2)
   t3p = u3p / N.sqrt(u3p[0]**2 + u3p[1]**2 + u3p[2]**2)
   t2p = N.cross(t3p, t1p)
   Tp = N.array([t1p, t2p, t3p],'Float64').T
   
   #calculating the UB matrix
   Umatrix = N.dot(Tp, Tc.T) 
   UBmatrix = N.dot(Umatrix, Bmatrix)
   return UBmatrix
   


def calcIdealAngles(h, UBmatrix, Bmatrix, wavelength, stars):
   "Calculates the remaining angles with omega given as 0"
   "Returns (twotheta, theta, omega, chi, phi)"
   '''myUBmatrix=N.array([[ -0.8495486120866541,0.8646150711829229,-1.055554030805845],
                     [-0.7090402876860106,0.7826211792587279,1.211714627203656],
                     [1.165768160358335,1.106088263216144,-0.03224481098900243]],'Float64')
   '''
   hp = N.dot(UBmatrix, h)
   phi = N.degrees(N.arctan2(hp[1], hp[0]))
   chi = N.degrees(N.arctan2(hp[2], N.sqrt(hp[0]**2 + hp[1]**2)))
      
   q = calcq (h[0], h[1], h[2], stars)
   twotheta = N.degrees(2 * N.arcsin(wavelength * q / 4 / N.pi))
   theta = twotheta / 2
   omega = 0
      
   #print 'chi',chi, 180-chi
   #print 'phi',phi,180+phi
   return twotheta, theta, omega, chi, phi
      


def calcScatteringPlane (h1, h2, UBmatrix, wavelength):
   "Calculates the chi and phi for the scattering plane defined by h1 and h2. Used with calcIdealAngles2."
   #Accepts two scattering plane vectors, h1 and h2, and the UB matrix
   h1p = N.dot(UBmatrix, h1)
   h2p = N.dot(UBmatrix, h2)
   
   x0 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
   p0 = NLSP(equations, x0, args=(h1p, h2p, wavelength))
   r0 = p0.solve('nlp:ralg')
   chi = N.degrees(r0.xf[0]) #xf is the final array, xf[0] = chi
   phi = N.degrees(r0.xf[1]) #                       xf[1] = phi
   
   return chi, phi
   
def calcIdealAngles2 (desiredh, chi, phi, UBmatrix, wavelength, stars):
   "Calculates the twotheta, theta, and omega values for a desired h vector. Uses chi and phi from calcScatteringPlane."
   #Accepts the desired h vector, chi, phi, the UB matrix, the wavelength, and the stars dictionary
   
   desiredhp = N.dot(UBmatrix, desiredh)
   
   #Old code (scipy.optimize.fsolve) produced inaccurate results with far-off estimates
   #solutions = scipy.optimize.fsolve(equations, x0, args=(h1p, h2p, wavelength)) 

   q = calcq (desiredh[0], desiredh[1], desiredh[2], stars)
   #print 'calculation WR'
   #print 'wl',wavelength
   #print 'q', q
   twotheta = 2.0 * N.arcsin(wavelength * q / 4.0 / N.pi)
    
   x0 = [0.0, 0.0]
   p = NLSP(secondequations, x0, args=(desiredhp, chi, phi, wavelength, twotheta))
   r = p.solve('nlp:ralg')
   omega = r.xf[0]
   theta = twotheta/2.0 - omega   # ------ ALTERNATE SOLUTION FOR THETA ------
   
   
   #theta = r.xf[1]  # ------ SOLVER POTENTIALLY INACCURATE FOR THETA ------
    
    
   solutions = [twotheta, theta, omega]
   return N.degrees(solutions) #% 360
   #returns an array of 3 angles [twotheta, theta, omega]
    
    
def equations(x, h1p, h2p, wavelength):
   #x vector are the intial estimates
   chi = x[0]
   phi = x[1]
   theta1 = x[2]
   omega1 = x[3]
   theta2 = x[4]
   omega2 = x[5]
   outvec=[h1p[0] - 2.0/wavelength * N.sin(theta1) * (N.cos(omega1)*N.cos(chi)*N.cos(phi) - N.sin(omega1)*N.sin(phi)),
           h1p[1] - 2.0/wavelength * N.sin(theta1) * (N.cos(omega1)*N.cos(chi)*N.sin(phi) + N.sin(omega1)*N.cos(phi)),
           h1p[2] - 2.0/wavelength * N.sin(theta1) * N.cos(omega1)*N.sin(chi),
           h2p[0] - 2.0/wavelength * N.sin(theta2) * (N.cos(omega2)*N.cos(chi)*N.cos(phi) - N.sin(omega2)*N.sin(phi)),
           h2p[1] - 2.0/wavelength * N.sin(theta2) * (N.cos(omega2)*N.cos(chi)*N.sin(phi) + N.sin(omega2)*N.cos(phi)),
           h2p[2] - 2.0/wavelength * N.sin(theta2) * N.cos(omega2)*N.sin(chi)]  
   return outvec
   
def secondequations(x, hp, chi, phi, wavelength,tth):
   #theta = x[0]
   #omega = x[1]
   omega=x[0]
   theta=tth/2
   outvec=[hp[0] - 2.0/wavelength * N.sin(theta) * (N.cos(omega)*N.cos(chi)*N.cos(phi) - N.sin(omega)*N.sin(phi)),
           hp[1] - 2.0/wavelength * N.sin(theta) * (N.cos(omega)*N.cos(chi)*N.sin(phi) + N.sin(omega)*N.cos(phi)),
           hp[2] - 2.0/wavelength * N.sin(theta) * N.cos(omega)*N.sin(chi)]
   return outvec
    
    
# ******************************* START - METHODS FOR CALCULATING Q ******************************* 
def scalar(x1, y1, z1, x2, y2, z2, stars):
   "calculates scalar product of two vectors"
   a = stars['astar']
   b = stars['bstar']
   c = stars['cstar']
   alpha = N.radians(stars['alphastar'])
   beta = N.radians(stars['betastar'])
   gamma = N.radians(stars['gammastar'])

   s=x1*x2*a**2+y1*y2*b**2+z1*z2*c**2+(x1*y2+x2*y1)*a*b*N.cos(gamma)+(x1*z2+x2*z1)*a*c*N.cos(beta)+(z1*y2+z2*y1)*c*b*N.cos(alpha)
   return s


def modvec(x, y, z, stars):
   "Calculates modulus of a vector defined by its fraction cell coordinates"
   "or Miller indexes"
   m=N.sqrt(scalar(x, y, z, x, y, z, stars))
   return m



def calcq(H, K, L, stars):
   "Given reciprocal-space coordinates of a vector, calculate its coordinates in the Cartesian space."
   q = modvec(H, K, L, stars);
   return q
          
# ******************************* END - METHODS FOR CALCULATING Q ******************************* 
          
# **************************************** UB MATRIX TESTING CODE ****************************************
  
def UBtestrun():
   "Test method to calculate UB matrix given input"
   #a, b, c, alpha, beta, gamma, h1, k1, l1, omega1, chi1, phi1, h2, k2, l2, omega2, chi2, phi2 = input('enter data: ')
   #Test data:
   #3.9091,3.9091,3.9091,90,90,90,1,1,0,0,89.62,.001,0,0,1,0,-1.286,131.063
   #maybe: 3.9091,3.9091,3.9091,90,90,90,1,1,0,-1.855,89.62,.001,0,0,1,-.0005,-1.286,131.063
   #Should yield:
   a, b, c, alpha, beta, gamma, h1, k1, l1, omega1, chi1, phi1, h2, k2, l2, omega2, chi2, phi2=3.9091,3.9091,3.9091,90,90,90,1,1,0,0,89.62,.001,0,0,1,0,-1.286,131.063
   #a, b, c, alpha, beta, gamma, h1, k1, l1, omega1, chi1, phi1, h2, k2, l2, omega2, chi2, phi2=3.9091,3.9091,3.9091,90,90,90,1,1,0,0,0,0,\
   # 1,-1,0,0,0,90
   '''
   UB["0"] = -0.8495486120866541
   UB["1"] = 0.8646150711829229
   UB["2"] = -1.055554030805845
   UB["3"] = -0.7090402876860106
   UB["4"] = 0.7826211792587279
   UB["5"] = 1.211714627203656
   UB["6"] = 1.165768160358335
   UB["7"] = 1.106088263216144
   UB["8"] = -0.03224481098900243
   '''
   
   astar,bstar,cstar,alphastar,betastar,gammastar = star(a, b, c, alpha, beta, gamma)
   Bmatrix = calcB(astar, bstar, cstar, alphastar, betastar, gammastar, c, alpha)
   UB=calcUB(h1, k1, l1, h2, k2, l2, omega1, chi1, phi1, omega2, chi2, phi2, Bmatrix)
   #calcIdealAngles(N.array([1,1,1],'Float64'),UB,0,Bmatrix)
   hv1=[1,0,0]
   hv2=[0,1,0]
   result = calcIdealAngles2(hv1, hv2, UB, 2.35916)
   print UB
   print result
   print 'chi',(180-result[0])%360
   print 'phi',(result[1]+180)%360
# **************************************** END OF UB MATRIX TESTING CODE ****************************************  


if __name__=="__main__":
   pi=N.pi
   a=2*pi; b=2*pi; c=2*pi
   alpha=90; beta=90; gamma=90
   recip=star(a,b,c,alpha,beta,gamma)
   print recip
   UBtestrun()
   print('done!')