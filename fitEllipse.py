# -*- coding: utf-8 -*-
"""
Created on Mon May 07 21:35:07 2018

@author: Edward
"""

import numpy
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

"""Demonstration of least-squares fitting of ellipses
    __author__ = "Ben Hammel, Nick Sullivan-Molina"
    __credits__ = ["Ben Hammel", "Nick Sullivan-Molina"]
    __maintainer__ = "Ben Hammel"
    __email__ = "bdhammel@gmail.com"
    __status__ = "Development"
    Requirements 
    ------------
    Python 2.X or 3.X
    numpy
    matplotlib
    References
    ----------
    (*) Halir, R., Flusser, J.: 'Numerically Stable Direct Least Squares 
        Fitting of Ellipses'
    (**) http://mathworld.wolfram.com/Ellipse.html
    (***) White, A. McHale, B. 'Faraday rotation data analysis with least-squares 
        elliptical fitting'
"""

class LSqEllipse:

    def fit(self, data):
        """Lest Squares fitting algorithm 
        Theory taken from (*)
        Solving equation Sa=lCa. with a = |a b c d f g> and a1 = |a b c> 
            a2 = |d f g>
        Args
        ----
        data (list:list:float): list of two lists containing the x and y data of the
            ellipse. of the form [[x1, x2, ..., xi],[y1, y2, ..., yi]]
        Returns
        ------
        coef (list): list of the coefficients describing an ellipse
           [a,b,c,d,f,g] corresponding to ax**2+2bxy+cy**2+2dx+2fy+g
        """
        x, y = numpy.asarray(data, dtype=float)

        #Quadratic part of design matrix [eqn. 15] from (*)
        D1 = numpy.mat(numpy.vstack([x**2, x*y, y**2])).T
        #Linear part of design matrix [eqn. 16] from (*)
        D2 = numpy.mat(numpy.vstack([x, y, numpy.ones(len(x))])).T
        
        #forming scatter matrix [eqn. 17] from (*)
        S1 = D1.T*D1
        S2 = D1.T*D2
        S3 = D2.T*D2  
        
        #Constraint matrix [eqn. 18]
        C1 = numpy.mat('0. 0. 2.; 0. -1. 0.; 2. 0. 0.')

        #Reduced scatter matrix [eqn. 29]
        M=C1.I*(S1-S2*S3.I*S2.T)

        #M*|a b c >=l|a b c >. Find eigenvalues and eigenvectors from this equation [eqn. 28]
        eval, evec = numpy.linalg.eig(M) 

        # eigenvector must meet constraint 4ac - b^2 to be valid.
        cond = 4*numpy.multiply(evec[0, :], evec[2, :]) - numpy.power(evec[1, :], 2)
        a1 = evec[:, numpy.nonzero(cond.A > 0)[1]]
        
        #|d f g> = -S3^(-1)*S2^(T)*|a b c> [eqn. 24]
        a2 = -S3.I*S2.T*a1
        
        # eigenvectors |a b c d f g> 
        self.coef = numpy.vstack([a1, a2])
        self._save_parameters()
            
    def _save_parameters(self):
        """finds the important parameters of the fitted ellipse
        
        Theory taken form http://mathworld.wolfram
        Args
        -----
        coef (list): list of the coefficients describing an ellipse
           [a,b,c,d,f,g] corresponding to ax**2+2bxy+cy**2+2dx+2fy+g
        Returns
        _______
        center (List): of the form [x0, y0]
        width (float): major axis 
        height (float): minor axis
        phi (float): rotation of major axis form the x-axis in radians 
        """

        #eigenvectors are the coefficients of an ellipse in general form
        #a*x^2 + 2*b*x*y + c*y^2 + 2*d*x + 2*f*y + g = 0 [eqn. 15) from (**) or (***)
        a = self.coef[0,0]
        b = self.coef[1,0]/2.
        c = self.coef[2,0]
        d = self.coef[3,0]/2.
        f = self.coef[4,0]/2.
        g = self.coef[5,0]
        
        #finding center of ellipse [eqn.19 and 20] from (**)
        x0 = (c*d-b*f)/(b**2.-a*c)
        y0 = (a*f-b*d)/(b**2.-a*c)
        
        #Find the semi-axes lengths [eqn. 21 and 22] from (**)
        numerator = 2*(a*f*f+c*d*d+g*b*b-2*b*d*f-a*c*g)
        denominator1 = (b*b-a*c)*( (c-a)*numpy.sqrt(1+4*b*b/((a-c)*(a-c)))-(c+a))
        denominator2 = (b*b-a*c)*( (a-c)*numpy.sqrt(1+4*b*b/((a-c)*(a-c)))-(c+a))
        width = numpy.sqrt(numerator/denominator1)
        height = numpy.sqrt(numerator/denominator2)

        # angle of counterclockwise rotation of major-axis of ellipse to x-axis [eqn. 23] from (**)
        # or [eqn. 26] from (***).
        phi = .5*numpy.arctan((2.*b)/(a-c))

        self._center = [x0, y0]
        self._width = width
        self._height = height
        self._phi = phi

    @property
    def center(self):
        return self._center

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def phi(self):
        """angle of counterclockwise rotation of major-axis of ellipse to x-axis 
        [eqn. 23] from (**)
        """
        return self._phi

    def parameters(self):
        return self.center, self.width, self.height, self.phi

