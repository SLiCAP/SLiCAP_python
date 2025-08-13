#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
laplace.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl
import sympy as sp

passive_network = sl.makeCircuit("kicad/myPassiveNetwork/myPassiveNetwork.kicad_sch")

# Obtain the transfer from source to detector
result = sl.doLaplace(passive_network)
gain   = result.laplace
print(gain)

M        = result.M
Iv       = result.Iv
Dv       = result.Dv
denom    = result.denom
numer    = result.numer
transfer = result.laplace

# Same, but with parameter substitution and conversion to floats
gain_numeric = sl.doLaplace(passive_network, pardefs="circuit", numeric=True).laplace
print(gain_numeric)

vout_laplace = sl.doLaplace(passive_network, transfer=None).laplace

gain_factor, numer_coeffs, denom_coeffs = sl.coeffsTransfer(gain)
print("\nGain factor: ", gain_factor)
print("\nNumerator coefficients of 's':")
for i in range(len(numer_coeffs)):
    print(str(i), numer_coeffs[i])
print("\nDenominator coefficients of 's':")
for i in range(len(denom_coeffs)):
    print(str(i), denom_coeffs[i])

# Obtain a normalized Butterworth polynomial of the 4th order
BuP = sl.butterworthPoly(4)

# Obtain a normalized Bessel polynomial of the 4th order
BeP = sl.besselPoly(4)

# Obtain a normalized Chebyshev polynomial of the 4th order 
# with 1 dB pass-band ripple
ChP = sl.chebyshev1Poly(4, 1)

# Obtain filter functions
n   = 2                # Order of the filter
f_h = sp.Symbol("f_h") # Low-frequency -3dB
f_l = sp.Symbol("f_l") # High-frequency -3dB
ftp = "Butterworth"    # Fiter characteristic

LP = sl.filterFunc(ftp, "lp", n, f_low=f_l, f_high=f_h) # Low-pass
HP = sl.filterFunc(ftp, "hp", n, f_low=f_l, f_high=f_h) # High-pass
BP = sl.filterFunc(ftp, "bp", n, f_low=f_l, f_high=f_h) # Band-pass
BS = sl.filterFunc(ftp, "bs", n, f_low=f_l, f_high=f_h) # Band-stop
AP = sl.filterFunc(ftp, "ap", n, f_low=f_l, f_high=f_h) # All-pass

# 3-rd order Chebyshev band-pass 900-1200 Hz
BP_num   = sp.N(sl.filterFunc("Chebyshev1", "bp", 3, f_low=900, f_high=1200,
                              ripple=1))

# Plot with an instruction object, this comprises plot settings and results
filt          = sl.instruction()
filt.gainType = "gain"
filt.dataType = "laplace"
filt.laplace  = BP_num
filt.label    = "gain"

# Create the plot
sl.plotSweep("BP4", "3-rd order Chebyshev type 1 band-pass, 1 dB ripple", 
             filt, 0.1, 10, 500, sweepScale="k", funcType="dBmag", show=False)

# Generate RST snippets for the Help file
rst = sl.RSTformatter()

rst.eqn("V_out/V_V1", gain).save("eqn-laplace-passive")
rst.matrixEqn(result.Iv, result.M, result.Dv).save("eqn-matrix-passive")
rst.eqn("V_out/V_V1", gain_numeric).save("eqn-laplace-passive-numeric")
rst.eqn("V_out", vout_laplace).save("eqn-laplace-passive-vout")
rst.coeffsTransfer(sl.coeffsTransfer(gain), 
                   caption="Normalized coefficients of 'gain'.").save("table-coeffs-gain")
rst.eqn("P_Bu", BuP,).save("eqn-BuP")
rst.eqn("P_Be", BeP,).save("eqn-BeP")
rst.eqn("P_Ch", ChP,).save("eqn-ChP")
rst.eqn("F_LP", LP,).save("eqn-FLP")
rst.eqn("F_HP", HP,).save("eqn-FHP")
rst.eqn("F_BP", BP,).save("eqn-FBP")
rst.eqn("F_BS", BS,).save("eqn-FBS")
rst.eqn("F_AP", AP,).save("eqn-FAP")
rst.eqn("H_s", BP_num).save("eqn-BP_num")

# Generate LaTeX snippets for the Help file
ltx = sl.LaTeXformatter()

ltx.eqn("V_out/V_V1", gain).save("eqn-laplace-passive")
ltx.matrixEqn(result.Iv, result.M, result.Dv).save("eqn-matrix-passive")
ltx.eqn("V_out/V_V1", gain_numeric).save("eqn-laplace-passive-numeric")
ltx.eqn("V_out", vout_laplace).save("eqn-laplace-passive-vout")
ltx.coeffsTransfer(sl.coeffsTransfer(gain), 
                   caption="Normalized coefficients of 'gain'.").save("table-coeffs-gain")
ltx.eqn("P_Bu", BuP,).save("eqn-BuP")
ltx.eqn("P_Be", BeP,).save("eqn-BeP")
ltx.eqn("F_LP", LP,).save("eqn-FLP")
ltx.eqn("F_HP", HP,).save("eqn-FHP")
ltx.eqn("F_BP", BP,).save("eqn-FBP")
ltx.eqn("F_BS", BS,).save("eqn-FBS")
ltx.eqn("F_AP", AP,).save("eqn-FAP")
ltx.eqn("H_s", BP_num).save("eqn-BP_num")