'''
@author: Peng
'''

from numpy import dot
from numpy import array

def gauss(a,b):
    n=len(b)
    # Elimination phase
    for k in range(0, n-1):
        for i in range(k+1,n):
            if a[i,k]!=0.0:
                lam=a[i,k] /a[k,k]
                a[i,k+1:n]=a[i,k+1:n]-lam*a[k,k+1:n]
                b[i]=b[i]-lam*b[k]
    #Back substitution
    for k in range(n-1,-1,-1):
        b[k]=(b[k]-dot(a[k,k+1:n],b[k+1:n]))/a[k,k]
    return b

##x=array([[4,-2,1],[-2,4,-2],[1,-2,4]],float)
##y=array([11,-16,17],float)
##
x=array([[-83.900289,42.508828, 1], [-83.858695, 42.506322, 1], [-83.880742, 42.511788, 1]],float)
y=array([228,507,171],float)

##print(x)
##print("Solution is")
##print(gauss(x,y))