def make_test_ellipse(center=[1,1], width=1, height=.6, phi=3.14/5):
    """Generate Elliptical data with noise
    
    Args
    ----
    center (list:float): (<x_location>, <y_location>)
    width (float): semimajor axis. Horizontal dimension of the ellipse (**)
    height (float): semiminor axis. Vertical dimension of the ellipse (**)
    phi (float:radians): tilt of the ellipse, the angle the semimajor axis
        makes with the x-axis 
    Returns
    -------
    data (list:list:float): list of two lists containing the x and y data of the
        ellipse. of the form [[x1, x2, ..., xi],[y1, y2, ..., yi]]
    """
    t = numpy.linspace(0, 2*numpy.pi, 1000)
    x_noise, y_noise = numpy.random.rand(2, len(t))
    
    ellipse_x = center[0] + width*numpy.cos(t)*numpy.cos(phi)-height*numpy.sin(t)*numpy.sin(phi) + x_noise/2.
    ellipse_y = center[1] + width*numpy.cos(t)*numpy.sin(phi)+height*numpy.sin(t)*numpy.cos(phi) + y_noise/2.

    return [ellipse_x, ellipse_y]

from math import *
from numpy import *

def ascol( arr ):
    '''
    If the dimensionality of 'arr' is 1, reshapes it to be a column matrix (N,1).
    '''
    if len( arr.shape ) == 1: arr = arr.reshape( ( arr.shape[0], 1 ) )
    return arr
def asrow( arr ):
    '''
    If the dimensionality of 'arr' is 1, reshapes it to be a row matrix (1,N).
    '''
    if len( arr.shape ) == 1: arr = arr.reshape( ( 1, arr.shape[0] ) )
    return arr

