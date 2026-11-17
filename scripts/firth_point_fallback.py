"""Same Jeffreys-penalized objective, independently checked numerical fallback."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


def objective_score(beta, design, y, weights):
    eta=design@beta;p=expit(eta);v=weights*p*(1-p)
    information=design.T@(v[:,None]*design)
    sign,logdet=np.linalg.slogdet(information)
    if sign<=0:raise np.linalg.LinAlgError('Nonpositive information determinant')
    h=v*np.einsum('ij,ji->i',design,np.linalg.solve(information,design.T))
    score=design.T@(weights*(y-p)+h*(.5-p))
    loglik=float(weights@(y*eta-np.logaddexp(0,eta))+.5*logdet)
    return loglik,score


def verified_point(X,y,weights,start):
    """Never change the penalty, sample, or score acceptance threshold."""
    design=np.column_stack([X,np.ones(len(X))])
    initial,gradient=objective_score(start,design,y,weights)
    if np.max(np.abs(gradient))<1e-5:return start,False
    def fun(beta):
        ll,score=objective_score(beta,design,y,weights)
        return -ll,-score
    result=minimize(fun,start,jac=True,method='BFGS',options={'gtol':1e-6,'maxiter':200})
    final,gradient=objective_score(result.x,design,y,weights)
    if (not np.isfinite(result.x).all() or not np.isfinite(final) or final<initial-1e-7
            or np.max(np.abs(gradient))>=1e-5):
        raise ValueError('FallbackScoreFailure')
    return result.x,True
