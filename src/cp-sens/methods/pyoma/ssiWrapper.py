import typing
import logging

from pyoma2.algorithms.data.result import SSIResult
from pyoma2.algorithms.data.run_params import SSIRunParams
from pyoma2.algorithms.base import BaseAlgorithm
from pyoma2.functions import plot, ssi
from pyoma2.support.sel_from_plot import SelFromPlot
from pyoma import genWrapper as gen

class SSIdat(BaseAlgorithm[SSIRunParams, SSIResult, typing.Iterable[float]]):
    """
    Data-Driven Stochastic Subspace Identification (SSI) algorithm for single setup
    analysis.

    This class processes measurement data from a single setup experiment to identify
    and extract modal parameters using the SSIdat-ref method.

    Attributes
    ----------
    RunParamCls : Type[SSIRunParams]
        The class of parameters specific to this algorithm's run.
    ResultCls : Type[SSIResult]
        The class of results produced by this algorithm.
    method : str
        The method used in this SSI algorithm, set to 'dat' by default.
    """

    RunParamCls = SSIRunParams
    ResultCls = SSIResult
    method: typing.Literal["dat"] = "dat"

    def run(self) -> SSIResult:
        """
        Executes the SSIdat algorithm and returns the results.

        Processes the input data using the Data-Driven Stochastic Subspace Identification method.
        Computes state space matrices, modal parameters, and other relevant results.

        Returns
        -------
        SSIResult
            An object containing the computed matrices and modal parameters.
        """
        Y = self.data.T
        br = self.run_params.br
        method_hank = self.run_params.method or self.method
        ordmin = self.run_params.ordmin
        ordmax = self.run_params.ordmax
        step = self.run_params.step
        sc = self.run_params.sc
        hc = self.run_params.hc
        calc_unc = self.run_params.calc_unc
        nb = self.run_params.nb

        if self.run_params.ref_ind is not None:
            ref_ind = self.run_params.ref_ind
            Yref = Y[ref_ind, :]
        else:
            Yref = Y

        # Build Hankel matrix
        H, T = ssi.build_hank(
            Y=Y, Yref=Yref, br=br, method=method_hank, calc_unc=calc_unc, nb=nb
        )
        # Get state matrix and output matrix
        Obs, A, C, Q1, Q2, Q3, Q4 = ssi.SSI_fast(
            H, br, ordmax, step=step, calc_unc=calc_unc, T=T, nb=nb
        )

        # Get frequency poles (and damping and mode shapes)
        Fns, Xis, Phis, Lambds, Fn_cov, Xi_cov, Phi_cov = ssi.SSI_poles(
            Obs,
            A,
            C,
            ordmax,
            self.dt,
            step=step,
            calc_unc=calc_unc,
            Q1=Q1,
            Q2=Q2,
            Q3=Q3,
            Q4=Q4,
        )

        hc_conj = hc["conj"]
        hc_xi_max = hc["xi_max"]
        # print(f'highest limit for damping: {hc_xi_max}')
        hc_mpc_lim = hc["mpc_lim"]
        hc_mpd_lim = hc["mpd_lim"]
        hc_cov_max = hc["cov_max"]
        
        
        # Criteria regarding eigenvalue stability
        # HC - remove eigevalues with positive real part
        Lambds, mask6 = gen.HC_realEigen(Lambds)
        lista = [Fns, Xis, Phis, Fn_cov, Xi_cov, Phi_cov]
        Fns, Xis, Phis, Fn_cov, Xi_cov, Phi_cov = gen.applymask(
            lista, mask6, Phis.shape[2]
            )
        
        # Criteria regarding zero imaginary part in eigenvalues
        # HC - remove eigenvalues with zero imaginary part of eigenvalues
        Lambds, mask7 = gen.HC_removeZeroImg(Lambds)
        lista = [Fns, Xis, Phis, Fn_cov, Xi_cov, Phi_cov]
        Fns, Xis, Phis, Fn_cov, Xi_cov, Phi_cov = gen.applymask(
            lista, mask7, Phis.shape[2]
            )
       
      
        # Get the labels of the poles
        Lab = gen.SC_apply(
            Fns,
            Xis,
            Phis,
            ordmin,
            ordmax,
            step,
            sc["err_fn"],
            sc["err_xi"],
            sc["err_phi"],
        )

        return SSIResult(
            Obs=Obs,
            A=A,
            C=C,
            H=H,
            Lambds=Lambds,
            Fn_poles=Fns,
            Xi_poles=Xis,
            Phi_poles=Phis,
            Lab=Lab,
            Fn_poles_cov=Fn_cov,
            Xi_poles_cov=Xi_cov,
            Phi_poles_cov=Phi_cov,
        )

    def mpe(
        self,
        sel_freq: typing.List[float],
        order: typing.Union[int, str] = "find_min",
        rtol: float = 5e-2,
    ) -> typing.Any:
        """
        Extracts the modal parameters at the selected frequencies.

        Parameters
        ----------
        sel_freq : list of float
            Selected frequencies for modal parameter extraction.
        order : int or str, optional
            Model order for extraction, or 'find_min' to auto-determine the minimum stable order.
            Default is 'find_min'.
        rtol : float, optional
            Relative tolerance for comparing frequencies. Default is 5e-2.

        Returns
        -------
        typing.Any
            The extracted modal parameters. The format and content depend on the algorithm's implementation.
        """
        super().mpe(sel_freq=sel_freq, order=order, rtol=rtol)

        # Save run parameters
        self.run_params.sel_freq = sel_freq
        self.run_params.order_in = order
        self.run_params.rtol = rtol

        # Get poles
        Fn_pol = self.result.Fn_poles
        Xi_pol = self.result.Xi_poles
        Phi_pol = self.result.Phi_poles
        Lab = self.result.Lab
        # Get cov
        Fn_pol_cov = self.result.Fn_poles_cov
        Xi_pol_cov = self.result.Xi_poles_cov
        Phi_pol_cov = self.result.Phi_poles_cov
        # Extract modal results
        Fn, Xi, Phi, order_out, Fn_cov, Xi_cov, Phi_cov = ssi.SSI_mpe(
            sel_freq,
            Fn_pol,
            Xi_pol,
            Phi_pol,
            order,
            Lab=Lab,
            rtol=rtol,
            Fn_cov=Fn_pol_cov,
            Xi_cov=Xi_pol_cov,
            Phi_cov=Phi_pol_cov,
        )

        # Save results
        self.result.order_out = order_out
        self.result.Fn = Fn
        self.result.Xi = Xi
        self.result.Phi = Phi
        self.result.Fn_cov = Fn_cov
        self.result.Xi_cov = Xi_cov
        self.result.Phi_cov = Phi_cov

    def mpe_from_plot(
        self,
        freqlim: typing.Optional[tuple[float, float]] = None,
        rtol: float = 1e-2,
    ) -> typing.Any:
        """
        Interactive method for extracting modal parameters by selecting frequencies from a plot.

        Parameters
        ----------
        freqlim : tuple of float, optional
            Frequency limits for the plot. If None, limits are determined automatically. Default is None.
        rtol : float, optional
            Relative tolerance for comparing frequencies. Default is 1e-2.

        Returns
        -------
        typing.Any
            The extracted modal parameters after interactive selection. Format depends on algorithm's
            implementation.
        """
        super().mpe_from_plot(freqlim=freqlim, rtol=rtol)

        # Save run parameters
        self.run_params.rtol = rtol

        # Get poles
        Fn_pol = self.result.Fn_poles
        Xi_pol = self.result.Xi_poles
        Phi_pol = self.result.Phi_poles
        # Get cov
        Fn_pol_cov = self.result.Fn_poles_cov
        Xi_pol_cov = self.result.Xi_poles_cov
        Phi_pol_cov = self.result.Phi_poles_cov

        # call interactive plot
        SFP = SelFromPlot(algo=self, freqlim=freqlim, plot="SSI")
        sel_freq = SFP.result[0]
        order = SFP.result[1]

        # and then extract results
        Fn, Xi, Phi, order_out, Fn_cov, Xi_cov, Phi_cov = ssi.SSI_mpe(
            sel_freq,
            Fn_pol,
            Xi_pol,
            Phi_pol,
            order,
            Lab=None,
            rtol=rtol,
            Fn_cov=Fn_pol_cov,
            Xi_cov=Xi_pol_cov,
            Phi_cov=Phi_pol_cov,
        )

        # Save results
        self.result.order_out = order_out
        self.result.Fn = Fn
        self.result.Xi = Xi
        self.result.Phi = Phi
        self.result.Fn_cov = Fn_cov
        self.result.Xi_cov = Xi_cov
        self.result.Phi_cov = Phi_cov

    def plot_stab(
        self,
        freqlim: typing.Optional[tuple[float, float]] = None,
        hide_poles: typing.Optional[bool] = True,
    ) -> typing.Any:
        """
        Plot the Stability Diagram for the SSI algorithms.

        The Stability Diagram helps visualize the stability of identified poles across different
        model orders, making it easier to separate physical poles from spurious ones.

        Parameters
        ----------
        freqlim : tuple of float, optional
            Frequency limits for the plot. If None, limits are determined automatically. Default is None.
        hide_poles : bool, optional
            Option to hide poles in the plot for clarity. Default is True.

        Returns
        -------
        typing.Any
            A tuple containing the matplotlib figure and axes of the Stability Diagram plot.
        """
        if not self.result:
            raise ValueError("Run algorithm first")

        fig, ax = plot.stab_plot(
            Fn=self.result.Fn_poles,
            Lab=self.result.Lab,
            step=self.run_params.step,
            ordmax=self.run_params.ordmax,
            ordmin=self.run_params.ordmin,
            freqlim=freqlim,
            hide_poles=hide_poles,
            fig=None,
            ax=None,
            Fn_cov=self.result.Fn_poles_cov,
        )
        return fig, ax

    def plot_cluster(
        self,
        freqlim: typing.Optional[tuple[float, float]] = None,
        hide_poles: typing.Optional[bool] = True,
    ) -> typing.Any:
        """
        Plot the frequency-damping cluster diagram for the identified modal parameters.

        The cluster diagram visualizes the relationship between frequencies and damping
        ratios for the identified poles, helping to identify clusters of physical modes.

        Parameters
        ----------
        freqlim : tuple of float, optional
            Frequency limits for the plot. If None, limits are determined automatically. Default is None.
        hide_poles : bool, optional
            Option to hide poles in the plot for clarity. Default is True.

        Returns
        -------
        typing.Any
            A tuple containing the matplotlib figure and axes of the cluster diagram plot.
        """
        if not self.result:
            raise ValueError("Run algorithm first")

        fig, ax = plot.cluster_plot(
            Fn=self.result.Fn_poles,
            Xi=self.result.Xi_poles,
            Lab=self.result.Lab,
            ordmin=self.run_params.ordmin,
            freqlim=freqlim,
            hide_poles=hide_poles,
        )
        return fig, ax

    def plot_svalH(
        self,
        iter_n: typing.Optional[int] = None,
    ) -> typing.Any:
        """
        Plot the singular values of the Hankel matrix for the SSI algorithm.

        This plot is useful for checking the influence of the number of block-rows, br,
        on the Singular Values of the Hankel matrix.

        Parameters
        ----------
        iter_n : int, optional
            The iteration number for which to plot the singular values. If None, the last
            iteration is used. Default is None.

        Returns
        -------
        typing.Any
            A tuple containing the matplotlib figure and axes of the singular value plot.

        Raises
        ------
        ValueError
            If the algorithm has not been run before plotting.
        """
        if not self.result:
            raise ValueError("Run algorithm first")

        fig, ax = plot.svalH_plot(H=self.result.H, br=self.run_params.br, iter_n=iter_n)
        return fig, ax










class SSIcov(SSIdat):
    """
    Implements the Covariance-driven Stochastic Subspace Identification (SSI) algorithm
    for single setup experiments.

    This class is an extension of the SSIdat class, adapted for covariance-driven analysis.
    It processes measurement data from a single setup to identify system dynamics and extract
    modal parameters using the SSIcov-ref method.

    Inherits all attributes and methods from SSIdat.

    Attributes
    ----------
    method : str
        The method used in this SSI algorithm, overridden to 'cov_bias', 'cov_mm', or 'cov_unb' for
        covariance-based analysis.

    Methods
    -------
    Inherits all methods from SSIdat with covariance-specific implementations.
    """

    method: typing.Literal["cov_R", "cov_mm"] = "cov_mm"