def fitellipse( x, opt = 'nonlinear', **kwargs ):
    '''
    function [z, a, b, alpha] = fitellipse(x, varargin)
    %FITELLIPSE   least squares fit of ellipse to 2D data
    %
    %   [Z, A, B, ALPHA] = FITELLIPSE(X)
    %       Fit an ellipse to the 2D points in the 2xN array X. The ellipse is
    %       returned in parametric form such that the equation of the ellipse
    %       parameterised by 0 <= theta < 2*pi is:
    %           X = Z + Q(ALPHA) * [A * cos(theta); B * sin(theta)]
    %       where Q(ALPHA) is the rotation matrix
    %           Q(ALPHA) = [cos(ALPHA), -sin(ALPHA); 
    %                       sin(ALPHA), cos(ALPHA)]
    %
    %       Fitting is performed by nonlinear least squares, optimising the
    %       squared sum of orthogonal distances from the points to the fitted
    %       ellipse. The initial guess is calculated by a linear least squares
    %       routine, by default using the Bookstein constraint (see below)
    %
    %   [...]            = FITELLIPSE(X, 'linear')
    %       Fit an ellipse using linear least squares. The conic to be fitted
    %       is of the form
    %           x'Ax + b'x + c = 0
    %       and the algebraic error is minimised by least squares with the
    %       Bookstein constraint (lambda_1^2 + lambda_2^2 = 1, where 
    %       lambda_i are the eigenvalues of A)
    %
    %   [...]            = FITELLIPSE(..., 'Property', 'value', ...)
    %       Specify property/value pairs to change problem parameters
    %          Property                  Values
    %          =================================
    %          'constraint'              {|'bookstein'|, 'trace'}
    %                                    For the linear fit, the following
    %                                    quadratic form is considered
    %                                    x'Ax + b'x + c = 0. Different
    %                                    constraints on the parameters yield
    %                                    different fits. Both 'bookstein' and
    %                                    'trace' are Euclidean-invariant
    %                                    constraints on the eigenvalues of A,
    %                                    meaning the fit will be invariant
    %                                    under Euclidean transformations
    %                                    'bookstein': lambda1^2 + lambda2^2 = 1
    %                                    'trace'    : lambda1 + lambda2     = 1
    %
    %           Nonlinear Fit Property   Values
    %           ===============================
    %           'maxits'                 positive integer, default 200
    %                                    Maximum number of iterations for the
    %                                    Gauss Newton step
    %
    %           'tol'                    positive real, default 1e-5
    %                                    Relative step size tolerance
    %   Example:
    %       % A set of points
    %       x = [1 2 5 7 9 6 3 8; 
    %            7 6 8 7 5 7 2 4];
    % 
    %       % Fit an ellipse using the Bookstein constraint
    %       [zb, ab, bb, alphab] = fitellipse(x, 'linear');
    %
    %       % Find the least squares geometric estimate       
    %       [zg, ag, bg, alphag] = fitellipse(x);
    %       
    %       % Plot the results
    %       plot(x(1,:), x(2,:), 'ro')
    %       hold on
    %       % plotellipse(zb, ab, bb, alphab, 'b--')
    %       % plotellipse(zg, ag, bg, alphag, 'k')
    % 
    %   See also PLOTELLIPSE
    
    % Copyright Richard Brown, this code can be freely used and modified so
    % long as this line is retained
    '''
    #error(nargchk(1, 5, nargin, 'struct'))
    
    x = asarray( x )
    
    ## Parse inputs
    # ...
    ## Default parameters
    kwargs[ 'fNonlinear' ] = opt is not 'linear'
    kwargs.setdefault( 'constraint', 'bookstein' )
    kwargs.setdefault( 'maxits', 200 )
    kwargs.setdefault( 'tol', 1e-5 )
    if x.shape[1] == 2:
        x = x.T
    if x.shape[1] < 6:
        raise RuntimeError, 'fitellipse:InsufficientPoints At least 6 points required to compute fit'
    
    ## Constraints are Euclidean-invariant, so improve conditioning by removing
    ## centroid
    centroid = mean(x, 1)
    x        = x - centroid.reshape((2,1))
    
    ## Obtain a linear estimate
    if kwargs['constraint'] == 'bookstein':
        ## Bookstein constraint : lambda_1^2 + lambda_2^2 = 1
        z, a, b, alpha = fitbookstein(x)
    
    elif kwargs['constraint'] == 'trace':
        ## 'trace' constraint, lambda1 + lambda2 = trace(A) = 1
        z, a, b, alpha = fitggk(x)
    
    ## Minimise geometric error using nonlinear least squares if required
    if kwargs['fNonlinear']:
        ## Initial conditions
        z0     = z
        a0     = a
        b0     = b
        alpha0 = alpha
        
        ## Apply the fit
        z, a, b, alpha, fConverged = fitnonlinear(x, z0, a0, b0, alpha0, **kwargs)
        
        ## Return linear estimate if GN doesn't converge
        if not fConverged:
            print 'fitellipse:FailureToConverge', 'Gauss-Newton did not converge, returning linear estimate'
            z = z0
            a = a0
            b = b0
            alpha = alpha0
    
    ## Add the centroid back on
    z = z + centroid
    
    return z, a, b, alpha

