"""
Spectral analysis algorithms for mineral unmixing
"""

import numpy as np
from numpy.linalg import multi_dot


class SpectralAlgorithms:
    """Implementation of spectral unmixing algorithms"""
    
    @staticmethod
    def run_WLS(EMdat, M, W, WLSendmembers):
        """
        Run Weighted Least Squares (WLS) algorithm
        
        Parameters:
        -----------
        EMdat : np.ndarray
            End-member spectral data matrix
        M : np.ndarray
            Mixed spectrum
        W : np.ndarray
            Weight matrix (diagonal matrix of 1/uncertainty^2)
        WLSendmembers : np.ndarray
            Names of end-members
        
        Returns:
        --------
        tuple : (fit, residual, endmembers, abundances, errors, rms)
        """
        # Solves: Abundances = (E^T W E)^-1 E^T W M
        WLSA = multi_dot([np.linalg.inv(multi_dot([EMdat, W, EMdat.T])), EMdat, W, M])

        # Find negative abundances, remove them, repeat algorithm
        while (np.around(WLSA, decimals=2) <= 0).any(): 
            Negatives = np.argwhere(np.around(WLSA, decimals=2) <= 0)[:, 0]  # Find indices of negatives
            WLSendmembers = np.delete(WLSendmembers, Negatives)  # List of names
            EMdat = np.delete(EMdat, Negatives, axis=0)  # Delete from endmember matrix
            WLSA = multi_dot([np.linalg.inv(multi_dot([EMdat, W, EMdat.T])), EMdat, W, M])  # Recalculate

        # Fit & errors
        WLSfit = multi_dot([EMdat.T, WLSA])
        WLSaberror = np.sqrt(np.linalg.inv(multi_dot([EMdat, W, EMdat.T])).diagonal())
        WLSresidual = M - WLSfit
        WLSrms = np.sqrt(np.sum(np.square(WLSresidual))/np.size(WLSresidual))

        print('WLS RMS value: ' + repr(WLSrms))

        return WLSfit, WLSresidual, WLSendmembers, WLSA, WLSaberror, WLSrms
    
    @staticmethod
    def run_STO(EMdat, M, W, STOendmembers):
        """
        Run Sum-to-One (STO) algorithm
        
        Parameters:
        -----------
        EMdat : np.ndarray
            End-member spectral data matrix
        M : np.ndarray
            Mixed spectrum
        W : np.ndarray
            Weight matrix (diagonal matrix of 1/uncertainty^2)
        STOendmembers : np.ndarray
            Names of end-members
        
        Returns:
        --------
        tuple : (fit, residual, endmembers, abundances, errors, normalized_abundances, rms)
        """
        # Solves: Abundances = P*A_WLS + (E^T W E)^-1 1 [1^T (E^T W E)^-1 1]^-1
        rows, cols = EMdat.shape
        onesT = np.ones(rows, dtype=np.float64)
        ones = onesT[:, None]
        P1 = multi_dot([np.linalg.inv(multi_dot([EMdat, W, EMdat.T])), ones])
        P2 = 1/(multi_dot([onesT, np.linalg.inv(multi_dot([EMdat, W, EMdat.T])), ones]))*onesT 
        STOP = np.identity(rows)-P1*P2
        WLSA = multi_dot([np.linalg.inv(multi_dot([EMdat, W, EMdat.T])), EMdat, W, M])
        STOA = multi_dot([STOP, WLSA]) + multi_dot([P1, 1/(multi_dot([onesT, np.linalg.inv(multi_dot([EMdat, W, EMdat.T])), ones]))])

        # Find negative abundances, remove them, repeat algorithm
        while (np.around(STOA, decimals=2) <= 0).any(): 
            Negatives = np.argwhere(np.around(STOA, decimals=2) <= 0)[:, 0] 
            STOendmembers = np.delete(STOendmembers, Negatives)
            EMdat = np.delete(EMdat, Negatives, axis=0) 
            rows, cols = EMdat.shape
            onesT = np.ones(rows, dtype=np.float64)
            ones = onesT[:, None]
            P1 = multi_dot([np.linalg.inv(multi_dot([EMdat, W, EMdat.T])), ones])
            P2 = 1/(multi_dot([onesT, np.linalg.inv(multi_dot([EMdat, W, EMdat.T])), ones]))*onesT 
            STOP = np.identity(rows)-P1*P2
            WLSA = multi_dot([np.linalg.inv(multi_dot([EMdat, W, EMdat.T])), EMdat, W, M])
            STOA = multi_dot([STOP, WLSA]) + multi_dot([P1, 1/(multi_dot([onesT, np.linalg.inv(multi_dot([EMdat, W, EMdat.T])), ones]))])

        # Fit & errors
        STOfit = np.dot(STOA, EMdat)
        STOaberror = np.sqrt(np.linalg.inv(multi_dot([EMdat, W, EMdat.T])).diagonal())
        STOresidual = M - STOfit
        STOrms = np.sqrt(np.sum(np.square(STOresidual))/np.size(STOresidual))

        print('Sum to One RMS value: ' + repr(STOrms))
        
        # Normalized values without BB
        if np.any(STOendmembers == 'BB'):
            STOnorm = np.copy(STOA)
            STOnorm[np.where(STOendmembers == 'BB')] = 0
            factor = 1/np.sum(STOnorm)
            STOnorm *= factor
        else:
            STOnorm = np.copy(STOA)
            
        return STOfit, STOresidual, STOendmembers, STOA, STOaberror, STOnorm, STOrms
