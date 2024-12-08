import numpy as npfrom ..arterial import BloodInputfrom ..core import TACfrom .kineticmodel import KineticModel_Linear, discrete_integratefrom ..typing_utils import NumpyRealNumberArraydef transform_without_blood_correction(cp: NumpyRealNumberArray,                                       ct: NumpyRealNumberArray,                                       t: NumpyRealNumberArray) -> (NumpyRealNumberArray, NumpyRealNumberArray):    """    cp : plasma tac, len = N    ct : target tissue tac, len = N    t : time array (frame mid points), len = N    Returns    -------    xs: scaled time, independent variable for linear regression, RHS, len = N-1    ys: scaled time, dependent variable for linear regression, LHS, len = N-1    """        # integral of cp    intcp = discrete_integrate(cp, t)  # len = N-1        cps = cp[1:]  # N-1    cts = ct[1:]  # N-1        ys = cts / cps   # len = N-1    xs = intcp / cps   # len = N-1        return xs, ys    def transform_with_blood_correction(cp: NumpyRealNumberArray,                                    cb: NumpyRealNumberArray,                                    ct: NumpyRealNumberArray,                                     t: NumpyRealNumberArray) -> (NumpyRealNumberArray, NumpyRealNumberArray):    """    cp : plasma tac, len = N    cb : whole blood tac, len = N    ct : target tissue tac, len = N    t : time array (frame mid points), len = N    Returns    -------    xs: scaled time, independent variable for linear regression, RHS, len = N-1    ys: scaled time, dependent variable for linear regression, LHS, len = N-1    """        VB_fixed = 0.05        # blood activity correction    ct_bc = (ct - VB_fixed * cb) / (1-VB_fixed)  # N    cts = ct_bc[1:]  # N-1        # integral of cp    intcp = discrete_integrate(cp, t)  # len = N-1        cps = cp[1:]   # N-1        ys = cts / cps     # len = N-1    xs = intcp / cps   # len = N-1        return xs, ys        class Patlak_Model(KineticModel_Linear):    def __init__(self,                  binput: BloodInput,                  tacs: TAC,                 transform_type: str):                super().__init__(binput, tacs)                        self.macro_params = {'Ki': None,                             'V0': None}                self.param_unit = {'slope': '/min',                           'intercept': 'unitless',                           'Ki': '/min',                           'V0': 'unitless'}                self.transform_type = transform_type        self.name = 'Patlak'                    def fit(self):                self.xdata = np.zeros((self.tacs.num_elements, self.tacs.num_frames-1))        self.ydata = np.zeros((self.tacs.num_elements, self.tacs.num_frames-1))                for i in range(self.tacs.num_elements):            t = self.tacs.t            cp = self.inp.CP(t)            cb = self.inp.CB(t)            ct = self.tacs.data[i, :]                    if self.transform_type == 'without_blood_correction':                self.xdata[i, :], self.ydata[i, :] = transform_without_blood_correction(cp, ct, t)            elif self.transform_type == 'with_blood_correction':                self.xdata[i, :], self.ydata[i, :] = transform_with_blood_correction(cp, cb, ct, t)                        self.fit_linear()                # set macro params        Ki_arr = np.zeros(self.tacs.num_elements)        V0_arr = np.zeros(self.tacs.num_elements)                for i in range(self.tacs.num_elements):            slope = self.get_parameter('slope')[i]            intercept = self.get_parameter('intercept')[i]                        Ki = slope            V0 = intercept                        Ki_arr[i] = Ki            V0_arr[i] = V0                self.set_parameter('Ki', Ki_arr, 'macro')        self.set_parameter('V0', V0_arr, 'macro')                return None