def fitbookstein(x):
    '''
    function [z, a, b, alpha] = fitbookstein(x)
    %FITBOOKSTEIN   Linear ellipse fit using bookstein constraint
    %   lambda_1^2 + lambda_2^2 = 1, where lambda_i are the eigenvalues of A
    '''
    
    ## Convenience variables
    m  = x.shape[1]
    x1 = x[0, :].reshape((1,m)).T
    x2 = x[1, :].reshape((1,m)).T
    
    ## Define the coefficient matrix B, such that we solve the system
    ## B *[v; w] = 0, with the constraint norm(w) == 1
    B = hstack([ x1, x2, ones((m, 1)), power( x1, 2 ), multiply( sqrt(2) * x1, x2 ), power( x2, 2 ) ])
    
    ## To enforce the constraint, we need to take the QR decomposition
    Q, R = linalg.qr(B)
    
    ## Decompose R into blocks
    R11 = R[0:3, 0:3]
    R12 = R[0:3, 3:6]
    R22 = R[3:6, 3:6]
    
    ## Solve R22 * w = 0 subject to norm(w) == 1
    U, S, V = linalg.svd(R22)
    V = V.T
    w = V[:, 2]
    
    ## Solve for the remaining variables
    v = dot( linalg.solve( -R11, R12 ), w )
    
    ## Fill in the quadratic form
    A        = zeros((2,2))
    A.ravel()[0]     = w.ravel()[0]
    A.ravel()[1:3] = 1 / sqrt(2) * w.ravel()[1]
    A.ravel()[3]     = w.ravel()[2]
    bv       = v[0:2]
    c        = v[2]
    
    ## Find the parameters
    z, a, b, alpha = conic2parametric(A, bv, c)
    
    return z, a, b, alpha

def fitggk(x):
    '''
    function [z, a, b, alpha] = fitggk(x)
    % Linear least squares with the Euclidean-invariant constraint Trace(A) = 1
    '''
    
    ## Convenience variables
    m  = x.shape[1]
    x1 = x[0, :].reshape((1,m)).T
    x2 = x[1, :].reshape((1,m)).T
    
    ## Coefficient matrix
    B = hstack([ multiply( 2 * x1, x2 ), power( x2, 2 ) - power( x1, 2 ), x1, x2, ones((m, 1)) ])
    
    v = linalg.lstsq( B, -power( x1, 2 ) )[0].ravel()
    
    ## For clarity, fill in the quadratic form variables
    A        = zeros((2,2))
    A[0,0]   = 1 - v[1]
    A.ravel()[1:3] = v[0]
    A[1,1]   = v[1]
    bv       = v[2:4]
    c        = v[4]
    
    ## find parameters
    z, a, b, alpha = conic2parametric(A, bv, c)
    
    return z, a, b, alpha


def fitnonlinear(x, z0, a0, b0, alpha0, **params):
    '''
    function [z, a, b, alpha, fConverged] = fitnonlinear(x, z0, a0, b0, alpha0, params)
    % Gauss-Newton least squares ellipse fit minimising geometric distance 
    '''
    
    ## Get initial rotation matrix
    Q0 = array( [[ cos(alpha0), -sin(alpha0) ], [ sin(alpha0), cos(alpha0) ]] )
    m = x.shape[1]
    
    ## Get initial phase estimates
    phi0 = angle( dot( dot( array([1, 1j]), Q0.T ), x - z0.reshape((2,1)) ) ).T
    u = hstack( [ phi0, alpha0, a0, b0, z0 ] ).T
    
    
    def sys(u):
        '''
        function [f, J] = sys(u)
        % SYS : Define the system of nonlinear equations and Jacobian. Nested
        % function accesses X (but changeth it not)
        % from the FITELLIPSE workspace
        '''
        
        ## Tolerance for whether it is a circle
        circTol = 1e-5
        
        ## Unpack parameters from u
        phi   = u[:-5]
        alpha = u[-5]
        a     = u[-4]
        b     = u[-3]
        z     = u[-2:]
        
        ## If it is a circle, the Jacobian will be singular, and the
        ## Gauss-Newton step won't work. 
        ##TODO: This can be fixed by switching to a Levenberg-Marquardt
        ##solver
        if abs(a - b) / (a + b) < circTol:
            print 'fitellipse:CircleFound', 'Ellipse is near-circular - nonlinear fit may not succeed'
        
        ## Convenience trig variables
        c = cos(phi)
        s = sin(phi)
        ca = cos(alpha)
        sa = sin(alpha)
        
        ## Rotation matrices
        Q    = array( [[ca, -sa],[sa, ca]] )
        Qdot = array( [[-sa, -ca],[ca, -sa]] )
        
        ## Preallocate function and Jacobian variables
        f = zeros(2 * m)
        J = zeros((2 * m, m + 5))
        for i in range( m ):
            rows = range( (2*i), (2*i)+2 )
            ## Equation system - vector difference between point on ellipse
            ## and data point
            f[ rows ] = x[:, i] - z - dot( Q, array([ a * cos(phi[i]), b * sin(phi[i]) ]) )
            
            ## Jacobian
            J[ rows, i ] = dot( -Q, array([ -a * s[i], b * c[i] ]) )
            J[ rows, -5: ] = \
                hstack([ ascol( dot( -Qdot, array([ a * c[i], b * s[i] ]) ) ), ascol( dot( -Q, array([ c[i], 0 ]) ) ), ascol( dot( -Q, array([ 0, s[i] ]) ) ), array([[-1, 0],[0, -1]]) ])
        
        return f,J
    
    
    ## Iterate using Gauss Newton
    fConverged = False
    for nIts in range( params['maxits'] ):
        ## Find the function and Jacobian
        f, J = sys(u)
        
        ## Solve for the step and update u
        #h = linalg.solve( -J, f )
        h = linalg.lstsq( -J, f )[0]
        u = u + h
        
        ## Check for convergence
        delta = linalg.norm(h, inf) / linalg.norm(u, inf)
        if delta < params['tol']:
            fConverged = True
            break
    
    alpha = u[-5]
    a     = u[-4]
    b     = u[-3]
    z     = u[-2:]
    
    return z, a, b, alpha, fConverged

