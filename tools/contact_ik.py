"""Small analytic contact solver; preserves sourced limb lengths and bend plane."""
import math
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,s):return tuple(x*s for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def length(a):return math.sqrt(dot(a,a))
def unit(a):
    n=length(a)
    if n<1e-9:raise ValueError('Degenerate contact direction')
    return mul(a,1/n)
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def solve(root,joint,end,target):
    upper=length(sub(joint,root));lower=length(sub(end,joint))
    if min(upper,lower)<1e-6:raise ValueError('Degenerate limb')
    direction=unit(sub(target,root));distance=max(abs(upper-lower)+1e-5,min(length(sub(target,root)),upper+lower-1e-5))
    axis=sub(joint,root);bend=sub(axis,mul(direction,dot(axis,direction)))
    if length(bend)<1e-6:bend=cross(direction,(0,0,1) if abs(direction[2])<.9 else (1,0,0))
    bend=unit(bend);along=(upper*upper-lower*lower+distance*distance)/(2*distance);height=math.sqrt(max(0,upper*upper-along*along))
    return add(root,add(mul(direction,along),mul(bend,height))),add(root,mul(direction,distance))
def qmul(a,b):
    x,y,z,w=a;X,Y,Z,W=b
    return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
def between(a,b):
    a=unit(a);b=unit(b);d=dot(a,b)
    if d<-.999999:
        axis=unit(cross(a,(1,0,0) if abs(a[0])<.9 else (0,1,0)));return (*axis,0.)
    c=cross(a,b);return unit((*c,1+d))
def rotate(q,v):return qmul(qmul(q,(*v,0)),(-q[0],-q[1],-q[2],q[3]))[:3]
def slerp(a,b,t):
    d=dot(a,b)
    if d<0:b=mul(b,-1);d=-d
    if d>.9995:return unit(add(mul(a,1-t),mul(b,t)))
    angle=math.acos(max(-1,min(1,d)));s=math.sin(angle)
    return add(mul(a,math.sin((1-t)*angle)/s),mul(b,math.sin(t*angle)/s))
