.. math::
    :label: eqn-ss-PN

    \begin{aligned}
    \mathbf{x}^T &= \left[\begin{matrix}V_{\mathrm{C2}} & V_{\mathrm{C1}} & I_{\mathrm{L1}}\end{matrix}\right] \\
    \mathbf{u}^T &= \left[\begin{matrix}V_{1}\end{matrix}\right] \\
    \mathbf{y}^T &= \left[\begin{matrix}I_{\mathrm{L1}} & I_{\mathrm{V1}} & V_{1} & V_{2} & V_{\mathrm{out}}\end{matrix}\right] \\
    \mathbf{A} &= \left[\begin{matrix}\frac{- R_{\ell} - R_{\mathrm{s}}}{C_{\mathrm{a}} R_{\ell} R_{\mathrm{s}}} & - \frac{1}{C_{\mathrm{a}} R_{\mathrm{s}}} & 0\\- \frac{1}{C_{\mathrm{b}} R_{\mathrm{s}}} & - \frac{1}{C_{\mathrm{b}} R_{\mathrm{s}}} & - \frac{1}{C_{\mathrm{b}}}\\0 & \frac{1}{L} & 0\end{matrix}\right] \\
    \mathbf{B} &= \left[\begin{matrix}\frac{1}{C_{\mathrm{a}} R_{\mathrm{s}}}\\\frac{1}{C_{\mathrm{b}} R_{\mathrm{s}}}\\0\end{matrix}\right] \\
    \mathbf{C} &= \left[\begin{matrix}0 & 0 & 1\\\frac{1}{R_{\mathrm{s}}} & \frac{1}{R_{\mathrm{s}}} & 0\\0 & 0 & 0\\1 & 1 & 0\\1 & 0 & 0\end{matrix}\right] \\
    \mathbf{D} &= \left[\begin{matrix}0\\- \frac{1}{R_{\mathrm{s}}}\\1\\0\\0\end{matrix}\right]
    \end{aligned}