def conic2parametric(A, bv, c):
    '''
    function [z, a, b, alpha] = conic2parametric(A, bv, c)
    '''
    ## Diagonalise A - find Q, D such at A = Q' * D * Q
    D, Q = linalg.eig(A)
    Q = Q.T
    
    ## If the determinant < 0, it's not an ellipse
    if prod(D) <= 0:
        raise RuntimeError, 'fitellipse:NotEllipse Linear fit did not produce an ellipse'
    
    ## We have b_h' = 2 * t' * A + b'
    t = -0.5 * linalg.solve(A, bv)
    
    c_h = dot( dot( t.T, A ), t ) + dot( bv.T, t ) + c
    
    z = t
    a = sqrt(-c_h / D[0])
    b = sqrt(-c_h / D[1])
    alpha = atan2(Q[0,1], Q[0,0])
    
    return z, a, b, alpha


'''
    function [x, params] = parseinputs(x, params, varargin)
    % PARSEINPUTS put x in the correct form, and parse user parameters
    
    % CHECK x
    % Make sure x is 2xN where N > 3
    if size(x, 2) == 2
        x = x'; 
    end
    if size(x, 1) ~= 2
        error('fitellipse:InvalidDimension', ...
            'Input matrix must be two dimensional')
    end
    if size(x, 2) < 6
        error('fitellipse:InsufficientPoints', ...
            'At least 6 points required to compute fit')
    end
    
    
    % Determine whether we are solving for geometric (nonlinear) or algebraic
    % (linear) distance
    if ~isempty(varargin) && strncmpi(varargin{1}, 'linear', length(varargin{1}))
        params.fNonlinear = false;
        varargin(1)       = [];
    else
        params.fNonlinear = true;
    end
    
    % Parse property/value pairs
    if rem(length(varargin), 2) ~= 0
        error('fitellipse:InvalidInputArguments', ...
            'Additional arguments must take the form of Property/Value pairs')
    end
    
    % Cell array of valid property names
    properties = {'constraint', 'maxits', 'tol'};
    
    while length(varargin) ~= 0
        % Pop pair off varargin
        property      = varargin{1};
        value         = varargin{2};
        varargin(1:2) = [];
        
        % If the property has been supplied in a shortened form, lengthen it
        iProperty = find(strncmpi(property, properties, length(property)));
        if isempty(iProperty)
            error('fitellipse:UnknownProperty', 'Unknown Property');
        elseif length(iProperty) > 1
            error('fitellipse:AmbiguousProperty', ...
                'Supplied shortened property name is ambiguous');
        end
        
        % Expand property to its full name
        property = properties{iProperty};
        
        % Check for irrelevant property
        if ~params.fNonlinear && ismember(property, {'maxits', 'tol'})
            warning('fitellipse:IrrelevantProperty', ...
                'Supplied property has no effect on linear estimate, ignoring');
            continue
        end
            
        % Check supplied property value
        switch property
            case 'maxits'
                if ~isnumeric(value) || value <= 0
                    error('fitcircle:InvalidMaxits', ...
                        'maxits must be an integer greater than 0')
                end
                params.maxits = value;
            case 'tol'
                if ~isnumeric(value) || value <= 0
                    error('fitcircle:InvalidTol', ...
                        'tol must be a positive real number')
                end
                params.tol = value;
            case 'constraint'
                switch lower(value)
                    case 'bookstein'
                        params.constraint = 'bookstein';
                    case 'trace'
                        params.constraint = 'trace';
                    otherwise
                        error('fitellipse:InvalidConstraint', ...
                            'Invalid constraint specified')
                end
        end % switch property
    end % while
    
    end % parseinputs
'''

