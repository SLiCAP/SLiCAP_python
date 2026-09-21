.. math::
    :label: eqn-ss-PN

    \begin{aligned}
    \mathbf{x}^T &= \left[\begin{matrix}V_{C2} & V_{C1} & I_{L1}\end{matrix}\right] \\
    \mathbf{u}^T &= \left[\begin{matrix}V_{1}\end{matrix}\right] \\
    \mathbf{y}^T &= \left[\begin{matrix}I_{L1} & I_{V1} & V_{1} & V_{2} & V_{out}\end{matrix}\right] \\
    \mathbf{A} &= \left[\begin{matrix}\frac{- R_{\ell} - R_{s}}{C_{a} R_{\ell} R_{s}} & - \frac{1}{C_{a} R_{s}} & 0\\- \frac{1}{C_{b} R_{s}} & - \frac{1}{C_{b} R_{s}} & - \frac{1}{C_{b}}\\0 & \frac{1}{L} & 0\end{matrix}\right] \\
    \mathbf{B} &= \left[\begin{matrix}\frac{1}{C_{a} R_{s}}\\\frac{1}{C_{b} R_{s}}\\0\end{matrix}\right] \\
    \mathbf{C} &= \left[\begin{matrix}0 & 0 & 1\\\frac{1}{R_{s}} & \frac{1}{R_{s}} & 0\\0 & 0 & 0\\1 & 1 & 0\\1 & 0 & 0\end{matrix}\right] \\
    \mathbf{D} &= \left[\begin{matrix}0\\- \frac{1}{R_{s}}\\1\\0\\0\end{matrix}\right]
    \end{aligned}