def test_main():
    from numpy import mat
    
    ## Test FITELLIPSE - run through all possibilities
    # Example
    ## 1) Linear fit, bookstein constraint
    # Data points
    x = mat( "1 2 5 7 9 6 3 8; 7 6 8 7 5 7 2 4" )
    
    z, a, b, alpha = fitellipse(x, 'linear')
    
    ## 2) Linear fit, Trace constraint
    # Data points
    x = mat( "1 2 5 7 9 6 3 8; 7 6 8 7 5 7 2 4" )
    
    z, a, b, alpha = fitellipse(x, 'linear', constraint = 'trace')
    
    ## 3) Nonlinear fit
    # Data points
    x = mat( "1 2 5 7 9 6 3 8; 7 6 8 7 5 7 2 4" )
    
    z, a, b, alpha = fitellipse(x)
    
    # Changing the tolerance, maxits
    z, a, b, alpha = fitellipse(x, tol = 1e-8, maxits = 100)
    
    '''
    %% Plotting
    hF = figure();
    hAx = axes('Parent', hF);
    h = plotellipse(hAx, z, a, b, alpha, 'r.');
    
    hold on
    plotellipse(z, a, b, alpha)
    '''

def test2():
    matlab_pts = '[ -0.114374090767  -0.044  ;  -0.125082007641  0.0265859306118  ;  -0.156045389318  0.0895227803882  ;  -0.203908872948  0.13799036509  ;  -0.2634857074  0.166736469863  ;  -0.328319818233  0.172646008213  ;  -0.391385423532  0.155078589964  ;  -0.445848386399  0.11593791747  ;  -0.485806799728  0.0594654899254  ;  -0.506930549417  -0.00821902888511  ;  -0.506930549417  -0.0797809711149  ;  -0.485806799728  -0.147465489925  ;  -0.445848386399  -0.20393791747  ;  -0.391385423532  -0.243078589964  ;  -0.328319818233  -0.260646008213  ;  -0.2634857074  -0.254736469863  ;  -0.203908872948  -0.22599036509  ;  -0.156045389318  -0.177522780388  ;  -0.125082007641  -0.114585930612 ]'
    x = asarray( mat( matlab_pts.strip('[]') ) )
    from pprint import pprint
    pprint( fitellipse(x, 'linear', constraint = 'bookstein') )
    pprint( fitellipse(x, 'linear', constraint = 'trace') )
    pprint( fitellipse(x, 'nonlinear') )

if __name__=='__main__':
    data = make_test_ellipse()

    lsqe = LSqEllipse()
    lsqe.fit(data)
    center, width, height, phi = lsqe.parameters()
    
    # Fit an ellipse using the Bookstein constraint
    [zb, ab, bb, alphab] = fitellipse(data, 'linear')
    center = zb
    width = ab
    height = bb
    phi = alphab
    
    plt.close('all')
    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111)
    ax.axis('equal')
    ax.plot(data[0], data[1], 'ro', label='test data', zorder=1)
    
    ellipse = Ellipse(xy=center, width=2*width, height=2*height, angle=np.rad2deg(phi),
                   edgecolor='b', fc='None', lw=2, label='Fit', zorder = 2)
    ax.add_patch(ellipse)
    
    plt.legend()
    plt.show()