*  **********************************************
*  *               SPICE MODELS                 *
*  **********************************************
*
*    PROCESS :  0.18um CMOS (1P6M, 1.8V/3.3V)
*    MODEL   :  BSIM3 ( V3.2 )
*    VERSION :  1.11
*    DATE    :  May. 06, 2001
*    HSPICE VERSION: H98.2 & H98.4
*
********************************************************************************
******************************************************************************
*                                                                            *
*       IN THIS MODEL LIB CONTAINS :                                         *
*                                                                            *
*       1.LIB TT                                                             *
*             SS                                                             *
*             FF                                                             *
*             SF                                                             *
*             FS                                                             *
*        ( 1.8V Normal devices with different geometric and corner models)   *
*                                                                            *
*       2.LIB TT_3V                                                          *
*             SS_3V                                                          *
*             FF_3V                                                          *
*             SF_3V                                                          *
*             FS_3V                                                          *
*        ( 3.3V normal devices  with different geometric and corner models)  *
*                                                                            *
*                                                                            *
*       3.LIB TT_NA                                                          *
*             SS_NA                                                          *
*             FF_NA                                                          *
*             SF_NA                                                          *
*             FS_NA                                                          *
*        ( 1.8V native NMOS with different geometric and corner models)      *
*                                                                            *
*       4.LIB TT_3VNA                                                        *
*             SS_3VNA                                                        *
*             FF_3VNA                                                        *
*             SF_3VNA                                                        *
*             FS_3VNA                                                        *
*        ( 3.3V native NMOS with different geometric and corner models)      *
*                                                                            *
*       5.LIB BIP                                                            *
*        ( 1.8V P+/NW/PSUB 10x10, 5x5 and 2x2 vertical PNP bipolar )         *
*                                                                            *
*       6.LIB BIP3                                                           *
*        ( 3.3V P+/NW/PSUB 10x10, 5x5 and 2x2 vertical PNP bipolar )         *
*                                                                            *
*       7.LIB DIO                                                            *
*        ( 1.8V P+/NW , N+/PW & NW/PSUB diode )                              *
*                                                                            *
*       8.LIB DIO3                                                           *
*        ( 3.3V P+/NW , N+/PW & NW/PSUB diode )                              *
*                                                                            *
*       9.LIB RES                                                            *
*         (resist model)                                                     *
*                                                                            *
******************************************************************************
******************************************************************************
*                                                                            *
* 1)To use these models directly by programming in this style:               *
*                                                                            *
*     .lib 'lib_path/lib_name' model_name                                    *
*                                                                            *
*                                                                            *
*    EX: .lib '/home/user/log018.l' TT                                       *
*        for typical 1.8V N,PMOS                                             *
*        .lib '/home/user/log018.l' TT_3V                                    *
*        for typical 3.3V N,PMOS                                             *
*  note:                                                                     *
*      corner_name                                                           *
*       TT : typical model for 1.8V devices                                  *
*       SS : Slow NMOS Slow PMOS model for 1.8V devices                      *
*       FF : Fast NMOS Fast PMOS model for 1.8V devices                      *
*       SF : Slow NMOS Fast PMOS model for 1.8V devices                      *
*       FS : Fast NMOS Slow PMOS model for 1.8V devices                      *
*                                                                            *
*       TT_3V : typical model for 3.3V devices                               *
*       SS_3V : Slow NMOS Slow PMOS model for 3.3V devices                   *
*       FF_3V : Fast NMOS Fast PMOS model for 3.3V devices                   *
*       SF_3V : Slow NMOS Fast PMOS model for 3.3V devices                   *
*       FS_3V : Fast NMOS Slow PMOS model for 3.3V devices                   *
*                                                                            *
*       TT_NA : typical model for 1.8V native NMOS                           *
*       SS_NA : Slow NMOS for 1.8V native NMOS                               *
*       FF_NA : Fast NMOS for 1.8V native NMOS                               *
*       SF_NA : Slow NMOS for 1.8V native NMOS                               *
*       FS_NA : Fast NMOS for 1.8V native NMOS                               *
*                                                                            *
*       TT_3VNA : typical model for 3.3V native NMOS                         *
*       SS_3VNA : Slow NMOS for 3.3V native NMOS                             *
*       FF_3VNA : Fast NMOS for 3.3V native NMOS                             *
*       SF_3VNA : Slow NMOS for 3.3V native NMOS                             *
*       FS_3VNA : Fast NMOS for 3.3V native NMOS                             *
*                                                                            *
* 2)HDIF depends on your layout poly spacer to contact centre distance.      *
*   The value listed here is the minimum design rule value. You can change it*
*   according to your layout.                                                *
*                                                                            *
******************************************************************************
***************************************************************
*                                                             *
*                1.8V NORMAL DEVICES LIB                      *
*                                                             *
***************************************************************
***************** CORNER_LIB OF TYPICAL MODEL ***************
.LIB TT
.param
+toxn   = 4.08E-09        toxp   = 4.08E-09
+dvthn  = 0               dvthp  = 0
+dxl    = 0               dxw    = 0
+cjn    = 0.001000266     cjp    = 0.001121
+cjswn  = 2.040547E-10    cjswp  = 2.481E-10
+cjswgn = 3.340547E-10    cjswgp = 4.221E-10
+cgon   = 3.665E-10       cgop   = 3.28E-10
+hdifn  = 2E-07           hdifp  = 2E-07
.lib 'log018.l' MOS
.ENDL TT
***************** CORNER_LIB OF SNSP MODEL ***************
.LIB SS
.param
+toxn   = 4.213E-09       toxp   = 4.213E-09
+dvthn  = 0.1             dvthp  = -0.067
+dxl    = 1.33E-08        dxw    = -2.2E-08
+cjn    = 0.001050279     cjp    = 0.00117705
+cjswn  = 2.142574E-10    cjswp  = 2.60505E-10
+cjswgn = 3.507574E-10    cjswgp = 4.43205E-10
+cgon   = 3.48175E-10     cgop   = 3.116E-10
+hdifn  = 2E-07           hdifp  = 2E-07
.lib 'log018.l' MOS
.ENDL SS
***************** CORNER_LIB OF FNFP MODEL ***************
.LIB FF
.param
+toxn   = 3.947E-09       toxp   = 3.947E-09
+dvthn  = -0.1            dvthp  = 0.067
+dxl    = -1.33E-08       dxw    = 2.2E-08
+cjn    = 0.0009502527    cjp    = 0.00106495
+cjswn  = 1.93852E-10     cjswp  = 2.35695E-10
+cjswgn = 3.17352E-10     cjswgp = 4.00995E-10
+cgon   = 3.84825E-10     cgop   = 3.444E-10
+hdifn  = 2E-07           hdifp  = 2E-07
.lib 'log018.l' MOS
.ENDL FF
***************** CORNER_LIB OF SNFP MODEL ***************
.LIB SF
.param
+toxn   = 4.08E-09        toxp   = 4.08E-09
+dvthn  = 0.1             dvthp  = 0.067
+dxl    = 0               dxw    = 0
+cjn    = 0.001050279     cjp    = 0.00106495
+cjswn  = 2.142574E-10    cjswp  = 2.35695E-10
+cjswgn = 3.507574E-10    cjswgp = 4.00995E-10
+cgon   = 3.665E-10       cgop   = 3.28E-10
+hdifn  = 2E-07           hdifp  = 2E-07
.lib 'log018.l' MOS
.ENDL SF
***************** CORNER_LIB OF FNSP MODEL ***************
.LIB FS
.param
+toxn   = 4.08E-09        toxp   = 4.08E-09
+dvthn  = -0.1            dvthp  = -0.067
+dxl    = 0               dxw    = 0
+cjn    = 0.0009502527    cjp    = 0.00117705
+cjswn  = 1.93852E-10     cjswp  = 2.60505E-10
+cjswgn = 3.17352E-10     cjswgp = 4.43205E-10
+cgon   = 3.665E-10       cgop   = 3.28E-10
+hdifn  = 2E-07           hdifp  = 2E-07
.lib 'log018.l' MOS
.ENDL FS
***************************************************************
*                                                             *
*                3.3V NORMAL DEVICES LIB                      *
*                                                             *
***************************************************************
***************** CORNER_LIB OF TYPICAL MODEL ***************
.LIB TT_3V
.param
+toxn3   = 6.8E-09         toxp3   = 6.77E-09    toxe3= 6.98e-09
+dvthn3  = 0               dvthp3  = 0           dvthe3 = 0.0
+dxl3    = 0               dxw3    = 0
+cjn3    = 0.0008964788    cjp3    = 0.00103531  cje3 = 1.05363E-3
+cjswn3  = 2.50664E-10     cjswp3  = 2.23115E-10   cjswe3 = 3.36255E-10
+cjswgn3 = 3.00664E-10     cjswgp3 = 2.345762E-10  cjswge3 = 3.36255E-10
+cgon3   = 3.18E-10        cgop3   = 2.77E-10      cgoe3= 4.444E-10
+hdifn3  = 2E-07           hdifp3  = 2E-07         hdife3 = 1.50e-06
.lib 'log018.l' MOS_3V
.ENDL TT_3V
***************** CORNER_LIB OF SNSP MODEL ***************
.LIB SS_3V
.param
+toxn3   = 7.5E-09         toxp3   = 7.47E-09       toxe3= 7.68e-09
+dvthn3  = 0.1             dvthp3  = -0.1           dvthe3= 0.1
+dxl3    = 1.33E-08        dxw3    = -2.2E-08
+cjn3    = 0.0009413027    cjp3    = 0.001087076    cje3 = 1.10631E-3
+cjswn3  = 2.631972E-10    cjswp3  = 2.342708E-10   cjswe3 = 3.53068E-10
+cjswgn3 = 3.156972E-10    cjswgp3 = 2.46305E-10    cjswge3 = 3.53068E-10
+cgon3   = 3.021E-10       cgop3   = 2.6315E-10     cgoe3= 4.2218E-10
+hdifn3  = 2E-07           hdifp3  = 2E-07          hdife3 = 1.50e-06
.lib 'log018.l' MOS_3V
.ENDL SS_3V
***************** CORNER_LIB OF FNFP MODEL ***************
.LIB FF_3V
.param
+toxn3   = 6.1E-09         toxp3   = 6.07E-09       toxe3= 6.28e-09
+dvthn3  = -0.1            dvthp3  = 0.1            dvthe3= -0.1
+dxl3    = -1.33E-08       dxw3    = 2.2E-08
+cjn3    = 0.0008516549    cjp3    = 0.0009835445   cje3 = 1.00095E-3
+cjswn3  = 2.381308E-10    cjswp3  = 2.119593E-10   cjswe3 = 3.19442E-10
+cjswgn3 = 2.856308E-10    cjswgp3 = 2.228474E-10   cjswge3 = 3.19442E-10
+cgon3   = 3.339E-10       cgop3   = 2.9085E-10     cgoe3= 4.6662E-10
+hdifn3  = 2E-07           hdifp3  = 2E-07          hdife3 = 1.50e-06
.lib 'log018.l' MOS_3V
.ENDL FF_3V
***************** CORNER_LIB OF SNFP MODEL ***************
.LIB SF_3V
.param
+toxn3   = 6.8E-09         toxp3   = 6.77E-09       toxe3= 6.98e-09
+dvthn3  = 0.1             dvthp3  = 0.1            dvthe3= 0.1
+dxl3    = 0               dxw3    = 0
+cjn3    = 0.0009413027    cjp3    = 0.0009835445   cje3 = 1.10631E-3
+cjswn3  = 2.631972E-10    cjswp3  = 2.119593E-10   cjswe3 = 3.53068E-10
+cjswgn3 = 3.156972E-10    cjswgp3 = 2.228474E-10   cjswge3 = 3.53068E-10
+cgon3   = 3.18E-10        cgop3   = 2.77E-10       cgoe3= 4.444E-10
+hdifn3  = 2E-07           hdifp3  = 2E-07          hdife3 = 1.50e-06
.lib 'log018.l' MOS_3V
.ENDL SF_3V
***************** CORNER_LIB OF FNSP MODEL ***************
.LIB FS_3V
.param
+toxn3   = 6.8E-09         toxp3   = 6.77E-09       toxe3= 6.98e-09
+dvthn3  = -0.1            dvthp3  = -0.1           dvthe3= -0.1
+dxl3    = 0               dxw3    = 0
+cjn3    = 0.0008516549    cjp3    = 0.001087076    cje3 = 1.00095E-3
+cjswn3  = 2.381308E-10    cjswp3  = 2.342708E-10   cjswe3 = 3.19442E-10
+cjswgn3 = 2.856308E-10    cjswgp3 = 2.46305E-10    cjswge3 = 3.19442E-10
+cgon3   = 3.18E-10        cgop3   = 2.77E-10       cgoe3= 4.444E-10
+hdifn3  = 2E-07           hdifp3  = 2E-07          hdife3 = 1.50e-06
.lib 'log018.l' MOS_3V
.ENDL FS_3V
***************************************************************
*                                                             *
*               1.8V NATIVE NMOS LIB                          *
*                                                             *
***************************************************************
***************** CORNER_LIB OF TYPICAL MODEL ***************
.LIB TT_NA
.param
+toxna   = 4.08E-09        cjna    = 0.0001337865    cjswna  = 1.553397E-10
+cjswgna = 3.173876E-10    cgona   = 5.553E-10
+dvthna  = 0               hdifna  = 2E-07
+dxlna   = 0               dxwna   = 0
.lib 'log018.l' MOSNA
.ENDL TT_NA
***************** CORNER_LIB OF SNSP MODEL ***************
.LIB SS_NA
.param
+toxna   = 4.213E-09       cjna    = 0.0001404758    cjswna  = 1.631067E-10
+cjswgna = 3.33257E-10     cgona   = 5.27535E-10
+dvthna  = 0.08            hdifna  = 2E-07
+dxlna   = 1.33E-08        dxwna   = -2.2E-08
.lib 'log018.l' MOSNA
.ENDL SS_NA
***************** CORNER_LIB OF FNFP MODEL ***************
.LIB FF_NA
.param
+toxna   = 3.947E-09       cjna    = 0.0001270972    cjswna  = 1.475727E-10
+cjswgna = 3.015182E-10    cgona   = 5.83065E-10
+dvthna  = -0.08           hdifna  = 2E-07
+dxlna   = -1.33E-08       dxwna   = 2.2E-08
.lib 'log018.l' MOSNA
.ENDL FF_NA
***************** CORNER_LIB OF SNFP MODEL ***************
.LIB SF_NA
.param
+toxna   = 4.08E-09        cjna    = 0.0001404758    cjswna  = 1.631067E-10
+cjswgna = 3.33257E-10     cgona   = 5.553E-10
+dvthna  = 0.08            hdifna  = 2E-07
+dxlna   = 0               dxwna   = 0
.lib 'log018.l' MOSNA
.ENDL SF_NA
***************** CORNER_LIB OF FNSP MODEL ***************
.LIB FS_NA
.param
+toxna   = 4.08E-09        cjna    = 0.0001270972    cjswna  = 1.475727E-10
+cjswgna = 3.015182E-10    cgona   = 5.553E-10
+dvthna  = -0.08           hdifna  = 2E-07
+dxlna   = 0               dxwna   = 0
.lib 'log018.l' MOSNA
.ENDL FS_NA
***************************************************************
*                                                             *
*               3.3V NATIVE NMOS LIB                          *
*                                                             *
***************************************************************
***************** CORNER_LIB OF TYPICAL MODEL ***************
.LIB TT_3VNA
.param
+toxna3 = 6.8E-09         cjna3  = 0.0001247448    cjswna3= 1.458794E-10
+cjswgna3 = 3.180842E-10    cgona3   = 4.942E-10
+dvthna3  = 0               hdifna3  = 2E-08
+dxlna3    = 0              dxwna3    = 0
.lib 'log018.l' MOSNA3
.ENDL TT_3VNA
***************** CORNER_LIB OF SNSP MODEL ***************
.LIB SS_3VNA
.param
+toxna3 = 7.5E-09         cjna3  = 0.000130982     cjswna3= 1.531734E-10
+cjswgna3 = 3.339884E-10    cgona3   = 4.6949E-10
+dvthna3  = 0.1             hdifna3  = 2E-08
+dxlna3    = 1.33E-08       dxwna3    = -2.2E-08
.lib 'log018.l' MOSNA3
.ENDL SS_3VNA
***************** CORNER_LIB OF FNFP MODEL ***************
.LIB FF_3VNA
.param
+toxna3 = 6.1E-09         cjna3  = 0.0001185076    cjswna3= 1.385854E-10
+cjswgna3 = 3.0218E-10      cgona3   = 5.1891E-10
+dvthna3  = -0.1            hdifna3  = 2E-08
+dxlna3    = -1.33E-08      dxwna3    = 2.2E-08
.lib 'log018.l' MOSNA3
.ENDL FF_3VNA
***************** CORNER_LIB OF SNFP MODEL ***************
.LIB SF_3VNA
.param
+toxna3 = 6.8E-09         cjna3  = 0.000130982     cjswna3= 1.531734E-10
+cjswgna3 = 3.339884E-10    cgona3   = 4.942E-10
+dvthna3  = 0.1             hdifna3  = 2E-08
+dxlna3    = 0              dxwna3    = 0
.lib 'log018.l' MOSNA3
.ENDL SF_3VNA
***************** CORNER_LIB OF FNSP MODEL ***************
.LIB FS_3VNA
.param
+toxna3 = 6.8E-09         cjna3  = 0.0001185076    cjswna3= 1.385854E-10
+cjswgna3 = 3.0218E-10      cgona3   = 4.942E-10
+dvthna3  = -0.1            hdifna3  = 2E-08
+dxlna3    = 0              dxwna3    = 0
.lib 'log018.l' MOSNA3
.ENDL FS_3VNA

.LIB MOS
***************************************************************
*                                                             *
*               1.8V  MOS DEVICES MODEL                       *
*                                                             *
***************************************************************
*
.MODEL nch.1            NMOS   (                    LMIN     = '1.2E-06-dxl'
+LMAX    = 2.1E-05        WMIN     = '1.01E-05-dxw' WMAX     = 0.000101
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.4452004+dvthn' LVTH0    = 4.083943E-08   WVTH0    = -1.48489E-07
+PVTH0   = 1.993185E-13   K1       = 0.5099412      LK1      = 3.668304E-08
+WK1     = 2.766093E-08   PK1      = -2.19267E-13   K2       = 0.01695608
+LK2     = -1.755245E-08  WK2      = -1.034945E-08  PK2      = 6.480148E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 90659.09       LVSAT    = -0.006564545
+UA      = -7.469327E-10  LUA      = 2.025139E-16   WUA      = 1.830494E-15
+PUA     = -6.726249E-21  UB       = 2.910666E-18   LUB      = -1.955871E-25
+WUB     = -6.764042E-24  PUB      = 9.411708E-30   UC       = 1.641302E-10
+LUC     = -2.017381E-17  WUC      = -5.974077E-16  PUC      = 5.963958E-22
+RDSW    = 170            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.04590562     LU0      = 3.578498E-09
+WU0     = -4.055627E-08  PU0      = -2.913943E-15  A0       = 0.2119483
+LA0     = -5.177149E-08  WA0      = 1.948019E-06   PA0      = -3.003349E-12
+KETA    = -0.005987795   LKETA    = -2.748571E-08  WKETA    = 1.97602E-07
+PKETA   = -1.586947E-13  A1       = 0              A2       = 0.99
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1498675     LVOFF    = 4.906377E-09   WVOFF    = 1.042303E-07
+PVOFF   = -1.550514E-13  NFACTOR  = 1              CIT      = -0.0001267591
+LCIT    = 2.665205E-10   CDSC     = 0              CDSCB    = 0
+CDSCD   = 0              ETA0     = 5E-05          ETAB     = -5E-05
+DSUB    = 0              PCLM     = 0.7736364      LPCLM    = 2.625818E-07
+PDIBLC1 = 1E-06          PDIBLC2  = 0.0003968181   LPDIBLC2 = 3.019691E-09
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 1.736364E+08
+LPSCBE1 = 262.5818       PSCBE2   = 1E-06          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 0.448150714    BETA0    = 11.59263
+KT1     = -0.2281038     LKT1     = 1.487402E-08   WKT1     = 4.09886E-08
+PKT1    = -1.499301E-13  KT2      = -0.02603289    LKT2     = 8.023716E-10
+WKT2    = -4.269E-08     PKT2     = -8.087905E-15  AT       = 20000
+UTE     = -1.606637      LUTE     = 4.379861E-08   WUTE     = 2.685053E-07
+PUTE    = -4.4149E-13    UA1      = 1.224E-09      UB1      = -1.459973E-18
+LUB1    = 5.961568E-25   WUB1     = 3.423235E-24   PUB1     = -6.00926E-30
+UC1     = -5.990395E-11  LUC1     = 1.037438E-16   WUC1     = 7.225532E-16
+PUC1    = -1.045737E-21  KT1L     = 0              PRT      = 0
+CJ      = cjn            PB       = 0.6882682      MJ       = 0.3595262
+CJSW    = cjswn          PBSW     = 0.6882682      MJSW     = 0.2003879
+CJSWG   = cjswgn         PBSWG    = 0.6882682      MJSWG    = 0.43879
+CGDO    = cgon           CGSO     = cgon           TCJ      = 0.001040287
+TCJSW   = 0.000645489    TCJSWG   = 0.000645489    TPB      = 0.001554306    TPBSW    = 0.001554306    TPBSWG   = 0.001554306
+JS      = 8.38E-06       JSW      = 1.6E-11
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0
+CALCACM  = 1
+ALPHA0   = 0             DLC      = 3E-9           LLC      = -0.039        )


.MODEL nch.2            NMOS   (                    LMIN     = '5E-07-dxl'
+LMAX    = '1.2E-06-dxl'  WMIN     = '1.01E-05-dxw' WMAX     = 0.000101
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.4690217+dvthn' LVTH0    = 1.320675E-08   WVTH0    = 1.03913E-07
+PVTH0   = -9.346779E-14  K1       = 0.5348862      LK1      = 7.746888E-09
+WK1     = -3.099871E-08  PK1      = -1.512218E-13  K2       = 0.005167292
+LK2     = -3.877456E-09  WK2      = -3.134034E-09  PK2      = 5.643159E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 85657.14       LVSAT    = -0.0007622857
+UA      = -4.439753E-10  LUA      = -1.489168E-16  WUA      = -5.953859E-15
+PUA     = 2.303602E-21   UB       = 2.349393E-18   LUB      = 4.554895E-25
+WUB     = 6.663095E-24   PUB      = -6.163771E-30  UC       = 9.496897E-11
+LUC     = 6.005324E-17   WUC      = 5.22306E-16    PUC      = -7.024722E-22
+RDSW    = 170            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.04780528     LU0      = 1.374896E-09
+WU0     = -4.015433E-08  PU0      = -3.380197E-15  A0       = 0.1270388
+LA0     = 4.67235E-08    WA0      = -4.21675E-06   PA0      = 4.147783E-12
+KETA    = -0.02483604    LKETA    = -5.621754E-09  WKETA    = 8.9844E-08
+PKETA   = -3.369537E-14  A1       = 0              A2       = 0.99
+AGS     = 0.017056       LAGS     = 3.41504E-09    WAGS     = 2.946355E-07
+PAGS    = -3.417772E-13  B0       = 0              B1       = 0
+VOFF    = -0.1517648     LVOFF    = 7.107172E-09   WVOFF    = -1.044416E-07
+PVOFF   = 8.700798E-14   NFACTOR  = 1              CIT      = -0.0001578858
+LCIT    = 3.026274E-10   CDSC     = 0              CDSCB    = 0
+CDSCD   = 0              ETA0     = 1.714285E-05   LETA0    = 3.811429E-11
+ETAB    = -1.714285E-05  LETAB    = -3.811429E-11  DSUB     = 0
+PCLM    = 0.8685714      LPCLM    = 1.524572E-07   PDIBLC1  = 1E-06
+PDIBLC2 = 0.001685714    LPDIBLC2 = 1.524571E-09   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 4E+08          PSCBE2   = 1E-06
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 0.448150714
+BETA0   = 11.59263       KT1      = -0.223624      LKT1     = 9.677446E-09
+WKT1    = -5.442481E-08  PKT1     = -3.925055E-14  KT2      = -0.02933674
+LKT2    = 4.634833E-09   WKT2     = -2.291865E-08  PKT2     = -3.102267E-14
+AT      = 20000          UTE      = -1.638485      LUTE     = 8.074134E-08
+WUTE    = 2.907924E-06   PUTE     = -3.503216E-12  UA1      = 1.223706E-09
+LUA1    = 3.415059E-19   WUA1     = 2.946371E-17   PUA1     = -3.417791E-23
+UB1     = -1.198842E-18  LUB1     = 2.932454E-25   WUB1     = 1.123821E-23
+PUB1    = -1.507463E-29  UC1      = 1.573038E-11   LUC1     = 1.600793E-17
+WUC1    = 5.277456E-16   PUC1     = -8.197604E-22  KT1L     = 0
+PRT     = 0              CJ       = cjn            PB       = 0.6882682
+MJ      = 0.3595262      CJSW     = cjswn          PBSW     = 0.6882682
+MJSW    = 0.2003879      CJSWG    = cjswgn         PBSWG    = 0.6882682
+MJSWG   = 0.43879        CGDO     = cgon           CGSO     = cgon
+TCJ     = 0.001040287    TCJSW    = 0.000645489    TCJSWG   = 0.000645489    TPB      = 0.001554306
+TPBSW   = 0.001554306    TPBSWG  = 0.001554306    JS       = 8.38E-06       JSW      = 1.6E-11
+XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+CALCACM  = 1
+ALPHA0   = 0              DLC      = 3E-9
+LLC     = -0.039        )


.MODEL nch.3            NMOS   (                    LMIN     = 1.8E-07
+LMAX    = '5E-07-dxl'    WMIN     = '1.01E-05-dxw' WMAX     = 0.000101
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.4889706+dvthn' LVTH0    = 4.03025E-09    WVTH0    = -1.385044E-07
+PVTH0   = 1.804418E-14   K1       = 0.4620976      LK1      = 4.122966E-08
+WK1     = -5.300568E-07  PK1      = 7.834502E-14   K2       = 0.04110285
+LK2     = -2.040781E-08  WK2      = 1.839435E-07   PK2      = -2.962406E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 84437.5        LVSAT    = -0.00020125
+UA      = -7.610477E-10  LUA      = -3.063457E-18  WUA      = -9.912273E-16
+PUA     = 2.079115E-23   UB       = 2.63488E-18    LUB      = 3.241653E-25
+WUB     = 2.452493E-25   PUB      = -3.211562E-30  UC       = 1.317473E-10
+LUC     = 4.313522E-17   WUC      = -1.501932E-16  PUC      = -3.931226E-22
+RDSW    = 170            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.04633423     LU0      = 2.051578E-09
+WU0     = -2.998386E-08  PU0      = -8.05861E-15   A0       = 0.4302041
+LA0     = -9.273254E-08  WA0      = 1.113129E-06   PA0      = 1.696039E-12
+KETA    = -0.03103998    LKETA    = -2.76794E-09   WKETA    = -1.089419E-07
+PKETA   = 5.774615E-14   A1       = 0              A2       = 0.99
+AGS     = 0.04393999     LAGS     = -8.951599E-09  WAGS     = -6.445151E-07
+PAGS    = 9.023213E-14   B0       = 0              B1       = 0
+VOFF    = -0.1400894     LVOFF    = 1.736505E-09   WVOFF    = 1.566271E-07
+PVOFF   = -3.308362E-14  NFACTOR  = 1              CIT      = 0.0002665949
+LCIT    = 1.073664E-10   WCIT     = 5.374534E-11   PCIT     = -2.47229E-17
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -0.00029375    LETA0    = 1.81125E-10    ETAB     = 0.0013875
+LETAB   = -6.8425E-10    DSUB     = 0              PCLM     = 1.097804
+LPCLM   = 4.701011E-08   WPCLM    = 9.902701E-08   PPCLM    = -4.555247E-14
+PDIBLC1 = 1E-06          PDIBLC2  = -0.005937497   LPDIBLC2 = 5.03125E-09
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 4E+08
+PSCBE2  = 1E-06          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 0.448150714    BETA0    = 11.59263       KT1      = -0.2023527
+LKT1    = -1.073793E-10  WKT1     = -2.499313E-07  PKT1     = 5.068245E-14
+KT2     = -0.01509771    LKT2     = -1.915123E-09  WKT2     = -1.455392E-07
+PKT2    = 2.53828E-14    AT       = 20004.7        LAT      = -2.163157E-06
+WAT     = -4.740137E-05  PAT      = 2.180463E-11   UTE      = -1.46527
+LUTE    = 1.062595E-09   WUTE     = -6.227977E-06  PUTE     = 6.992989E-13
+UA1     = 1.224644E-09   LUA1     = -9.016052E-20  WUA1     = -6.445188E-17
+PUA1    = 9.023264E-24   UB1      = -8.07023E-19   LUB1     = 1.130082E-25
+WUB1    = -2.744663E-23  PUB1     = 2.720394E-30   UC1      = 9.072359E-12
+LUC1    = 1.907063E-17   WUC1     = -1.485916E-15  PUC1     = 1.065238E-22
+KT1L    = 0              PRT      = 0              CJ       = cjn
+PB      = 0.6882682      MJ       = 0.3595262      CJSW     = cjswn
+PBSW    = 0.6882682      MJSW     = 0.2003879      CJSWG    = cjswgn
+PBSWG   = 0.6882682      MJSWG    = 0.43879        CGDO     = cgon
+CGSO    = cgon           TCJ      = 0.001040287    TCJSW    = 0.000645489    TCJSWG   = 0.000645489
+TPB     = 0.001554306    TPBSW    = 0.001554306    TPBSWG   = 0.001554306    JS       = 8.38E-06
+JSW     = 1.6E-11        XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0
+CALCACM = 1              ALPHA0   = 0
+DLC     = 3E-9           LLC      = -0.039        )


.MODEL nch.4            NMOS   (                    LMIN     = '1.2E-06-dxl'
+LMAX    = 2.1E-05        WMIN     = '1.3E-06-dxw'  WMAX     = '1.01E-05-dxw'
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.4303551+dvthn' LVTH0    = 6.063544E-08   WVTH0    = 1.151582E-09
+PVTH0   = -2.252282E-16  K1       = 0.5079118      LK1      = 1.708006E-08
+WK1     = 4.811752E-08   PK1      = -2.166895E-14  K2       = 0.01749582
+LK2     = -1.215701E-08  WK2      = -1.579011E-08  PK2      = 1.041545E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 90678.27       LVSAT    = -0.006755514
+WVSAT   = -0.0001932689  PVSAT    = 1.924963E-09   UA       = -5.334703E-10
+LUA     = -5.097949E-16  WUA      = -3.212069E-16  PUA      = 4.538242E-22
+UB      = 2.252485E-18   LUB      = 7.926502E-25   WUB      = -1.295807E-25
+PUB     = -5.497242E-31  UC       = 1.065297E-10   LUC      = 3.988117E-17
+WUC     = -1.679473E-17  PUC      = -8.958444E-24  RDSW     = 170
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.04281001     LU0      = 3.050399E-09   WU0      = -9.352497E-09
+PU0     = 2.409294E-15   A0       = 0.4075408      LA0      = -3.610417E-07
+WA0     = -2.355343E-08  PA0      = 1.140953E-13   KETA     = 0.01500895
+LKETA   = -4.536782E-08  WKETA    = -1.404518E-08  PKETA    = 2.155698E-14
+A1      = 0              A2       = 0.99           AGS      = 0.02
+B0      = 0              B1       = 0              VOFF     = -0.1395841
+LVOFF   = -1.091341E-08  WVOFF    = 5.73079E-10    PVOFF    = 4.41203E-15
+NFACTOR = 1              CIT      = -0.0001267591  LCIT     = 2.665205E-10
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 5E-05          ETAB     = -5E-05         DSUB     = 0
+PCLM    = 0.7755538      LPCLM    = 2.434849E-07   WPCLM    = -1.932694E-08
+PPCLM   = 1.924964E-13   PDIBLC1  = 1E-06          PDIBLC2  = 0.0003968181
+LPDIBLC2= 3.019691E-09   PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 1.736364E+08   LPSCBE1  = 262.5818       PSCBE2   = 1E-06
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 0.448150714
+BETA0   = 11.59263       KT1      = -0.2231153     LKT1     = -3.905888E-10
+WKT1    = -9.296202E-09  PKT1     = 3.937134E-15   KT2      = -0.03050068
+LKT2    = 4.543159E-10   WKT2     = 2.345302E-09   PKT2     = -4.579503E-15
+AT      = 20000          UTE      = -1.580575      LUTE     = 5.729051E-09
+WUTE    = 5.798076E-09   PUTE     = -5.774884E-14  UA1      = 1.224E-09
+UB1     = -1.059435E-18  LUB1     = -4.518781E-26  WUB1     = -6.141879E-25
+PUB1    = 4.554933E-31   UC1      = 2.59445E-11    LUC1     = -7.81201E-18
+WUC1    = -1.427992E-16  PUC1     = 7.874507E-23   KT1L     = 0
+PRT     = 0              CJ       = cjn            PB       = 0.6882682
+MJ      = 0.3595262      CJSW     = cjswn          PBSW     = 0.6882682
+MJSW    = 0.2003879      CJSWG    = cjswgn         PBSWG    = 0.6882682
+MJSWG   = 0.43879        CGDO     = cgon           CGSO     = cgon
+TCJ     = 0.001040287    TCJSW    = 0.000645489    TCJSWG   = 0.000645489    TPB      = 0.001554306
+TPBSW   = 0.001554306    TPBSWG  = 0.001554306    JS       = 8.38E-06       JSW      = 1.6E-11
+XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+CALCACM  = 1
+ALPHA0   = 0              DLC     = 3E-9
+LLC     = -0.039        )


.MODEL nch.5            NMOS   (                    LMIN     = '5E-07-dxl'
+LMAX    = '1.2E-06-dxl'  WMIN     = '1.3E-06-dxw'  WMAX     = '1.01E-05-dxw'
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.4799766+dvthn' LVTH0    = 3.074509E-09   WVTH0    = -6.512545E-09
+PVTH0   = 8.665152E-15   K1       = 0.5324208      LK1      = -1.135038E-08
+WK1     = -6.147623E-09  PK1      = 4.127862E-14   K2       = 0.004003276
+LK2     = 3.494347E-09   WK2      = 8.599232E-09   PK2      = -1.787618E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 85511.69       LVSAT    = -0.0007622857
+WVSAT   = 0.001466182    UA       = -1.023122E-09  LUA      = 5.820092E-17
+WUA     = -1.160614E-16  PUA      = 2.158555E-22   UB       = 3.043298E-18
+LUB     = -1.246927E-25  WUB      = -3.314691E-25  PUB      = -3.155337E-31
+UC      = 1.463423E-10   LUC      = -6.301452E-18  WUC      = 4.462591E-18
+PUC     = -3.361694E-23  RDSW     = 170            PRWB     = 0
+PRWG    = 0              WR       = 1              U0       = 0.04463334
+LU0     = 9.35341E-10    WU0      = -8.181137E-09  PU0      = 1.050515E-15
+A0      = -0.3045075     LA0      = 4.649343E-07   WA0      = 1.332365E-07
+PA0     = -6.778103E-14  KETA     = -0.01546816    LKETA    = -1.001437E-08
+WKETA   = -4.584175E-09  PKETA    = 1.058221E-14   A1       = 0
+A2      = 0.99           AGS      = 0.05010909     LAGS     = -3.492654E-08
+WAGS    = -3.853963E-08  PAGS     = 4.470598E-14   B0       = 0
+B1      = 0              VOFF     = -0.1628752     LVOFF    = 1.610426E-08
+WVOFF   = 7.551262E-09   PVOFF    = -3.68266E-15   NFACTOR  = 1
+CIT     = -0.0001578858  LCIT     = 3.026274E-10   CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = 1.714286E-05
+LETA0   = 3.811428E-11   ETAB     = -1.714286E-05  LETAB    = -3.811428E-11
+DSUB    = 0              PCLM     = 0.8540259      LPCLM    = 1.524572E-07
+WPCLM   = 1.466183E-07   PDIBLC1  = 1E-06          PDIBLC2  = 0.001781299
+LPDIBLC2= 1.413693E-09   WPDIBLC2 = -9.634911E-10  PPDIBLC2 = 1.11765E-15
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 4E+08
+PSCBE2  = 1E-06          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 0.448150714    BETA0    = 11.59263       KT1      = -0.2285168
+LKT1    = 5.875238E-09   WKT1     = -5.105314E-09  PKT1     = -9.242955E-16
+KT2     = -0.03146011    LKT2     = 1.567252E-09   WKT2     = -1.515083E-09
+PKT2    = -1.014558E-16  AT       = 20000          UTE      = -1.303027
+LUTE    = -3.162274E-07  WUTE     = -4.734936E-07  PUTE     = 4.982295E-13
+UA1     = 1.227011E-09   LUA1     = -3.492674E-18  WUA1     = -3.853985E-18
+PUA1    = 4.470623E-24   UB1      = 9.605878E-20   LUB1     = -1.385561E-24
+WUB1    = -1.814396E-24  PUB1     = 1.847735E-30   UC1      = 8.797449E-11
+LUC1    = -7.976681E-17  WUC1     = -2.004749E-16  PUC1     = 1.456489E-22
+KT1L    = 0              PRT      = 0              CJ       = cjn
+PB      = 0.6882682      MJ       = 0.3595262      CJSW     = cjswn
+PBSW    = 0.6882682      MJSW     = 0.2003879      CJSWG    = cjswgn
+PBSWG   = 0.6882682      MJSWG    = 0.43879        CGDO     = cgon
+CGSO    = cgon           TCJ      = 0.001040287    TCJSW    = 0.000645489    TCJSWG   = 0.000645489
+TPB     = 0.001554306    TPBSW    = 0.001554306    TPBSWG   = 0.001554306    JS       = 8.38E-06
+JSW     = 1.6E-11        XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0
+CALCACM = 1              ALPHA0   = 0
+DLC     = 3E-9           LLC     = -0.039         )


.MODEL nch.6            NMOS   (                    LMIN     = 1.8E-07
+LMAX    = '5E-07-dxl'    WMIN     = '1.3E-06-dxw'  WMAX     = '1.01E-05-dxw'
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.4751247+dvthn' LVTH0    = 5.306376E-09   WVTH0    = 1.062077E-09
+PVTH0   = 5.180826E-15   K1       = 0.3998241      LK1      = 4.964413E-08
+WK1     = 9.765969E-08   PK1      = -6.472741E-15  K2       = 0.06352166
+LK2     = -2.388411E-08  WK2      = -4.203799E-08  PK2      = 5.416945E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 84292.05       LVSAT    = -0.00020125
+WVSAT   = 0.001466182    UA       = -9.057631E-10  LUA      = 4.215886E-18
+WUA     = 4.675041E-16   PUA      = -5.258461E-23  UB       = 2.760486E-18
+LUB     = 5.400765E-27   WUB      = -1.020856E-24  PUB      = 1.584294E-33
+UC      = 1.234253E-10   LUC      = 4.240396E-18   WUC      = -6.630735E-17
+PUC     = -1.06277E-24   RDSW     = 170            PRWB     = 0
+PRWG    = 0              WR       = 1              U0       = 0.04387662
+LU0     = 1.283432E-09   WU0      = -5.211112E-09  PU0      = -3.156964E-16
+A0      = 0.5262759      LA0      = 8.277392E-08   WA0      = 1.447255E-07
+PA0     = -7.306591E-14  KETA     = -0.04428695    LKETA    = 3.242273E-09
+WKETA   = 2.458758E-08   PKETA    = -2.8368E-15    A1       = 0
+A2      = 0.99           AGS      = -0.02836364    LAGS     = 1.170909E-09
+WAGS    = 8.430546E-08   PAGS     = -1.180276E-14  B0       = 0
+B1      = 0              VOFF     = -0.1246745     LVOFF    = -1.468027E-09
+WVOFF   = 1.245329E-09   PVOFF    = -7.81931E-16   NFACTOR  = 1
+CIT     = 0.0002756616   LCIT     = 1.031957E-10   WCIT     = -3.764672E-11
+PCIT    = 1.731749E-17   CDSC     = 0              CDSCB    = 0
+CDSCD   = 0              ETA0     = -0.00029375    LETA0    = 1.81125E-10
+ETAB    = 0.0013875      LETAB    = -6.8425E-10    DSUB     = 0
+PCLM    = 1.102557       LPCLM    = 3.813286E-08   WPCLM    = 5.111752E-08
+PPCLM   = 4.393024E-14   PDIBLC1  = 1E-06          PDIBLC2  = -0.006146589
+LPDIBLC2= 5.060522E-09   WPDIBLC2 = 2.107634E-09   PPDIBLC2 = -2.950686E-16
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 4E+08
+PSCBE2  = 1E-06          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 0.448150714    BETA0    = 11.59263       KT1      = -0.2268918
+LKT1    = 5.127722E-09   WKT1     = -2.576878E-09  PKT1     = -2.087376E-15
+KT2     = -0.02937242    LKT2     = 6.06917E-10    WKT2     = -1.65007E-09
+PKT2    = -3.93619E-17   AT       = 20000          UTE      = -2.172423
+LUTE    = 8.369503E-08   WUTE     = 9.001274E-07   PUTE     = -1.336361E-13
+UA1     = 1.217414E-09   LUA1     = 9.220962E-19   WUA1     = 8.430593E-18
+PUA1    = -1.180283E-24  UB1      = -3.852224E-18  LUB1     = 4.306491E-25
+WUB1    = 3.248998E-24   PUB1     = -4.814262E-31  UC1      = -1.568814E-10
+LUC1    = 3.286692E-17   WUC1     = 1.868985E-16   PUC1     = -3.254285E-23
+KT1L    = 0              PRT      = 0              CJ       = cjn
+PB      = 0.6882682      MJ       = 0.3595262      CJSW     = cjswn
+PBSW    = 0.6882682      MJSW     = 0.2003879      CJSWG    = cjswgn
+PBSWG   = 0.6882682      MJSWG    = 0.43879        CGDO     = cgon
+CGSO    = cgon           TCJ      = 0.001040287    TCJSW    = 0.000645489    TCJSWG   = 0.000645489
+TPB     = 0.001554306    TPBSW    = 0.001554306    TPBSWG   = 0.001554306    JS       = 8.38E-06
+JSW     = 1.6E-11        XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0
+CALCACM = 1              ALPHA0   = 0
+DLC     = 3E-9           LLC     = -0.039         )


.MODEL nch.7            NMOS   (                    LMIN     = '1.2E-06-dxl'
+LMAX    = 2.1E-05        WMIN     = '6E-07-dxw'    WMAX     = '1.3E-06-dxw'
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.4337114+dvthn' LVTH0    = 6.675699E-08   WVTH0    = -3.144492E-09
+PVTH0   = -8.060817E-15  K1       = 0.5648248      LK1      = 2.192964E-08
+WK1     = -2.47311E-08   PK1      = -2.787642E-14  K2       = -0.0002770806
+LK2     = -9.479984E-09  WK2      = 6.959211E-09   PK2      = 6.988862E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 90636.49       LVSAT    = -0.006339475
+WVSAT   = -0.0001398028  PVSAT    = 1.392434E-09   UA       = -9.356199E-10
+LUA     = -2.007095E-16  WUA      = 1.935446E-16   PUA      = 5.819503E-23
+UB      = 2.352719E-18   LUB      = 3.53453E-25    WUB      = -2.578803E-25
+PUB     = 1.244829E-32   UC       = 1.089601E-10   LUC      = 3.56231E-17
+WUC     = -1.990555E-17  PUC      = -3.508111E-24  RDSW     = 170
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.03490788     LU0      = 2.751226E-09   WU0      = 7.622277E-10
+PU0     = 2.792237E-15   A0       = 0.2937173      LA0      = -1.629362E-07
+WA0     = 1.221407E-07   PA0      = -1.394798E-13  KETA     = 0.003630752
+LKETA   = -2.766508E-08  WKETA    = 5.189081E-10   PKETA    = -1.102526E-15
+A1      = 0              A2       = 0.99           AGS      = 0.02
+B0      = 0              B1       = 0              VOFF     = -0.1393593
+LVOFF   = -1.120061E-09  WVOFF    = 2.853291E-10   PVOFF    = -8.123458E-15
+NFACTOR = 1              CIT      = -0.0001267591  LCIT     = 2.665205E-10
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 5E-05          ETAB     = -5E-05         DSUB     = 0
+PCLM    = 0.7713767      LPCLM    = 2.850888E-07   WPCLM    = -1.398026E-08
+PPCLM   = 1.392434E-13   PDIBLC1  = 1E-06          PDIBLC2  = 0.0003968183
+LPDIBLC2= 3.019691E-09   PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 1.736364E+08   LPSCBE1  = 262.5818       PSCBE2   = 1E-06
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 0.448150714
+BETA0   = 11.59263       KT1      = -0.2294805     LKT1     = -6.668915E-09
+WKT1    = -1.148684E-09  PKT1     = 1.197339E-14   KT2      = -0.02756653
+LKT2    = -3.983356E-09  WKT2     = -1.410404E-09  PKT2     = 1.100718E-15
+AT      = 20000          UTE      = -1.612465      LUTE     = -6.751966E-09
+WUTE    = 4.661704E-08   PUTE     = -4.177314E-14  UA1      = 1.224E-09
+UB1     = -1.546692E-18  LUB1     = 3.371048E-25   WUB1     = 9.500769E-27
+PUB1    = -3.38413E-32   UC1      = -7.376004E-11  LUC1     = 4.105292E-17
+WUC1    = -1.517736E-17  PUC1     = 1.619797E-23   KT1L     = 0
+PRT     = 0              CJ       = cjn            PB       = 0.6882682
+MJ      = 0.3595262      CJSW     = cjswn          PBSW     = 0.6882682
+MJSW    = 0.2003879      CJSWG    = cjswgn         PBSWG    = 0.6882682
+MJSWG   = 0.43879        CGDO     = cgon           CGSO     = cgon
+TCJ     = 0.001040287    TCJSW    = 0.000645489    TCJSWG   = 0.000645489    TPB      = 0.001554306
+TPBSW   = 0.001554306    TPBSWG  = 0.001554306    JS       = 8.38E-06       JSW      = 1.6E-11
+XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+CALCACM  = 1
+ALPHA0   = 0              DLC      = 3E-9
+LLC     = -0.039        )


.MODEL nch.8            NMOS   (                    LMIN     = '5E-07-dxl'
+LMAX    = '1.2E-06-dxl'  WMIN     = '6E-07-dxw'    WMAX     = '1.3E-06-dxw'
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.4808935+dvthn' LVTH0    = 1.202573E-08   WVTH0    = -7.686219E-09
+PVTH0   = -2.792416E-15  K1       = 0.5770396      LK1      = 7.760477E-09
+WK1     = -6.325968E-08  PK1      = 1.681673E-14   K2       = -0.005123796
+LK2     = -3.857791E-09  WK2      = 2.028189E-08   PK2      = -8.465442E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 85828.57       LVSAT    = -0.0007622857
+WVSAT   = 0.001060571    UA       = -1.424596E-09  LUA      = 3.665024E-16
+WUA     = 3.978251E-16   PUA      = -1.787704E-22  UB       = 3.028664E-18
+LUB     = -4.306433E-25  WUB      = -3.127378E-25  PUB      = 7.608303E-32
+UC      = 1.63363E-10    LUC      = -2.748434E-17  WUC      = -1.732388E-17
+PUC     = -6.502839E-24  RDSW     = 170            PRWB     = 0
+PRWG    = 0              WR       = 1              U0       = 0.03449604
+LU0     = 3.228961E-09   WU0      = 4.794603E-09   PU0      = -1.885319E-15
+A0      = -0.2092096     LA0      = 4.20459E-07    WA0      = 1.12553E-08
+PA0     = -1.085273E-14  KETA     = -0.01817785    LKETA    = -2.367101E-09
+WKETA   = -1.115772E-09  PKETA    = 7.937026E-16   A1       = 0
+A2      = 0.99           AGS      = 0.02           B0       = 0
+B1      = 0              VOFF     = -0.1488233     LVOFF    = 9.858188E-09
+WVOFF   = -1.043516E-08  PVOFF    = 4.31231E-15    NFACTOR  = 1
+CIT     = -0.0001578858  LCIT     = 3.026274E-10   CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = 1.714285E-05
+LETA0   = 3.811429E-11   ETAB     = -1.714285E-05  LETAB    = -3.811429E-11
+DSUB    = 0              PCLM     = 0.9401633      LPCLM    = 8.929624E-08
+WPCLM   = 3.636246E-08   PPCLM    = 8.084588E-14   PDIBLC1  = 1E-06
+PDIBLC2 = 0.001028572    LPDIBLC2 = 2.286857E-09   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 4E+08          PSCBE2   = 1E-06
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 0.448150714
+BETA0   = 11.59263       KT1      = -0.2414929     LKT1     = 7.265427E-09
+WKT1    = 1.150402E-08   PKT1     = -2.703738E-15  KT2      = -0.03334108
+LKT2    = 2.715118E-09   WKT2     = 8.925629E-10   PKT2     = -1.570723E-15
+AT      = 20000          UTE      = -1.86406       LUTE     = 2.85098E-07
+WUTE    = 2.44629E-07    PUTE     = -2.71467E-13   UA1      = 1.224E-09
+UB1     = -1.864369E-18  LUB1     = 7.05611E-25    WUB1     = 6.949518E-25
+PUB1    = -8.289646E-31  UC1      = -1.092616E-10  LUC1     = 8.223476E-17
+WUC1    = 5.198735E-17   PUC1     = -6.171309E-23  KT1L     = 0
+PRT     = 0              CJ       = cjn            PB       = 0.6882682
+MJ      = 0.3595262      CJSW     = cjswn          PBSW     = 0.6882682
+MJSW    = 0.2003879      CJSWG    = cjswgn         PBSWG    = 0.6882682
+MJSWG   = 0.43879        CGDO     = cgon           CGSO     = cgon
+TCJ     = 0.001040287    TCJSW    = 0.000645489    TCJSWG   = 0.000645489    TPB      = 0.001554306
+TPBSW   = 0.001554306    TPBSWG  = 0.001554306    JS       = 8.38E-06       JSW      = 1.6E-11
+XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+CALCACM  = 1
+ALPHA0   = 0              DLC      = 3E-9
+LLC     = -0.039        )


.MODEL nch.9            NMOS   (                    LMIN     = 1.8E-07
+LMAX    = '5E-07-dxl'    WMIN     = '6E-07-dxw'    WMAX     = '1.3E-06-dxw'
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.481488+dvthn' LVTH0    = 1.17523E-08    WVTH0    = -7.082873E-09
+PVTH0   = -3.069955E-15  K1       = 0.4891953      LK1      = 4.816888E-08
+WK1     = -1.673544E-08  PK1      = -4.58442E-15   K2       = 0.0302083
+LK2     = -2.011056E-08  WK2      = 6.031026E-10   PK2      = 5.867986E-16
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 84637.98       LVSAT    = -0.0002146133
+WVSAT   = 0.001023387    PVSAT    = 1.710496E-11   UA       = -5.066291E-10
+LUA     = -5.57622E-17   WUA      = -4.338739E-17  PUA      = 2.418733E-23
+UB      = 1.984037E-18   LUB      = 4.988523E-26   WUB      = -2.700116E-26
+PUB     = -5.535582E-32  UC       = 7.191223E-11   LUC      = 1.458302E-17
+WUC     = -3.706532E-19  PUC      = -1.430133E-23  RDSW     = 170
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.04022617     LU0      = 5.931013E-10   WU0      = -5.385397E-10
+PU0     = 5.679271E-16   A0       = 0.5373152      LA0      = 7.705761E-08
+WA0     = 1.305951E-07   PA0      = -6.574904E-14  KETA     = -0.02712423
+LKETA   = 1.748234E-09   WKETA    = 2.6193E-09     PKETA    = -9.244303E-16
+A1      = 0              A2       = 0.99           AGS      = 0.03866202
+LAGS    = -8.58453E-09   WAGS     = -1.487385E-09  PAGS     = 6.841983E-16
+B0      = 0              B1       = 0              VOFF     = -0.1276647
+LVOFF   = 1.252623E-10   WVOFF    = 5.072778E-09   PVOFF    = -2.821342E-15
+NFACTOR = 1              CIT      = 0.0002127283   LCIT     = 1.32145E-10
+WCIT    = 4.290785E-11   PCIT     = -1.973761E-17  CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = -0.0003198954
+LETA0   = 1.931519E-10   WETA0    = 3.346616E-11   PETA0    = -1.539446E-17
+ETAB    = 0.001419582    LETAB    = -6.990077E-10  WETAB    = -4.106481E-11
+PETAB   = 1.888986E-17   DSUB     = 0              PCLM     = 0.9740778
+LPCLM   = 7.369557E-08   WPCLM    = 2.155709E-07   PPCLM    = -1.590029E-15
+PDIBLC1 = 1E-06          PDIBLC2  = -0.003529964   LPDIBLC2 = 4.383784E-09
+WPDIBLC2= -1.241645E-09  PPDIBLC2 = 5.711567E-16   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 4E+08          PSCBE2   = 1E-06
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 0.448150714
+BETA0   = 11.59263       KT1      = -0.2299624     LKT1     = 1.961425E-09
+WKT1    = 1.35353E-09    PKT1     = 1.965485E-15   KT2      = -0.02660687
+LKT2    = -3.826203E-10  WKT2     = -5.189979E-09  PKT2     = 1.227246E-15
+AT      = 20000          UTE      = -1.094227      LUTE     = -6.902506E-08
+WUTE    = -4.799637E-07  PUTE     = 6.184562E-14   UA1      = 1.224E-09
+UB1     = -5.722656E-20  LUB1     = -1.256748E-25  WUB1     = -1.608598E-24
+PUB1    = 2.306684E-31   UC1      = 1.072241E-10   LUC1     = -1.734869E-17
+WUC1    = -1.511566E-16  PUC1     = 3.173314E-23   KT1L     = 0
+PRT     = 0              CJ       = cjn            PB       = 0.6882682
+MJ      = 0.3595262      CJSW     = cjswn          PBSW     = 0.6882682
+MJSW    = 0.2003879      CJSWG    = cjswgn         PBSWG    = 0.6882682
+MJSWG   = 0.43879        CGDO     = cgon           CGSO     = cgon
+TCJ     = 0.001040287    TCJSW    = 0.000645489    TCJSWG   = 0.000645489    TPB      = 0.001554306
+TPBSW   = 0.001554306    TPBSWG  = 0.001554306    JS       = 8.38E-06       JSW      = 1.6E-11
+XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+CALCACM  = 1
+ALPHA0   = 0              DLC      = 3E-9
+LLC     = -0.039        )


.MODEL nch.10           NMOS   (                    LMIN     = '1.2E-06-dxl'
+LMAX    = 2.1E-05        WMIN     = 2.2E-07        WMAX     = '6E-07-dxw'
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.4352488+dvthn' LVTH0    = 5.971231E-08   WVTH0    = -4.036178E-09
+PVTH0   = -3.974899E-15  K1       = 0.5279656      LK1      = -6.041289E-08
+WK1     = -3.352767E-09  PK1      = 1.988225E-14   K2       = 0.01424122
+LK2     = 1.937711E-08   WK2      = -1.461409E-09  PK2      = -9.748253E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 90518.48       LVSAT    = -0.005164109
+WVSAT   = -7.135755E-05  PVSAT    = 7.107215E-10   UA       = -5.753777E-10
+LUA     = -1.265512E-16  WUA      = -1.539588E-17  PUA      = 1.51832E-23
+UB      = 1.668276E-18   LUB      = 7.517433E-25   WUB      = 1.390964E-25
+PUB     = -2.185601E-31  UC       = 6.614737E-11   LUC      = 6.744323E-17
+WUC     = 4.925809E-18   PUC      = -2.196379E-23  RDSW     = 170
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.03449046     LU0      = 9.712911E-09   WU0      = 1.004335E-09
+PU0     = -1.245541E-15  A0       = 0.5242422      LA0      = -4.198011E-07
+WA0     = -1.156377E-08  PA0      = 9.501862E-15   KETA     = 0.005068241
+LKETA   = -3.031378E-08  WKETA    = -3.148353E-10  PKETA    = 4.337169E-16
+A1      = 0              A2       = 0.99           AGS      = 0.02
+B0      = 0              B1       = 0              VOFF     = -0.1357364
+LVOFF   = -1.936854E-08  WVOFF    = -1.81595E-09   PVOFF    = 2.46066E-15
+NFACTOR = 1              CIT      = -0.000126513   LCIT     = 2.640698E-10
+WCIT    = -1.427138E-13  PCIT     = 1.421443E-18   CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = 5E-05
+ETAB    = -5E-05         DSUB     = 0              PCLM     = 0.7595757
+LPCLM   = 4.026256E-07   WPCLM    = -7.135753E-09  PPCLM    = 7.107208E-14
+PDIBLC1 = 1E-06          PDIBLC2  = 0.0003968181   LPDIBLC2 = 3.019691E-09
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 1.736364E+08
+LPSCBE1 = 262.5818       PSCBE2   = 1E-06          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 0.448150714    BETA0    = 11.59263
+KT1     = -0.2400692     LKT1     = 1.973544E-08   WKT1     = 4.992732E-09
+PKT1    = -3.341133E-15  KT2      = -0.03543628    LKT2     = -3.00608E-09
+WKT2    = 3.15405E-09    PKT2     = 5.338977E-16   AT       = 20000
+UTE     = -1.574903      LUTE     = -5.076592E-08  WUTE     = 2.483101E-08
+PUTE    = -1.624505E-14  UA1      = 1.224E-09      UB1      = -1.457473E-18
+LUB1    = 2.445644E-25   WUB1     = -4.224631E-26  PUB1     = 1.983214E-32
+UC1     = -7.225825E-11  LUC1     = 5.984138E-17   WUC1     = -1.60484E-17
+PUC1    = 5.300662E-24   KT1L     = 0              PRT      = 0
+CJ      = cjn            PB       = 0.6882682      MJ       = 0.3595262
+CJSW    = cjswn          PBSW     = 0.6882682      MJSW     = 0.2003879
+CJSWG   = cjswgn         PBSWG    = 0.6882682      MJSWG    = 0.43879
+CGDO    = cgon           CGSO     = cgon           TCJ      = 0.001040287
+TCJSW   = 0.000645489    TCJSWG   = 0.000645489    TPB      = 0.001554306    TPBSW    = 0.001554306    TPBSWG   = 0.001554306
+JS      = 8.38E-06       JSW      = 1.6E-11
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0
+CALCACM  = 1
+ALPHA0   = 0              DLC      = 3E-9          LLC     = -0.039             )


.MODEL nch.11           NMOS   (                    LMIN     = '5E-07-dxl'
+LMAX    = '1.2E-06-dxl'  WMIN     = 2.2E-07        WMAX     = '6E-07-dxw'
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.4879968+dvthn' LVTH0    = -1.475447E-09  WVTH0    = -1.180615E-08
+PVTH0   = 5.03827E-15    K1       = 0.4182783      LK1      = 6.682436E-08
+WK1     = 2.882188E-08   PK1      = -1.744033E-14  K2       = 0.05724643
+LK2     = -3.050892E-08  WK2      = -1.589285E-08  PK2      = 6.992215E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 86745.34       LVSAT    = -0.0007872646
+WVSAT   = 0.0005288439   PVSAT    = 1.448774E-11   UA       = -7.371595E-10
+LUA     = 6.111558E-17   WUA      = -8.878959E-19  PUA      = -1.646058E-24
+UB      = 2.570856E-18   LUB      = -2.952486E-25  WUB      = -4.720896E-26
+PUB     = -2.445921E-33  UC       = 1.484849E-10   LUC      = -2.806833E-17
+WUC     = -8.694588E-18  PUC      = -6.164128E-24  RDSW     = 170
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.04425179     LU0      = -1.610234E-09  WU0      = -8.637309E-10
+PU0     = 9.214146E-16   A0       = -0.08643652    LA0      = 2.885862E-07
+WA0     = -5.995313E-08  PA0      = 6.563351E-14   KETA     = -0.0159613
+LKETA   = -5.919509E-09  WKETA    = -2.401372E-09  PKETA    = 2.854099E-15
+A1      = 0              A2       = 0.99           AGS      = 0.02
+B0      = 0              B1       = 0              VOFF     = -0.169209
+LVOFF   = 1.945972E-08   WVOFF    = 1.388564E-09   PVOFF    = -1.256577E-15
+NFACTOR = 1              CIT      = -0.000160979   LCIT     = 3.040503E-10
+WCIT    = 1.794118E-12   PCIT     = -8.252955E-19  CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = 1.714286E-05
+LETA0   = 3.811428E-11   ETAB     = -1.714286E-05  LETAB    = -3.811428E-11
+DSUB    = 0              PCLM     = 0.9751641      LPCLM    = 1.525431E-07
+WPCLM   = 1.606201E-08   PPCLM    = 4.416267E-14   PDIBLC1  = 1E-06
+PDIBLC2 = 0.001663438    LPDIBLC2 = 1.550412E-09   WPDIBLC2 = -3.682228E-10
+PPDIBLC2= 4.271384E-16   PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 4E+08          PSCBE2   = 1E-06          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 0.448150714    BETA0    = 11.59263
+KT1     = -0.2410275     LKT1     = 2.084706E-08   WKT1     = 1.123407E-08
+PKT1    = -1.058109E-14  KT2      = -0.04000202    LKT2     = 2.290172E-09
+WKT2    = 4.755906E-09   PKT2     = -1.324255E-15  AT       = 20000
+UTE     = -1.473219      LUTE     = -1.687192E-07  WUTE     = 1.794131E-08
+PUTE    = -8.253005E-15  UA1      = 1.224E-09      UB1      = -5.006146E-19
+LUB1    = -8.653909E-25  WUB1     = -9.602595E-26  PUB1     = 8.221649E-32
+UC1     = 4.363964E-11   LUC1     = -7.460019E-17  WUC1     = -3.669539E-17
+PUC1    = 2.925118E-23   KT1L     = 0              PRT      = 0
+CJ      = cjn            PB       = 0.6882682      MJ       = 0.3595262
+CJSW    = cjswn          PBSW     = 0.6882682      MJSW     = 0.2003879
+CJSWG   = cjswgn         PBSWG    = 0.6882682      MJSWG    = 0.43879
+CGDO    = cgon           CGSO     = cgon           TCJ      = 0.001040287
+TCJSW   = 0.000645489    TCJSWG   = 0.000645489    TPB      = 0.001554306    TPBSW    = 0.001554306    TPBSWG   = 0.001554306
+JS      = 8.38E-06       JSW      = 1.6E-11
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0
+CALCACM  = 1
+ALPHA0   = 0             DLC      = 3E-9           LLC      = -0.039            )


.MODEL nch.12           NMOS   (                    LMIN     = 1.8E-07
+LMAX    = '5E-07-dxl'    WMIN     = 2.2E-07        WMAX     = '6E-07-dxw'
+NOIMOD  = 3              EF       = 0.825          AF       = 0.8256         KF       = 4.000E-29
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn           XJ       = 1.6E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.4736658+dvthn' LVTH0    = 5.116823E-09   WVTH0    = -2.546044E-09
+PVTH0   = 7.786215E-16   K1       = 0.4916317      LK1      = 3.308183E-08
+WK1     = -1.814856E-08  PK1      = 4.166068E-15   K2       = 0.0241211
+LK2     = -1.527126E-08  WK2      = 4.133682E-09   PK2      = -2.219989E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 85478.73       LVSAT    = -0.0002046202
+WVSAT   = 0.0005357541   PVSAT    = 1.130901E-11   UA       = -6.551957E-10
+LUA     = 2.341229E-17   WUA      = 4.278126E-17   PUA      = -2.173387E-23
+UB      = 2.115113E-18   LUB      = -8.560682E-26  WUB      = -1.030253E-25
+PUB     = 2.322958E-32   UC       = 1.210543E-10   LUC      = -1.545024E-17
+WUC     = -2.887305E-17  PUC      = 3.117964E-24   RDSW     = 170
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.03727462     LU0      = 1.599263E-09   WU0      = 1.173359E-09
+PU0     = -1.564659E-17  A0       = 0.3091393      LA0      = 1.066214E-07
+WA0     = 2.629372E-07   PA0      = -8.289604E-14  KETA     = -0.02983288
+LKETA   = 4.61416E-10    WKETA    = 4.190313E-09   PKETA    = -1.780756E-16
+A1      = 0              A2       = 0.99           AGS      = 0.05334493
+LAGS    = -1.533867E-08  WAGS     = -1.000348E-08  PAGS     = 4.601601E-15
+B0      = 0              B1       = 0              VOFF     = -0.1182942
+LVOFF   = -3.96108E-09   WVOFF    = -3.621182E-10  PVOFF    = -4.512629E-16
+NFACTOR = 1              CIT      = 0.0002910191   LCIT     = 9.613119E-11
+WCIT    = -2.500833E-12  PCIT     = 1.150396E-18   CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = -0.0002621952
+LETA0   = 1.666098E-10   ETAB     = 0.00134878     LETAB    = -6.66439E-10
+DSUB    = 0              PCLM     = 1.151922       LPCLM    = 7.123444E-08
+WPCLM   = 1.124212E-07   PPCLM    = -1.625715E-16  PDIBLC1  = 1E-06
+PDIBLC2 = -0.00702563    LPDIBLC2 = 5.547383E-09   WPDIBLC2 = 7.858404E-10
+PPDIBLC2= -1.037308E-16  PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 4E+08          PSCBE2   = 1E-06          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 0.448150714    BETA0    = 11.59263
+KT1     = -0.1956458     LKT1     = -2.850022E-11  WKT1     = -1.855012E-08
+PKT1    = 3.119642E-15   KT2      = -0.03908098    LKT2     = 1.866495E-09
+WKT2    = 2.045007E-09   PKT2     = -7.724148E-17  AT       = 20000
+UTE     = -1.944663      LUTE     = 4.814495E-08   WUTE     = 1.328912E-08
+PUTE    = -6.112999E-15  UA1      = 1.224E-09      UB1      = -3.081556E-18
+LUB1    = 3.21842E-25    WUB1     = 1.455128E-25   PUB1     = -2.889132E-32
+UC1     = -2.392738E-10  LUC1     = 5.554002E-17   WUC1     = 4.98122E-17
+PUC1    = -1.054232E-23  KT1L     = 0              PRT      = 0
+CJ      = cjn            PB       = 0.6882682      MJ       = 0.3595262
+CJSW    = cjswn          PBSW     = 0.6882682      MJSW     = 0.2003879
+CJSWG   = cjswgn         PBSWG    = 0.6882682      MJSWG    = 0.43879
+CGDO    = cgon           CGSO     = cgon           TCJ      = 0.001040287
+TCJSW   = 0.000645489    TCJSWG   = 0.000645489    TPB      = 0.001554306    TPBSW    = 0.001554306    TPBSWG   = 0.001554306
+JS      = 8.38E-06       JSW      = 1.6E-11
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0
+CALCACM  = 1
+ALPHA0   = 0             DLC      = 3E-9           LLC     = -0.039         )


.MODEL pch.1            PMOS   (                    LMIN     = '1.2E-06-dxl'
+LMAX    = 2.1E-05        WMIN     = '1.01E-05-dxw' WMAX     = 0.000101
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.4379811+dvthp' LVTH0    = -2.157551E-08  WVTH0    = 1.993098E-08
+PVTH0   = -3.253912E-14  K1       = 0.5232846      LK1      = 1.902614E-08
+WK1     = 1.2434E-07     PK1      = -2.513947E-15  K2       = 0.03910666
+LK2     = -5.042024E-09  WK2      = -3.541453E-08  PK2      = -4.457568E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 151306.8       LVSAT    = -0.01300284
+UA      = 8.542461E-10   LUA      = -4.102831E-17  WUA      = 8.143675E-17
+PUA     = -3.518285E-21  UB       = 5.261967E-19   LUB      = -6.282183E-26
+WUB     = 1.155279E-24   PUB      = 5.160992E-30   UC       = -9.947074E-11
+LUC     = -1.021336E-17  WUC      = 1.107944E-16   PUC      = 3.027899E-22
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01091231     LU0      = -1.271836E-09
+WU0     = 8.47784E-10    PU0      = -2.243951E-16  A0       = 0.9876606
+LA0     = 1.192363E-07   WA0      = 5.132671E-07   PA0      = -4.412657E-13
+KETA    = 0.02612185     LKETA    = -1.707487E-09  WKETA    = 7.135232E-09
+PKETA   = -3.335716E-15  A1       = 0              A2       = 0.4
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1293096     LVOFF    = -7.007391E-10  WVOFF    = 1.923288E-08
+PVOFF   = -1.21129E-14   NFACTOR  = 1              CIT      = -0.0001
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 5E-05          ETAB     = -5E-05         DSUB     = 0
+PCLM    = 0.5738637      LPCLM    = 2.600568E-07   PDIBLC1  = 1E-06
+PDIBLC2 = 0.000477273    LPDIBLC2 = 5.201136E-09   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 1.803977E+08   LPSCBE1  = 195.0426
+PSCBE2  = 5E-07          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 6.8730453846   BETA0    = 22.67827       KT1      = -0.2295955
+LKT1    = -1.534336E-08  KT2      = -0.02403249    LKT2     = -3.075286E-09
+AT      = 10000          UTE      = -0.8386704     LUTE     = 9.622102E-08
+UA1     = 1.224E-09      UB1      = -1.397786E-18  LUB1     = 4.807877E-26
+UC1     = -6.721975E-12  LUC1     = 2.087204E-17   KT1L     = 0
+PRT     = 0              CJ       = cjp            PB       = 0.895226
+MJ      = 0.4476         CJSW     = cjswp          PBSW     = 0.895226
+MJSW    = 0.3683619      CJSWG    = cjswgp         PBSWG    = 0.895226
+MJSWG   = 0.3683619      CGDO     = cgop           CGSO     = cgop
+TCJ     = 0.0009739001   TCJSW    = 0.0004130718   TCJSWG   = 0.0004130718   TPB      = 0.001572025
+TPBSW   = 0.001572025    TPBSWG  = 0.001572025    JS       = 4.92E-06       JSW      = 9E-10
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              DLC      = 2E-9
+LLC     = -0.039        )


.MODEL pch.2            PMOS   (                    LMIN     = '5E-07-dxl'
+LMAX    = '1.2E-06-dxl'  WMIN     = '1.01E-05-dxw' WMAX     = 0.000101
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.4469995+dvthp' LVTH0    = -1.120441E-08  WVTH0    = -4.790911E-08
+PVTH0   = 4.5477E-14     K1       = 0.5344138      LK1      = 6.227659E-09
+WK1     = 6.223506E-08   PK1      = 6.890672E-14   K2       = 0.03583825
+LK2     = -1.283352E-09  WK2      = -9.515445E-09  PK2      = -3.424151E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 146428.6       LVSAT    = -0.007392862
+UA      = 8.910204E-10   LUA      = -8.331874E-17  WUA      = -3.674354E-15
+PUA     = 8.008744E-22   UB       = 3.976959E-19   LUB      = 8.495415E-26
+WUB     = 7.818968E-24   PUB      = -2.502251E-30  UC       = -1.224148E-10
+LUC     = 1.617235E-17   WUC      = 7.976175E-16   PUC      = -4.870566E-22
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01004072     LU0      = -2.69502E-10
+WU0     = 1.856901E-09   PU0      = -1.38488E-15   A0       = 1.023592
+LA0     = 7.791549E-08   WA0      = -1.932599E-07  PA0      = 3.712404E-13
+KETA    = 0.03089782     LKETA    = -7.199843E-09  WKETA    = 1.264146E-08
+PKETA   = -9.667874E-15  A1       = 0              A2       = 0.4
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1293548     LVOFF    = -6.487139E-10  WVOFF    = 1.137041E-08
+PVOFF   = -3.071056E-15  NFACTOR  = 1              CIT      = -0.0003062223
+LCIT    = 2.371556E-10   WCIT     = 1.151661E-10   PCIT     = -1.324412E-16
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 1.785714E-05   LETA0    = 3.696428E-11   ETAB     = -1.785714E-05
+LETAB   = -3.696428E-11  DSUB     = 0              PCLM     = 0.6714286
+LPCLM   = 1.478571E-07   PDIBLC1  = 1E-06          PDIBLC2  = 0.001785714
+LPDIBLC2= 3.696428E-09   PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 3.5E+08        PSCBE2   = 5E-07          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 6.8730453846   BETA0    = 22.67827
+KT1     = -0.2443071     LKT1     = 1.574977E-09   KT2      = -0.02755304
+LKT2    = 9.733445E-10   AT       = 10000          UTE      = -0.7721764
+LUTE    = 1.97529E-08    WUTE     = -1.467434E-07  PUTE     = 1.687549E-13
+UA1     = 1.224E-09      UB1      = -1.382905E-18  LUB1     = 3.096568E-26
+UC1     = -1.449268E-11  LUC1     = 2.980835E-17   KT1L     = 0
+PRT     = 0              CJ       = cjp            PB       = 0.895226
+MJ      = 0.4476         CJSW     = cjswp          PBSW     = 0.895226
+MJSW    = 0.3683619      CJSWG    = cjswgp         PBSWG    = 0.895226
+MJSWG   = 0.3683619      CGDO     = cgop           CGSO     = cgop
+TCJ     = 0.0009739001   TCJSW    = 0.0004130718   TCJSWG   = 0.0004130718   TPB      = 0.001572025
+TPBSW   = 0.001572025    TPBSWG  = 0.001572025    JS       = 4.92E-06       JSW      = 9E-10
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              DLC      = 2E-9
+LLC     = -0.039        )


.MODEL pch.3            PMOS   (                    LMIN     = 1.8E-07
+LMAX    = '5E-07-dxl'    WMIN     = '1.01E-05-dxw' WMAX     = 0.000101
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.4550796+dvthp' LVTH0    = -7.568369E-09  WVTH0    = 6.81538E-08
+PVTH0   = -6.751318E-15  K1       = 0.5074729      LK1      = 1.835105E-08
+WK1     = 2.494346E-07   PK1      = -1.533307E-14  K2       = 0.04798815
+LK2     = -6.750804E-09  WK2      = -1.04983E-07   PK2      = 8.71888E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 130812.5       LVSAT    = -0.0003656236
+UA      = 1.080984E-09   LUA      = -1.688024E-16  WUA      = -2.087708E-15
+PUA     = 8.688397E-23   UB       = 1.740202E-19   LUB      = 1.856082E-25
+WUB     = 3.67887E-24    PUB      = -6.392069E-31  UC       = -1.457954E-10
+LUC     = 2.66936E-17    WUC      = -1.016314E-16  PUC      = -8.239455E-23
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.009606076    LU0      = -7.391318E-11
+WU0     = -6.536676E-10  PU0      = -2.551239E-16  A0       = 1.233097
+LA0     = -1.636207E-08  WA0      = -9.402152E-08  PA0      = 3.265831E-13
+KETA    = 0.01660392     LKETA    = -7.675898E-10  WKETA    = -7.484155E-09
+PKETA   = -6.113507E-16  A1       = 0              A2       = 0.4
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1262417     LVOFF    = -2.049622E-09  WVOFF    = -4.056333E-08
+PVOFF   = 2.029913E-14   NFACTOR  = 1              CIT      = -0.0001049554
+LCIT    = 1.465856E-10   WCIT     = 6.463967E-10   PCIT     = -3.714952E-16
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -0.0004687502  LETA0    = 2.559375E-10   ETAB     = 0.001078125
+LETAB   = -5.301563E-10  DSUB     = 0              PCLM     = 0.9197022
+LPCLM   = 3.613398E-08   WPCLM    = -9.529438E-08  PPCLM    = 4.288248E-14
+PDIBLC1 = 1E-06          PDIBLC2  = 0.005710225    LPDIBLC2 = 1.930398E-09
+WPDIBLC2= 2.274334E-08   PPDIBLC2 = -1.02345E-14   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 3.5E+08        PSCBE2   = 5E-07
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 6.8730453846
+BETA0   = 22.67827       KT1      = -0.2348893     LKT1     = -2.662992E-09
+KT2     = -0.02487671    LKT2     = -2.310046E-10  AT       = 10000
+UTE     = -0.7355645     LUTE     = 3.277554E-09   WUTE     = 2.660134E-07
+PUTE    = -1.698563E-14  UA1      = 1.224E-09      UB1      = -1.378107E-18
+LUB1    = 2.880672E-26   UC1      = 6.698567E-11   LUC1     = -6.856913E-18
+KT1L    = 0              PRT      = 0              CJ       = cjp
+PB      = 0.895226       MJ       = 0.4476         CJSW     = cjswp
+PBSW    = 0.895226       MJSW     = 0.3683619      CJSWG    = cjswgp
+PBSWG   = 0.895226       MJSWG    = 0.3683619      CGDO     = cgop
+CGSO    = cgop           TCJ      = 0.0009739001   TCJSW    = 0.0004130718   TCJSWG   = 0.0004130718
+TPB     = 0.001572025    TPBSW    = 0.001572025    TPBSWG   = 0.001572025    JS       = 4.92E-06
+JSW     = 9E-10          N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+DLC     = 2E-9           LLC     = -0.039          )


.MODEL pch.4            PMOS   (                    LMIN     = '1.2E-06-dxl'
+LMAX    = 2.1E-05        WMIN     = '1.3E-06-dxw'  WMAX     = '1.01E-05-dxw'
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.4374633+dvthp' LVTH0    = -2.408414E-08  WVTH0    = 1.471636E-08
+PVTH0   = -7.277214E-15  K1       = 0.5343876      LK1      = 1.806018E-08
+WK1     = 1.253323E-08   PK1      = 7.213184E-15   K2       = 0.03616726
+LK2     = -5.236313E-09  WK2      = -5.814751E-09  PK2      = -2.50107E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 151306.8       LVSAT    = -0.01300284
+UA      = 8.425718E-10   LUA      = -3.904175E-16  WUA      = 1.989964E-16
+PUA     = 6.452796E-26   UB       = 7.128847E-19   LUB      = 4.125238E-25
+WUB     = -7.246685E-25  PUB      = 3.742612E-31   UC       = -8.017901E-11
+LUC     = 1.802016E-17   WUC      = -8.347328E-17  PUC      = 1.847838E-23
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01112962     LU0      = -1.309183E-09
+WU0     = -1.340516E-09  PU0      = 1.516926E-16   A0       = 1.044546
+LA0     = 6.895549E-08   WA0      = -5.956933E-08  PA0      = 6.50618E-14
+KETA    = 0.0260897      LKETA    = -1.288132E-09  WKETA    = 7.459047E-09
+PKETA   = -7.558624E-15  A1       = 0              A2       = 0.4
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1273455     LVOFF    = -1.352654E-09  WVOFF    = -5.45451E-10
+PVOFF   = -5.548117E-15  NFACTOR  = 1              CIT      = -0.0001
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 5E-05          ETAB     = -5E-05         DSUB     = 0
+PCLM    = 0.5738637      LPCLM    = 2.600568E-07   PDIBLC1  = 1E-06
+PDIBLC2 = 0.000477273    LPDIBLC2 = 5.201136E-09   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 1.803977E+08   LPSCBE1  = 195.0426
+PSCBE2  = 5E-07          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 6.8730453846   BETA0    = 22.67827       KT1      = -0.2303
+LKT1    = -1.635442E-08  WKT1     = 7.095216E-09   PKT1     = 1.018142E-14
+KT2     = -0.02416969    LKT2     = -3.344287E-09  WKT2     = 1.381573E-09
+PKT2    = 2.70884E-15    AT       = 10000          UTE      = -0.8501847
+LUTE    = 9.734694E-08   WUTE     = 1.159489E-07   PUTE     = -1.133805E-14
+UA1     = 1.224E-09      UB1      = -1.405289E-18  LUB1     = 5.362257E-26
+WUB1    = 7.555995E-26   PUB1     = -5.582602E-32  UC1      = -9.419797E-12
+LUC1    = 1.833659E-17   WUC1     = 2.716705E-17   PUC1     = 2.553191E-23
+KT1L    = 0              PRT      = 0              CJ       = cjp
+PB      = 0.895226       MJ       = 0.4476         CJSW     = cjswp
+PBSW    = 0.895226       MJSW     = 0.3683619      CJSWG    = cjswgp
+PBSWG   = 0.895226       MJSWG    = 0.3683619      CGDO     = cgop
+CGSO    = cgop           TCJ      = 0.0009739001   TCJSW    = 0.0004130718   TCJSWG   = 0.0004130718
+TPB     = 0.001572025    TPBSW    = 0.001572025    TPBSWG   = 0.001572025    JS       = 4.92E-06
+JSW     = 9E-10          N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+DLC     = 2E-9           LLC     = -0.039          )


.MODEL pch.5            PMOS   (                    LMIN     = '5E-07-dxl'
+LMAX    = '1.2E-06-dxl'  WMIN     = '1.3E-06-dxw'  WMAX     = '1.01E-05-dxw'
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.452691+dvthp' LVTH0    = -6.572238E-09  WVTH0    = 9.404809E-09
+PVTH0   = -1.168931E-15  K1       = 0.5438333      LK1      = 7.197658E-09
+WK1     = -3.26195E-08   PK1      = 5.913883E-14   K2       = 0.03407168
+LK2     = -2.826403E-09  WK2      = 8.27388E-09    PK2      = -1.8703E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 146428.6       LVSAT    = -0.007392862
+UA      = 4.708172E-10   LUA      = 3.710029E-17   WUA      = 5.57092E-16
+PUA     = -4.117454E-22  UB       = 1.245562E-18   LUB      = -2.000556E-25
+WUB     = -7.190487E-25  PUB      = 3.677984E-31   UC       = -3.187988E-11
+LUC     = -3.752386E-17  WUC      = -1.140697E-16  PUC      = 5.36643E-23
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01027813     LU0      = -3.299697E-10
+WU0     = -5.338523E-10  PU0      = -7.759703E-16  A0       = 0.9911001
+LA0     = 1.304183E-07   WA0      = 1.339304E-07   PA0      = -1.574629E-13
+KETA    = 0.03221126     LKETA    = -8.327926E-09  WKETA    = -5.849047E-10
+PKETA   = 1.691919E-15   A1       = 0              A2       = 0.4
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1272677     LVOFF    = -1.442123E-09  WVOFF    = -9.646923E-09
+PVOFF   = 4.918577E-15   NFACTOR  = 1              CIT      = -0.0002927503
+LCIT    = 2.216628E-10   WCIT     = -2.049704E-11  PCIT     = 2.357161E-17
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 1.785715E-05   LETA0    = 3.696428E-11   ETAB     = -1.785715E-05
+LETAB   = -3.696428E-11  DSUB     = 0              PCLM     = 0.6714286
+LPCLM   = 1.478571E-07   PDIBLC1  = 1E-06          PDIBLC2  = 0.001785715
+LPDIBLC2= 3.696428E-09   PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 3.5E+08        PSCBE2   = 5E-07          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 6.8730453846   BETA0    = 22.67827
+KT1     = -0.2459082     LKT1     = 1.594939E-09   WKT1     = 1.612342E-08
+PKT1    = -2.010177E-16  KT2      = -0.02786744    LKT2     = 9.081306E-10
+WKT2    = 3.166038E-09   PKT2     = 6.567054E-16   AT       = 10000
+UTE     = -0.7946973     LUTE     = 3.353639E-08   WUTE     = 8.00418E-08
+PUTE    = 2.995515E-14   UA1      = 1.224E-09      UB1      = -1.399018E-18
+LUB1    = 4.641101E-26   WUB1     = 1.62263E-25    PUB1     = -1.555346E-31
+UC1     = -2.426946E-11  LUC1     = 3.541371E-17   WUC1     = 9.845219E-17
+PUC1    = -5.644601E-23  KT1L     = 0              PRT      = 0
+CJ      = cjp            PB       = 0.895226       MJ       = 0.4476
+CJSW    = cjswp          PBSW     = 0.895226       MJSW     = 0.3683619
+CJSWG   = cjswgp         PBSWG    = 0.895226       MJSWG    = 0.3683619
+CGDO    = cgop           CGSO     = cgop           TCJ      = 0.0009739001
+TCJSW   = 0.0004130718   TCJSWG  = 0.0004130718   TPB      = 0.001572025    TPBSW    = 0.001572025    TPBSWG   = 0.001572025
+JS      = 4.92E-06       JSW      = 9E-10          N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0   = 0             DLC      = 2E-9           LLC     = -0.039           )


.MODEL pch.6            PMOS   (                    LMIN     = 1.8E-07
+LMAX    = '5E-07-dxl'    WMIN     = '1.3E-06-dxw'  WMAX     = '1.01E-05-dxw'
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.4493721+dvthp' LVTH0    = -8.06576E-09   WVTH0    = 1.067962E-08
+PVTH0   = -1.742597E-15  K1       = 0.5178921      LK1      = 1.88712E-08
+WK1     = 1.445133E-07   PK1      = -2.057092E-14  K2       = 0.04280981
+LK2     = -6.758558E-09  WK2      = -5.283713E-08  PK2      = 8.796957E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 130812.5       LVSAT    = -0.0003656236
+UA      = 9.499295E-10   LUA      = -1.785002E-16  WUA      = -7.679882E-16
+PUA     = 1.845406E-22   UB       = 4.958583E-19   LUB      = 1.373112E-25
+WUB     = 4.379602E-25   PUB      = -1.528556E-31  UC       = -1.587904E-10
+LUC     = 1.958586E-17   WUC      = 2.922792E-17   PUC      = -1.081963E-23
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.009831898    LU0      = -1.291645E-10
+WU0     = -2.92769E-09   PU0      = 3.012566E-16   A0       = 1.27343
+LA0     = 3.369685E-09   WA0      = -5.001745E-07  PA0      = 1.278843E-13
+KETA    = 0.01500061     LKETA    = -5.831355E-10  WKETA    = 8.661148E-09
+PKETA   = -2.468804E-15  A1       = 0              A2       = 0.4
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1308178     LVOFF    = 1.554266E-10   WVOFF    = 5.518163E-09
+PVOFF   = -1.905712E-15  NFACTOR  = 1              CIT      = -6.280855E-05
+LCIT    = 1.18189E-10    WCIT     = 2.219781E-10   PCIT     = -8.554223E-17
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -0.0004687502  LETA0    = 2.559375E-10   ETAB     = 0.001136754
+LETAB   = -5.565394E-10  WETAB    = -5.903965E-10  PETAB    = 2.656785E-16
+DSUB    = 0              PCLM     = 0.91154        LPCLM    = 3.980698E-08
+WPCLM   = -1.310087E-08  PPCLM    = 5.895399E-15   PDIBLC1  = 1E-06
+PDIBLC2 = 0.00796875     LPDIBLC2 = 9.140624E-10   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 3.5E+08        PSCBE2   = 5E-07
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 6.8730453846
+BETA0   = 22.67827       KT1      = -0.2368895     LKT1     = -2.463487E-09
+WKT1    = 2.014118E-08   PKT1     = -2.009008E-15  KT2      = -0.02567999
+LKT2    = -7.622315E-11  WKT2     = 8.089046E-09   PKT2     = -1.558648E-15
+AT      = 10000          UTE      = -0.7213691     LUTE     = 5.387008E-10
+WUTE    = 1.230652E-07   PUTE     = 1.059462E-14   UA1      = 1.224E-09
+UB1     = -1.352532E-18  LUB1     = 2.549208E-26   WUB1     = -2.575436E-25
+PUB1    = 3.337843E-32   UC1      = 7.191495E-11   LUC1     = -7.869275E-18
+WUC1    = -4.963781E-17  PUC1     = 1.019449E-23   KT1L     = 0
+PRT     = 0              CJ       = cjp            PB       = 0.895226
+MJ      = 0.4476         CJSW     = cjswp          PBSW     = 0.895226
+MJSW    = 0.3683619      CJSWG    = cjswgp         PBSWG    = 0.895226
+MJSWG   = 0.3683619      CGDO     = cgop           CGSO     = cgop
+TCJ     = 0.0009739001   TCJSW    = 0.0004130718   TCJSWG   = 0.0004130718   TPB      = 0.001572025
+TPBSW   = 0.001572025    TPBSWG  = 0.001572025    JS       = 4.92E-06       JSW      = 9E-10
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              DLC      = 2E-9
+LLC     = -0.039        )


.MODEL pch.7            PMOS   (                    LMIN     = '1.2E-06-dxl'
+LMAX    = 2.1E-05        WMIN     = '6E-07-dxw'    WMAX     = '1.3E-06-dxw'
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.4236826+dvthp' LVTH0    = -4.209848E-08  WVTH0    = -2.785141E-09
+PVTH0   = 1.560099E-14   K1       = 0.5423383      LK1      = 2.988238E-08
+WK1     = 2.435904E-09   PK1      = -7.800999E-15  K2       = 0.03449369
+LK2     = -9.442159E-09  WK2      = -3.689318E-09  PK2      = 2.840354E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 151306.8       LVSAT    = -0.01300284
+UA      = 1.106971E-09   LUA      = -6.623647E-16  WUA      = -1.367901E-16
+PUA     = 3.454374E-22   UB       = 2.174056E-19   LUB      = 1.283252E-24
+WUB     = -9.541014E-26  PUB      = -7.31563E-31   UC       = -1.198028E-10
+LUC     = 9.54289E-17    WUC      = -3.315101E-17  PUC      = -7.983071E-23
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01021944     LU0      = -9.699905E-10
+WU0     = -1.845879E-10  PU0      = -2.790822E-16  A0       = 0.9916247
+LA0     = 6.353922E-08   WA0      = 7.640753E-09   PA0      = 7.194045E-14
+KETA    = 0.03057079     LKETA    = -5.18059E-10   WKETA    = 1.768055E-09
+PKETA   = -8.536616E-15  A1       = 0              A2       = 0.4
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1270682     LVOFF    = -1.218737E-08  WVOFF    = -8.977046E-10
+PVOFF   = 8.211964E-15   NFACTOR  = 1              CIT      = -0.0001
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 5E-05          ETAB     = -5E-05         DSUB     = 0
+PCLM    = 0.5738636      LPCLM    = 2.600568E-07   PDIBLC1  = 1E-06
+PDIBLC2 = 0.0004772726   LPDIBLC2 = 5.201136E-09   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 1.803977E+08   LPSCBE1  = 195.0426
+PSCBE2  = 5E-07          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 6.8730453846   BETA0    = 22.67827       KT1      = -0.2305241
+LKT1    = -1.020931E-08  WKT1     = 7.379732E-09   PKT1     = 2.377124E-15
+KT2     = -0.02276375    LKT2     = -2.211963E-10  WKT2     = -4.039696E-10
+PKT2    = -1.257485E-15  AT       = 10000          UTE      = -0.7486248
+LUTE    = 3.492936E-08   WUTE     = -1.303221E-08  PUTE     = 6.793227E-14
+UA1     = 1.224E-09      UB1      = -1.392484E-18  LUB1     = 1.14957E-25
+WUB1    = 5.929722E-26   PUB1     = -1.337207E-31  UC1      = -9.73658E-12
+LUC1    = 1.696398E-17   WUC1     = 2.756936E-17   PUC1     = 2.727514E-23
+KT1L    = 0              PRT      = 0              CJ       = cjp
+PB      = 0.895226       MJ       = 0.4476         CJSW     = cjswp
+PBSW    = 0.895226       MJSW     = 0.3683619      CJSWG    = cjswgp
+PBSWG   = 0.895226       MJSWG    = 0.3683619      CGDO     = cgop
+CGSO    = cgop           TCJ      = 0.0009739001   TCJSW    = 0.0004130718   TCJSWG   = 0.0004130718
+TPB     = 0.001572025    TPBSW    = 0.001572025    TPBSWG   = 0.001572025    JS       = 4.92E-06
+JSW     = 9E-10          N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+DLC     = 2E-9           LLC     = -0.039         )


.MODEL pch.8            PMOS   (                    LMIN     = '5E-07-dxl'
+LMAX    = '1.2E-06-dxl'  WMIN     = '6E-07-dxw'    WMAX     = '1.3E-06-dxw'
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.457419+dvthp' LVTH0    = -3.301601E-09  WVTH0    = 1.540932E-08
+PVTH0   = -5.322639E-15  K1       = 0.4661291      LK1      = 1.175229E-07
+WK1     = 6.606479E-08   PK1      = -8.097422E-14  K2       = 0.06045378
+LK2     = -3.929626E-08  WK2      = -2.523138E-08  PK2      = 2.761372E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 146428.6       LVSAT    = -0.007392867
+UA      = 1.026414E-09   LUA      = -5.697246E-16  WUA      = -1.485162E-16
+PUA     = 3.589222E-22   UB       = 1.20417E-18    LUB      = 1.484726E-25
+WUB     = -6.664801E-25  PUB      = -7.483251E-32  UC       = -5.049388E-11
+LUC     = 1.572358E-17   WUC      = -9.042993E-17  PUC      = -1.395995E-23
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01094816     LU0      = -1.80802E-09
+WU0     = -1.384793E-09  PU0      = 1.101153E-15   A0       = 1.199156
+LA0     = -1.751223E-07  WA0      = -1.303012E-07  PA0      = 2.305737E-13
+KETA    = 0.0411355      LKETA    = -1.266747E-08  WKETA    = -1.191869E-08
+PKETA   = 7.203139E-15   A1       = 0              A2       = 0.4
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1442872     LVOFF    = 7.614513E-09   WVOFF    = 1.196779E-08
+PVOFF   = -6.58335E-15   NFACTOR  = 1              CIT      = -0.0003188039
+LCIT    = 2.516245E-10   WCIT     = 1.259109E-11   PCIT     = -1.447976E-17
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 1.785714E-05   LETA0    = 3.696428E-11   ETAB     = -1.785714E-05
+LETAB   = -3.696428E-11  DSUB     = 0              PCLM     = 0.6714286
+LPCLM   = 1.478571E-07   PDIBLC1  = 1E-06          PDIBLC2  = 0.001785715
+LPDIBLC2= 3.696428E-09   PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 3.5E+08        PSCBE2   = 5E-07          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 6.8730453846   BETA0    = 22.67827
+KT1     = -0.24406       LKT1     = 5.357059E-09   WKT1     = 1.377628E-08
+PKT1    = -4.97891E-15   KT2      = -0.02559545    LKT2     = 3.035259E-09
+WKT2    = 2.806062E-10   PKT2     = -2.044748E-15  AT       = 10000
+UTE     = -0.8199239     LUTE     = 1.169233E-07   WUTE     = 1.120795E-07
+PUTE    = -7.594623E-14  UA1      = 1.224E-09      UB1      = -1.180645E-18
+LUB1    = -1.286574E-25  WUB1     = -1.150706E-25  PUB1     = 6.680229E-32
+UC1     = 2.760364E-11   LUC1     = -2.597728E-17  WUC1     = 3.257336E-17
+PUC1    = 2.152054E-23   KT1L     = 0              PRT      = 0
+CJ      = cjp            PB       = 0.895226       MJ       = 0.4476
+CJSW    = cjswp          PBSW     = 0.895226       MJSW     = 0.3683619
+CJSWG   = cjswgp         PBSWG    = 0.895226       MJSWG    = 0.3683619
+CGDO    = cgop           CGSO     = cgop           TCJ      = 0.0009739001
+TCJSW   = 0.0004130718   TCJSWG  = 0.0004130718   TPB      = 0.001572025    TPBSW    = 0.001572025    TPBSWG   = 0.001572025
+JS      = 4.92E-06       JSW      = 9E-10          N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0   = 0             DLC      = 2E-9           LLC      = -0.039         )


.MODEL pch.9            PMOS   (                    LMIN     = 1.8E-07
+LMAX    = '5E-07-dxl'    WMIN     = '6E-07-dxw'    WMAX     = '1.3E-06-dxw'
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.4342877+dvthp' LVTH0    = -1.371066E-08  WVTH0    = -8.477504E-09
+PVTH0   = 5.426431E-15   K1       = 0.7542717      LK1      = -1.214128E-08
+WK1     = -1.556889E-07  PK1      = 1.881492E-14   K2       = -0.04034913
+LK2     = 6.065043E-09   WK2      = 5.277471E-08   PK2      = -7.489014E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 130812.5       LVSAT    = -0.0003656224
+UA      = -3.876963E-10  LUA      = 6.662492E-17   WUA      = 9.307964E-16
+PUA     = -1.267683E-22  UB       = 1.708786E-18   LUB      = -7.860463E-26
+WUB     = -1.102458E-24  PUB      = 1.213575E-31   UC       = -2.692677E-11
+LUC     = 5.118379E-18   WUC      = -1.382389E-16  PUC      = 7.55407E-24
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.006271143    LU0      = 2.966392E-10
+WU0     = 1.594468E-09   PU0      = -2.39514E-16   A0       = 0.3846521
+LA0     = 1.914046E-07   WA0      = 6.285738E-07   PA0      = -1.1092E-13
+KETA    = 0.01588796     LKETA    = -1.306077E-09  WKETA    = 7.534219E-09
+PKETA   = -1.550669E-15  A1       = 0              A2       = 0.4
+AGS     = 0.006767845    LAGS     = 5.954466E-09   WAGS     = 1.680483E-08
+PAGS    = -7.562171E-15  B0       = 0              B1       = 0
+VOFF    = -0.1286419     LVOFF    = 5.741402E-10   WVOFF    = 2.754739E-09
+PVOFF   = -2.437478E-15  NFACTOR  = 1              CIT      = 0.0001336648
+LCIT    = 4.801357E-11   WCIT     = -2.7543E-11    PCIT     = 3.580592E-18
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -0.0004687502  LETA0    = 2.559375E-10   ETAB     = 0.0006718751
+LETAB   = -3.473438E-10  DSUB     = 0              PCLM     = 0.8429525
+LPCLM   = 7.067135E-08   WPCLM    = 7.400524E-08   PPCLM    = -3.330235E-14
+PDIBLC1 = 1E-06          PDIBLC2  = 0.009622769    LPDIBLC2 = 1.697542E-10
+WPDIBLC2= -2.100604E-09  PPDIBLC2 = 9.452714E-16   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 3.5E+08        PSCBE2   = 5E-07
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 6.8730453846
+BETA0   = 22.67827       KT1      = -0.2223596     LKT1     = -4.408159E-09
+WKT1    = 1.688208E-09   PKT1     = 4.607245E-16   KT2      = -0.01169408
+LKT2    = -3.220356E-09  WKT2     = -9.673057E-09  PKT2     = 2.4344E-15
+AT      = 10000          UTE      = -0.5805172     LUTE     = 9.190298E-09
+WUTE    = -5.581674E-08  PUTE     = -3.929105E-16  UA1      = 1.224E-09
+UB1     = -1.64321E-18   LUB1     = 7.94965E-26    WUB1     = 1.116172E-25
+PUB1    = -3.520719E-32  UC1      = -5.644295E-11  LUC1     = 1.184368E-17
+WUC1    = 1.133767E-16   PUC1     = -1.484096E-23  KT1L     = 0
+PRT     = 0              CJ       = cjp            PB       = 0.895226
+MJ      = 0.4476         CJSW     = cjswp          PBSW     = 0.895226
+MJSW    = 0.3683619      CJSWG    = cjswgp         PBSWG    = 0.895226
+MJSWG   = 0.3683619      CGDO     = cgop           CGSO     = cgop
+TCJ     = 0.0009739001   TCJSW    = 0.0004130718   TCJSWG   = 0.0004130718   TPB      = 0.001572025
+TPBSW   = 0.001572025    TPBSWG  = 0.001572025    JS       = 4.92E-06       JSW      = 9E-10
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              DLC      = 2E-9
+LLC     = -0.039        )


.MODEL pch.10           PMOS   (                    LMIN     = '1.2E-06-dxl'
+LMAX    = 2.1E-05        WMIN     = 2.2E-07        WMAX     = '6E-07-dxw'
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.4303286+dvthp' LVTH0    = -2.737427E-08  WVTH0    = 1.003085E-09
+PVTH0   = 7.208191E-15   K1       = 0.5469828      LK1      = -4.144793E-08
+WK1     = -2.114652E-10  PK1      = 3.285728E-14   K2       = 0.03273299
+LK2     = 2.015941E-08   WK2      = -2.685718E-09  PK2      = -1.403254E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 151306.8       LVSAT    = -0.01300284
+UA      = 1.217034E-09   LUA      = -3.511119E-17  WUA      = -1.995263E-16
+PUA     = -1.209715E-23  UB       = 5.003731E-20   LUB      = -3.712788E-28
+WUB     = -1.026149E-29  PUB      = 1.021017E-34   UC       = -1.564762E-10
+LUC     = -6.608345E-17  WUC      = -1.22472E-17   PUC      = 1.223133E-23
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01023298     LU0      = -9.387005E-10
+WU0     = -1.923019E-10  PU0      = -2.969176E-16  A0       = 0.8403727
+LA0     = 4.720727E-07   WA0      = 9.38544E-08    PA0      = -1.609236E-13
+KETA    = 0.0461074      LKETA    = -4.22138E-08   WKETA    = -7.087812E-09
+PKETA   = 1.522996E-14   A1       = 0              A2       = 0.4
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1262222     LVOFF    = -1.866991E-09  WVOFF    = -1.379926E-09
+PVOFF   = 2.32935E-15    NFACTOR  = 1              CIT      = -0.0001
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 5E-05          ETAB     = -5E-05         DSUB     = 0
+PCLM    = 0.5738636      LPCLM    = 2.600568E-07   PDIBLC1  = 1E-06
+PDIBLC2 = 0.0004772726   LPDIBLC2 = 5.201136E-09   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 1.803977E+08   LPSCBE1  = 195.0426
+PSCBE2  = 5E-07          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 6.8730453846   BETA0    = 22.67827       KT1      = -0.2230191
+LKT1    = -9.921544E-09  WKT1     = 3.101877E-09   PKT1     = 2.213099E-15
+KT2     = -0.02651932    LKT2     = -1.693776E-09  WKT2     = 1.736708E-09
+PKT2    = -4.181145E-16  AT       = 10000          UTE      = -0.7886902
+LUTE    = 2.207672E-07   WUTE     = 9.805095E-09   PUTE     = -3.799531E-14
+UA1     = 1.224E-09      UB1      = -1.283856E-18  LUB1     = -1.981768E-25
+WUB1    = -2.620757E-27  PUB1     = 4.476558E-32   UC1      = 5.463716E-11
+LUC1    = 9.531897E-17   WUC1     = -9.123675E-18  PUC1     = -1.738722E-23
+KT1L    = 0              PRT      = 0              CJ       = cjp
+PB      = 0.895226       MJ       = 0.4476         CJSW     = cjswp
+PBSW    = 0.895226       MJSW     = 0.3683619      CJSWG    = cjswgp
+PBSWG   = 0.895226       MJSWG    = 0.3683619      CGDO     = cgop
+CGSO    = cgop           TCJ      = 0.0009739001   TCJSW    = 0.0004130718   TCJSWG   = 0.0004130718
+TPB     = 0.001572025    TPBSW    = 0.001572025    TPBSWG   = 0.001572025    JS       = 4.92E-06
+JSW     = 9E-10          N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+DLC     = 2E-9           LLC     = -0.039          )


.MODEL pch.11           PMOS   (                    LMIN     = '5E-07-dxl'
+LMAX    = '1.2E-06-dxl'  WMIN     = 2.2E-07        WMAX     = '6E-07-dxw'
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.4486066+dvthp' LVTH0    = -6.354536E-09  WVTH0    = 1.038626E-08
+PVTH0   = -3.582467E-15  K1       = 0.5183487      LK1      = -8.518739E-09
+WK1     = 3.629963E-08   PK1      = -9.130481E-15  K2       = 0.04981367
+LK2     = 5.166254E-10   WK2      = -1.916651E-08  PK2      = 4.920375E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 146428.6       LVSAT    = -0.007392852
+UA      = 1.055273E-09   LUA      = 1.509141E-16   WUA      = -1.649656E-16
+PUA     = -5.184191E-23  UB       = 2.216331E-20   LUB      = 3.168382E-26
+WUB     = 7.263627E-27   PUB      = -8.26287E-33   UC       = -2.173198E-10
+LUC     = 3.886775E-18   WUC      = 4.660883E-18   PUC      = -7.212972E-24
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.009125781    LU0      = 3.345732E-10
+WU0     = -3.460346E-10  PU0      = -1.201249E-16  A0       = 1.130455
+LA0     = 1.384775E-07   WA0      = -9.114161E-08  PA0      = 5.182181E-14
+KETA    = 0.002687342    LKETA    = 7.719271E-09   WKETA    = 9.996764E-09
+PKETA   = -4.417304E-15  A1       = 0              A2       = 0.4
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1191891     LVOFF    = -9.954978E-09  WVOFF    = -2.338109E-09
+PVOFF   = 3.431261E-15   NFACTOR  = 1              CIT      = -0.0002967142
+LCIT    = 2.262214E-10   CDSC     = 0              CDSCB    = 0
+CDSCD   = 0              ETA0     = 1.785715E-05   LETA0    = 3.696428E-11
+ETAB    = -1.785715E-05  LETAB    = -3.696428E-11  DSUB     = 0
+PCLM    = 0.6714286      LPCLM    = 1.478571E-07   PDIBLC1  = 1E-06
+PDIBLC2 = 0.001785715    LPDIBLC2 = 3.696428E-09   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 3.5E+08        PSCBE2   = 5E-07
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 6.8730453846
+BETA0   = 22.67827       KT1      = -0.2400945     LKT1     = 9.715253E-09
+WKT1    = 1.151595E-08   PKT1     = -7.463081E-15  KT2      = -0.02725602
+LKT2    = -8.465783E-10  WKT2     = 1.22713E-09    PKT2     = 1.679E-16
+AT      = 10000          UTE      = -0.5941593     LUTE     = -2.943329E-09
+WUTE    = -1.660627E-08  PUTE     = -7.622238E-15  UA1      = 1.224E-09
+UB1     = -1.447885E-18  LUB1     = -9.543706E-27  WUB1     = 3.725585E-26
+PUB1    = -1.092515E-33  UC1      = 1.329441E-10   LUC1     = 5.266003E-18
+WUC1    = -2.747071E-17  PUC1     = 3.71187E-24    KT1L     = 0
+PRT     = 0              CJ       = cjp            PB       = 0.895226
+MJ      = 0.4476         CJSW     = cjswp          PBSW     = 0.895226
+MJSW    = 0.3683619      CJSWG    = cjswgp         PBSWG    = 0.895226
+MJSWG   = 0.3683619      CGDO     = cgop           CGSO     = cgop
+TCJ     = 0.0009739001   TCJSW    = 0.0004130718   TCJSWG   = 0.0004130718   TPB      = 0.001572025
+TPBSW   = 0.001572025    TPBSWG  = 0.001572025    JS       = 4.92E-06       JSW      = 9E-10
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              DLC      = 2E-9
+LLC     = -0.039        )


.MODEL pch.12           PMOS   (                    LMIN     = 1.8E-07
+LMAX    = '5E-07-dxl'    WMIN     = 2.2E-07        WMAX     = '6E-07-dxw'
+NOIMOD  = 3              EF       = 1.25           AF       = 1.052          KF      = 6.100E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp           XJ       = 1.7E-07        NCH      = 3.9E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl'
+XW      = '0+dxw'        DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.4639236+dvthp' LVTH0    = 5.381074E-10   WVTH0    = 8.414935E-09
+PVTH0   = -2.695369E-15  K1       = 0.4669949      LK1      = 1.459046E-08
+WK1     = 8.058935E-09   PK1      = 3.577831E-15   K2       = 0.05886395
+LK2     = -3.555999E-09  WK2      = -3.776749E-09  PK2      = -2.00502E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 130812.5       LVSAT    = -0.0003656262
+UA      = 1.950118E-09   LUA      = -2.517664E-16  WUA      = -4.017582E-16
+PUA     = 5.471478E-23   UB       = -4.603974E-19  LUB      = 2.488361E-25
+WUB     = 1.339767E-25   PUB      = -6.528375E-32  UC       = -2.791416E-10
+LUC     = 3.170657E-17   WUC      = 5.523607E-18   PUC      = -7.601201E-24
+RDSW    = 530            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01060315     LU0      = -3.302419E-10
+WU0     = -8.747751E-10  PU0      = 1.178083E-16   A0       = 1.424732
+LA0     = 6.052879E-09   WA0      = 3.572804E-08   PA0      = -5.269527E-15
+KETA    = 0.03131204     LKETA    = -5.161843E-09  WKETA    = -1.257509E-09
+PKETA   = 6.471187E-16   A1       = 0              A2       = 0.4
+AGS     = 0.03625        LAGS     = -7.312499E-09  B0       = 0
+B1      = 0              VOFF     = -0.1281644     LVOFF    = -5.916089E-09
+WVOFF   = 2.482577E-09   PVOFF    = 1.261953E-15   NFACTOR  = 1
+CIT     = 8.534375E-05   LCIT     = 5.429531E-11   CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = -0.0004687499
+LETA0   = 2.559375E-10   ETAB     = 0.0006718751   LETAB    = -3.473438E-10
+DSUB    = 0              PCLM     = 0.9657306      LPCLM    = 1.542123E-08
+WPCLM   = 4.02174E-09    PPCLM    = -1.809783E-15  PDIBLC1  = 1E-06
+PDIBLC2 = 0.0059375      LPDIBLC2 = 1.828125E-09   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 3.5E+08        PSCBE2   = 5E-07
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 6.8730453846
+BETA0   = 22.67827       KT1      = -0.2138071     LKT1     = -2.114083E-09
+WKT1    = -3.186682E-09  PKT1     = -8.468991E-16  KT2      = -0.03507274
+LKT2    = 2.670948E-09   WKT2     = 3.652781E-09   PKT2     = -9.236432E-16
+AT      = 10000          UTE      = -0.5993978     LUTE     = -5.860002E-10
+WUTE    = -4.505475E-08  PUTE     = 5.179581E-15   UA1      = 1.224E-09
+UB1     = -1.443847E-18  LUB1     = -1.136091E-26  WUB1     = -2.019831E-27
+PUB1    = 1.658154E-32   UC1      = 1.970068E-10   LUC1     = -2.356221E-17
+WUC1    = -3.108965E-17  PUC1     = 5.340393E-24   KT1L     = 0
+PRT     = 0              CJ       = cjp            PB       = 0.895226
+MJ      = 0.4476         CJSW     = cjswp          PBSW     = 0.895226
+MJSW    = 0.3683619      CJSWG    = cjswgp         PBSWG    = 0.895226
+MJSWG   = 0.3683619      CGDO     = cgop           CGSO     = cgop
+TCJ     = 0.0009739001   TCJSW    = 0.0004130718   TCJSWG   = 0.0004130718   TPB      = 0.001572025
+TPBSW   = 0.001572025    TPBSWG  = 0.001572025    JS       = 4.92E-06       JSW      = 9E-10
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              DLC      = 2E-9
+LLC     = -0.039        )

.ENDL MOS
***************************************************************
*                                                             *
*              3.3V MOS DEVICES MODEL                         *
*                                                             *
***************************************************************
.LIB MOS_3V

.MODEL nch3.1            NMOS   (                   LMIN     = '1.2E-06-dxl3'
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = 2.1E-05        WMIN     = '1.008E-05-dxw3'  WMAX     = 0.000101
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.7377687+dvthn3' LVTH0    = 7.158307E-08   WVTH0    = -3.897868E-08
+PVTH0   = 6.325348E-15   K1       = 0.8467453      LK1      = 7.557583E-08
+WK1     = -3.136129E-08  PK1      = 7.475098E-14   K2       = 0.03349861
+LK2     = -3.426793E-08  WK2      = 2.34241E-08    PK2      = -3.243735E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 100875         LVSAT    = -0.008662499
+UA      = -6.944382E-10  LUA      = 1.262407E-16   WUA      = 3.73698E-16
+PUA     = -1.514989E-21  UB       = 2.496918E-18   LUB      = -3.669559E-26
+WUB     = -1.467808E-24  PUB      = 4.952361E-31   UC       = 1.051554E-10
+LUC     = 3.878228E-17   WUC      = -5.16416E-17   PUC      = -2.373328E-22
+RDSW    = 545            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.04083733     LU0      = 4.450713E-10
+WU0     = -6.91997E-09   PU0      = 1.930118E-14   A0       = 0.592568
+LA0     = -1.557801E-07  WA0      = 5.950033E-08   PA0      = 1.286864E-12
+KETA    = 0.02090335     LKETA    = -4.064016E-08  WKETA    = -7.624631E-08
+PKETA   = 1.436407E-13   A1       = 0              A2       = 0.99
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1282633     LVOFF    = 1.598365E-08   WVOFF    = -6.161996E-09
+PVOFF   = -4.588978E-15  NFACTOR  = 1              CIT      = 0.0003278114
+LCIT    = 1.944153E-10   WCIT     = -2.937005E-10  PCIT     = 4.823089E-16
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 1.055666E-05   LETA0    = -5.510993E-12  WETA0    = -5.567777E-11
+PETA0   = 5.512101E-16   ETAB     = -1.055666E-05  LETAB    = 5.510993E-12
+WETAB   = 5.567777E-11   PETAB    = -5.512101E-16  DSUB     = 0
+PCLM    = 0.488708       LPCLM    = 1.117912E-07   WPCLM    = -1.208207E-07
+PPCLM   = 1.196126E-12   PDIBLC1  = 1E-06          PDIBLC2  = 0.0004375
+LPDIBLC2= 6.187499E-10   PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 1.85E+08       LPSCBE1  = 148.5          PSCBE2   = 1E-06
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 7.049416
+BETA0   = 21.5673        KT1      = -0.2986445     LKT1     = 1.366386E-08
+WKT1    = 1.085947E-08   PKT1     = -5.556219E-14  KT2      = -0.03012501
+LKT2    = 1.665211E-09   WKT2     = -5.182832E-10  PKT2     = -4.12683E-15
+AT      = 20000          UTE      = -1.415816      LUTE     = 1.235164E-07
+WUTE    = 3.3383E-07     PUTE     = 2.340896E-15   UA1      = 2.04E-09
+UB1     = -2.358585E-18  LUB1     = 6.728733E-26   WUB1     = 1.27836E-25
+PUB1    = 1.488752E-30   UC1      = -2.609013E-11  LUC1     = 4.202186E-17
+WUC1    = -1.92745E-17   PUC1     = -1.40484E-22   KT1L     = 0
+PRT     = 0              CJ       = cjn3           PB       = 0.7076023
+MJ      = 0.3259624      CJSW     = cjswn3         PBSW     = 0.7076023
+MJSW    = 0.1513672      CJSWG    = cjswgn3        PBSWG    = 0.7076023
+MJSWG   = 0.3513672      CGDO     = cgon3          CGSO     = cgon3
+TCJ     = 0.0009923959   TCJSW    = 0.0005019466     TCJSWG   = 0.0005019466   TPB      = 0.001687207
+TPBSW   = 0.001687207    TPBSWG  = 0.001687207    JS       = 7.93E-06       JSW      = 7E-11
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              LLC      = -0.0165         )


.MODEL nch3.2            NMOS   (                   LMIN     = '5E-07-dxl3'
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = '1.2E-06-dxl3' WMIN     = '1.008E-05-dxw3'  WMAX     = 0.000101
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.7864478+dvthn3' LVTH0    = 1.803612E-08   WVTH0    = -9.46186E-09
+PVTH0   = -2.614315E-14  K1       = 0.8711752      LK1      = 4.870299E-08
+WK1     = 1.401369E-08   PK1      = 2.483856E-14   K2       = 0.02616277
+LK2     = -2.61985E-08   WK2      = 4.172089E-09   PK2      = -1.126011E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 94142.86       LVSAT    = -0.001257143
+UA      = -5.355195E-10  LUA      = -4.856997E-17  WUA      = -1.496712E-16
+PUA     = -9.392835E-22  UB       = 1.979541E-18   LUB      = 5.324185E-25
+WUB     = 2.426098E-24   PUB      = -3.78806E-30   UC       = 5.783059E-11
+LUC     = 9.083955E-17   WUC      = 2.900559E-16   PUC      = -6.131999E-22
+RDSW    = 545            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.03864448     LU0      = 2.857201E-09
+WU0     = 2.542139E-08   PU0      = -1.627432E-14  A0       = 0.4782223
+LA0     = -2.999986E-08  WA0      = 2.2123E-07     PA0      = 1.108961E-12
+KETA    = -0.0009261457  LKETA    = -1.662771E-08  WKETA    = 4.010373E-08
+PKETA   = 1.56557E-14    A1       = 0              A2       = 0.99
+AGS     = 0.01745523     LAGS     = 2.799239E-09   WAGS     = 2.545271E-07
+PAGS    = -2.799798E-13  B0       = 0              B1       = 0
+VOFF    = -0.1164467     LVOFF    = 2.985437E-09   WVOFF    = -1.666897E-08
+PVOFF   = 6.968688E-15   NFACTOR  = 1              CIT      = 0.0005062069
+LCIT    = -1.819676E-12  WCIT     = 2.079228E-10   PCIT     = -6.947683E-17
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -0.0002769981  LETA0    = 3.107993E-10   WETA0    = 6.999492E-10
+PETA0   = -2.799797E-16  ETAB     = 0.0002769981   LETAB    = -3.107993E-10
+WETAB   = -6.999492E-10  PETAB    = 2.799797E-16   DSUB     = 0
+PCLM    = 0.4724921      LPCLM    = 1.296286E-07   WPCLM    = 1.962608E-06
+PPCLM   = -1.095646E-12  PDIBLC1  = 1E-06          PDIBLC2  = 0.001
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 3.028572E+08
+LPSCBE1 = 18.85714       PSCBE2   = 1E-06          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 7.049416       BETA0    = 21.5673
+KT1     = -0.2924466     LKT1     = 6.846169E-09   WKT1     = -1.347476E-07
+PKT1    = 1.046056E-13   KT2      = -0.0306843     LKT2     = 2.280432E-09
+WKT2    = -1.928459E-08  PKT2     = 1.65161E-14    AT       = 20000
+UTE     = -1.24258       LUTE     = -6.704394E-08  WUTE     = -1.419894E-06
+PUTE    = 1.931437E-12   UA1      = 2.04E-09       UB1      = -1.87577E-18
+LUB1    = -4.638093E-25  WUB1     = -8.046232E-24  PUB1     = 1.048023E-29
+UC1     = 6.29267E-11    LUC1     = -5.589662E-17  WUC1     = -1.381841E-15
+PUC1    = 1.358339E-21   KT1L     = 0              PRT      = 0
+CJ      = cjn3           PB       = 0.7076023      MJ       = 0.3259624
+CJSW    = cjswn3         PBSW     = 0.7076023      MJSW     = 0.1513672
+CJSWG   = cjswgn3        PBSWG    = 0.7076023      MJSWG    = 0.3513672
+CGDO    = cgon3          CGSO     = cgon3          TCJ      = 0.0009923959
+TCJSW   = 0.0005019466    TCJSWG  = 0.0005019466   TPB      = 0.001687207    TPBSW    = 0.001687207     TPBSWG   = 0.001687207
+JS      = 7.93E-06       JSW      = 7E-11          N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0   = 0              LLC     = -0.0165         )


.MODEL nch3.3            NMOS   (                    LMIN     = 3.5E-07
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = '5E-07-dxl3'   WMIN     = '1.008E-05-dxw3' WMAX     = 0.000101
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.8911014+dvthn3' LVTH0    = -2.382535E-08  WVTH0    = -2.551964E-07
+PVTH0   = 7.215065E-14   K1       = 0.7296709      LK1      = 1.053047E-07
+WK1     = 8.462786E-08   PK1      = -3.407149E-15  K2       = 0.1835346
+LK2     = -8.914726E-08  WK2      = 7.027334E-08   PK2      = -3.770058E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 92666.66       LVSAT    = -0.0006666667
+UA      = -6.760403E-10  LUA      = 7.638383E-18   WUA      = -9.076434E-16
+PUA     = -6.360946E-22  UB       = 1.359161E-18   LUB      = 7.805709E-25
+WUB     = 8.12855E-24    PUB      = -6.069042E-30  UC       = 3.000795E-10
+LUC     = -6.060015E-18  WUC      = -4.907073E-16  PUC      = -3.008947E-22
+RDSW    = 545            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.0432966      LU0      = 9.963517E-10
+WU0     = -6.419746E-09  PU0      = -3.53786E-15   A0       = 1.297343
+LA0     = -3.576483E-07  WA0      = -4.086813E-06  PA0      = 2.832179E-12
+KETA    = -0.053454      LKETA    = 4.383425E-09   WKETA    = -4.725623E-08
+PKETA   = 5.059968E-14   A1       = 0              A2       = 0.99
+AGS     = 0.09854218     LAGS     = -2.963555E-08  WAGS     = -1.187793E-06
+PAGS    = 2.969482E-13   B0       = 0              B1       = 0
+VOFF    = -0.1158457     LVOFF    = 2.745016E-09   WVOFF    = 1.492712E-07
+PVOFF   = -5.94074E-14   NFACTOR  = 1              CIT      = 0.0005365447
+LCIT    = -1.395478E-11  WCIT     = -4.545648E-10  PCIT     = 1.955182E-16
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -0.001166667   LETA0    = 6.666667E-10   ETAB     = 0.003666667
+LETAB   = -1.666667E-09  DSUB     = 0              PCLM     = 0.396495
+LPCLM   = 1.600274E-07   WPCLM    = -5.407268E-06  PPCLM    = 1.852305E-12
+PDIBLC1 = 1E-06          PDIBLC2  = -0.006962223   LPDIBLC2 = 3.184889E-09
+WPDIBLC2= -3.711853E-08  PPDIBLC2 = 1.484741E-14   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 3.5E+08        PSCBE2   = 1E-06
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 7.049416
+BETA0   = 21.5673        KT1      = -0.3037852     LKT1     = 1.138163E-08
+WKT1    = 3.503706E-07   PKT1     = -8.944172E-14  KT2      = -0.002439955
+LKT2    = -9.017305E-09  WKT2     = -1.554807E-07  PKT2     = 7.099455E-14
+AT      = -17044.43      LAT      = 0.01481777     WAT      = 0.3711852
+PAT     = -1.484741E-07  UTE      = -1.105417      LUTE     = -1.219091E-07
+WUTE    = 1.001793E-06   PUTE     = 9.627622E-13   UA1      = 2.04E-09
+UB1     = 1.44435E-18    LUB1     = -1.791857E-24  WUB1     = -3.053457E-23
+PUB1    = 1.947557E-29   UC1      = -1.074149E-11  LUC1     = -2.642934E-17
+WUC1    = 1.01708E-15    PUC1     = 3.987705E-22   KT1L     = 0
+PRT     = 0              CJ       = cjn3           PB       = 0.7076023
+MJ      = 0.3259624      CJSW     = cjswn3         PBSW     = 0.7076023
+MJSW    = 0.1513672      CJSWG    = cjswgn3        PBSWG    = 0.7076023
+MJSWG   = 0.3513672      CGDO     = cgon3          CGSO     = cgon3
+TCJ     = 0.0009923959   TCJSW    = 0.0005019466     TCJSWG   = 0.0005019466   TPB      = 0.001687207
+TPBSW   = 0.001687207    TPBSWG  = 0.001687207    JS       = 7.93E-06       JSW      = 7E-11
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              LLC     = -0.0165                  )


.MODEL nch3.4            NMOS   (                   LMIN     = '1.2E-06-dxl3'
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = 2.1E-05        WMIN     = '1.28E-06-dxw3'  WMAX   = '1.008E-05-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.7336556+dvthn3' LVTH0    = 7.444032E-08   WVTH0    = 2.23491E-09
+PVTH0   = -2.23043E-14   K1       = 0.8418784      LK1      = 8.796925E-08
+WK1     = 1.740495E-08   PK1      = -4.943116E-14  K2       = 0.03582491
+LK2     = -3.914678E-08  WK2      = 1.145524E-10   PK2      = 1.644873E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 100875         LVSAT    = -0.008662499
+UA      = -6.560352E-10  LUA      = -2.705887E-17  WUA      = -1.110076E-17
+PUA     = 2.107195E-23   UB       = 2.385738E-18   LUB      = 2.565929E-26
+WUB     = -3.537852E-25  PUB      = -1.295599E-31  UC       = 1.018025E-10
+LUC     = 1.609684E-17   WUC      = -1.804592E-17  PUC      = -1.002473E-23
+RDSW    = 545            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.04046077     LU0      = 2.494007E-09
+WU0     = -3.146855E-09  PU0      = -1.22915E-15   A0       = 0.5930781
+LA0     = -1.696911E-08  WA0      = 5.438891E-08   PA0      = -1.040221E-13
+KETA    = 0.01336339     LKETA    = -2.632559E-08  WKETA    = -6.95778E-10
+PKETA   = 2.086418E-16   A1       = 0              A2       = 0.99
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1291182     LVOFF    = 1.551555E-08   WVOFF    = 2.40407E-09
+PVOFF   = 1.014263E-16   NFACTOR  = 1              CIT      = 0.0003008568
+LCIT    = 2.39805E-10    WCIT     = -2.361532E-11  PCIT     = 2.75049E-17
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 4.306819E-06   LETA0    = 5.636249E-11   WETA0    = 6.94568E-12
+PETA0   = -6.876224E-17  ETAB     = -4.306819E-06  LETAB    = -5.636249E-11
+WETAB   = -6.94568E-12   PETAB    = 6.876224E-17   DSUB     = 0
+PCLM    = 0.4771734      LPCLM    = 2.259838E-07   WPCLM    = -5.243991E-09
+PPCLM   = 5.19155E-14    PDIBLC1  = 1E-06          PDIBLC2  = 0.0004375
+LPDIBLC2= 6.187499E-10   PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 1.85E+08       LPSCBE1  = 148.5          PSCBE2   = 1E-06
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 7.049416
+BETA0   = 21.5673        KT1      = -0.2966189     LKT1     = 7.117821E-09
+WKT1    = -9.436516E-09  PKT1     = 1.002915E-14   KT2      = -0.03003805
+LKT2    = 1.07473E-09    WKT2     = -1.389639E-09  PKT2     = 1.789791E-15
+AT      = 20000          UTE      = -1.391595      LUTE     = 1.314454E-07
+WUTE    = 9.113693E-08   PUTE     = -7.710764E-14  UA1      = 2.04E-09
+UB1     = -2.342879E-18  LUB1     = 2.021821E-25   WUB1     = -2.954335E-26
+PUB1    = 1.371063E-31   UC1      = -2.217535E-11  LUC1     = 2.351995E-17
+WUC1    = -5.850065E-17  PUC1     = 4.490506E-23   KT1L     = 0
+PRT     = 0              CJ       = cjn3           PB       = 0.7076023
+MJ      = 0.3259624      CJSW     = cjswn3         PBSW     = 0.7076023
+MJSW    = 0.1513672      CJSWG    = cjswgn3        PBSWG    = 0.7076023
+MJSWG   = 0.3513672      CGDO     = cgon3          CGSO     = cgon3
+TCJ     = 0.0009923959   TCJSW    = 0.0005019466     TCJSWG   = 0.0005019466   TPB      = 0.001687207
+TPBSW   = 0.001687207    TPBSWG  = 0.001687207    JS       = 7.93E-06       JSW      = 7E-11
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              LLC      = -0.0165                )


.MODEL nch3.5            NMOS   (                   LMIN     = '5E-07-dxl3'
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = '1.2E-06-dxl3' WMIN     = '1.28E-06-dxw3'  WMAX   = '1.008E-05-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.7883273+dvthn3' LVTH0    = 1.430142E-08   WVTH0    = -2.829494E-08
+PVTH0   = 1.127853E-14   K1       = 0.8740014      LK1      = 5.263398E-08
+WK1     = -1.430527E-08  PK1      = -1.454993E-14  K2       = 0.02577455
+LK2     = -2.809138E-08  WK2      = 8.062049E-09   PK2      = 7.706492E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 94142.86       LVSAT    = -0.001257143
+UA      = -5.525029E-10  LUA      = -1.409444E-16  WUA      = 2.050277E-17
+PUA     = -1.369192E-23  UB       = 2.264117E-18   LUB      = 1.594418E-25
+WUB     = -4.253539E-25  PUB      = -5.083429E-32  UC       = 8.841382E-11
+LUC     = 3.082442E-17   WUC      = -1.638796E-17  PUC      = -1.184848E-23
+RDSW    = 545            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.04164665     LU0      = 1.189535E-09
+WU0     = -4.660346E-09  PU0      = 4.356904E-16   A0       = 0.5084204
+LA0     = 7.615436E-08   WA0      = -8.135503E-08  PA0      = 4.529623E-14
+KETA    = 0.003436721    LKETA    = -1.540626E-08  WKETA    = -3.612217E-09
+PKETA   = 3.416723E-15   A1       = 0              A2       = 0.99
+AGS     = 0.04285714     LAGS     = -2.514286E-08  B0       = 0
+B1      = 0              VOFF     = -0.1178821     LVOFF    = 3.155888E-09
+WVOFF   = -2.286241E-09  PVOFF    = 5.260768E-15   NFACTOR  = 1
+CIT     = 0.0005269716   LCIT     = -8.921331E-12  WCIT     = -1.39722E-13
+PCIT    = 1.681757E-18   CDSC     = 0              CDSCB    = 0
+CDSCD   = 0              ETA0     = -0.0001984287  LETA0    = 2.793714E-10
+WETA0   = -8.731711E-11  PETA0    = 3.492684E-17   ETAB     = 0.0001984287
+LETAB   = -2.793714E-10  WETAB    = 8.731711E-11   PETAB    = -3.492684E-17
+DSUB    = 0              PCLM     = 0.6757056      LPCLM    = 7.598389E-09
+WPCLM   = -7.358997E-08  PPCLM    = 1.270961E-13   PDIBLC1  = 1E-06
+PDIBLC2 = 0.001          PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 3.028572E+08   LPSCBE1  = 18.85714       PSCBE2   = 1E-06
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 7.049416
+BETA0   = 21.5673        KT1      = -0.3074853     LKT1     = 1.907084E-08
+WKT1    = 1.594053E-08   PKT1     = -1.78856E-14   KT2      = -0.03303095
+LKT2    = 4.36692E-09    WKT2     = 4.228818E-09   PKT2     = -4.390511E-15
+AT      = 20000          UTE      = -1.401053      LUTE     = 1.418483E-07
+WUTE    = 1.68006E-07    PUTE     = -1.616636E-13  UA1      = 2.04E-09
+UB1     = -2.742255E-18  LUB1     = 6.414957E-25   WUB1     = 6.359434E-25
+PUB1    = -5.949291E-31  UC1      = -7.916944E-11  LUC1     = 8.621345E-17
+WUC1    = 4.196188E-17   PUC1     = -6.560372E-23  KT1L     = 0
+PRT     = 0              CJ       = cjn3           PB       = 0.7076023
+MJ      = 0.3259624      CJSW     = cjswn3         PBSW     = 0.7076023
+MJSW    = 0.1513672      CJSWG    = cjswgn3        PBSWG    = 0.7076023
+MJSWG   = 0.3513672      CGDO     = cgon3          CGSO     = cgon3
+TCJ     = 0.0009923959   TCJSW    = 0.0005019466     TCJSWG   = 0.0005019466   TPB      = 0.001687207
+TPBSW   = 0.001687207    TPBSWG  = 0.001687207    JS       = 7.93E-06       JSW      = 7E-11
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              LLC     = -0.0165                  )


.MODEL nch3.6            NMOS   (                    LMIN     = 3.5E-07
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = '5E-07-dxl3'   WMIN     = '1.28E-06-dxw3' WMAX    = '1.008E-05-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.8654908+dvthn3' LVTH0    = -1.656396E-08  WVTH0    = 1.422681E-09
+PVTH0   = -6.085174E-16  K1       = 0.7481822      LK1      = 1.029616E-07
+WK1     = -1.008557E-07  PK1      = 2.007025E-14   K2       = 0.189703
+LK2     = -9.366277E-08  WK2      = 8.466009E-09   PK2      = 7.544907E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 93128.79       LVSAT    = -0.0008515152
+WVSAT   = -0.004630455   PVSAT    = 1.852182E-09   UA       = -6.665338E-10
+LUA     = -9.533202E-17  WUA      = -1.002899E-15  PUA      = 3.95669E-22
+UB      = 2.115918E-18   LUB      = 2.187213E-25   WUB      = 5.45836E-25
+PUB     = -4.393103E-31  UC       = 2.631281E-10   LUC      = -3.906129E-17
+WUC     = -1.204542E-16  PUC      = 2.977803E-23   RDSW     = 545
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.04367778     LU0      = 3.770848E-10   WU0      = -1.023911E-08
+PU0     = 2.667197E-15   A0       = 0.8783571      LA0      = -7.18203E-08
+WA0     = 1.114288E-07   PA0      = -3.181727E-14  KETA     = -0.05343806
+LKETA   = 7.343654E-09   WKETA    = -4.741592E-08  PKETA    = 2.09382E-14
+A1      = 0              A2       = 0.99           AGS      = -0.02
+B0      = 0              B1       = 0              VOFF     = -0.1005511
+LVOFF   = -3.776537E-09  WVOFF    = -3.980715E-09  PVOFF    = 5.938557E-15
+NFACTOR = 1              CIT      = 0.0004879227   LCIT     = 6.698259E-12
+WCIT    = 3.262776E-11   PCIT     = -1.142524E-17  CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = -0.001166667
+LETA0   = 6.666667E-10   ETAB     = 0.003782197    LETAB    = -1.712879E-09
+WETAB   = -1.157614E-09  PETAB    = 4.630456E-16   DSUB     = 0
+PCLM    = -0.2016089     LPCLM    = 3.585241E-07   WPCLM    = 5.857318E-07
+PPCLM   = -1.366326E-13  PDIBLC1  = 1E-06          PDIBLC2  = -0.01135985
+LPDIBLC2= 4.94394E-09    WPDIBLC2 = 6.945683E-09   PPDIBLC2 = -2.778273E-15
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 3.5E+08
+PSCBE2  = 1E-06          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 7.049416       BETA0    = 21.5673        KT1      = -0.253569
+LKT1    = -2.495687E-09  WKT1     = -1.527961E-07  PKT1     = 4.960905E-14
+KT2     = -0.01791622    LKT2     = -1.67897E-09   WKT2     = -4.085712E-10
+PKT2    = -2.535555E-15  AT       = 20000          UTE      = -1.026062
+LUTE    = -8.147821E-09  WUTE     = 2.066628E-07   PUTE     = -1.771264E-13
+UA1     = 2.04E-09       UB1      = -1.546182E-18  LUB1     = 1.630666E-25
+WUB1    = -5.694543E-25  PUB1     = -1.1277E-31    UC1      = 1.003715E-10
+LUC1    = 1.439706E-17   WUC1     = -9.627236E-17  PUC1     = -1.031002E-23
+KT1L    = 0              PRT      = 0              CJ       = cjn3
+PB      = 0.7076023      MJ       = 0.3259624      CJSW     = cjswn3
+PBSW    = 0.7076023      MJSW     = 0.1513672      CJSWG    = cjswgn3
+PBSWG   = 0.7076023      MJSWG    = 0.3513672      CGDO     = cgon3
+CGSO    = cgon3          TCJ      = 0.0009923959   TCJSW    = 0.0005019466     TCJSWG   = 0.0005019466
+TPB     = 0.001687207    TPBSW    = 0.001687207     TPBSWG   = 0.001687207    JS       = 7.93E-06
+JSW     = 7E-11          N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+LLC     = -0.0165          )


.MODEL nch3.7            NMOS   (                   LMIN     = '1.2E-06-dxl3'
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = 2.1E-05        WMIN     = '6E-07-dxw3'   WMAX     = '1.28E-06-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.7406393+dvthn3' LVTH0    = 6.144541E-08   WVTH0    = -6.285217E-09
+PVTH0   = -6.450512E-15  K1       = 0.8542737      LK1      = 5.181783E-08
+WK1     = 2.282768E-09   PK1      = -5.326427E-15  K2       = 0.0360122
+LK2     = -2.693281E-08  WK2      = -1.139535E-10  PK2      = 1.547693E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 100875         LVSAT    = -0.008662499
+UA      = -6.727692E-10  LUA      = -8.861249E-18  WUA      = 9.314717E-18
+PUA     = -1.129144E-24  UB       = 2.203694E-18   LUB      = -4.141939E-26
+WUB     = -1.316921E-25  PUB      = -4.772393E-32  UC       = 9.450803E-11
+LUC     = 1.650555E-17   WUC      = -9.146613E-18  PUC      = -1.052334E-23
+RDSW    = 545            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.03726697     LU0      = 1.863355E-09
+WU0     = 7.49579E-10    PU0      = -4.597551E-16  A0       = 0.6178071
+LA0     = -8.566931E-08  WA0      = 2.421956E-08   PA0      = -2.020785E-14
+KETA    = 0.01342164     LKETA    = -3.195836E-08  WKETA    = -7.668539E-10
+PKETA   = 7.080628E-15   A1       = 0              A2       = 0.99
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1261087     LVOFF    = 1.627283E-08   WVOFF    = -1.267467E-09
+PVOFF   = -8.224553E-16  NFACTOR  = 1              CIT      = 0.0001048089
+LCIT    = 4.706867E-10   WCIT     = 2.155632E-10   PCIT     = -2.541708E-16
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 1E-05          ETAB     = -1E-05         DSUB     = 0
+PCLM    = 0.4774809      LPCLM    = 2.229392E-07   WPCLM    = -5.619185E-09
+PPCLM   = 5.562985E-14   PDIBLC1  = 1E-06          PDIBLC2  = 0.0004375
+LPDIBLC2= 6.187499E-10   PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 1.85E+08       LPSCBE1  = 148.5          PSCBE2   = 1E-06
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 7.049416
+BETA0   = 21.5673        KT1      = -0.3109329     LKT1     = 2.702848E-08
+WKT1    = 8.026566E-09   PKT1     = -1.426186E-14  KT2      = -0.03294194
+LKT2    = 4.119126E-09   WKT2     = 2.15311E-09    PKT2     = -1.924373E-15
+AT      = 20000          UTE      = -1.352228      LUTE     = 1.035887E-07
+WUTE    = 4.310871E-08   PUTE     = -4.312251E-14  UA1      = 2.04E-09
+UB1     = -2.346215E-18  LUB1     = 3.15301E-25    WUB1     = -2.547322E-26
+PUB1    = -8.987504E-34  UC1      = -5.271665E-11  LUC1     = 4.672277E-17
+WUC1    = -2.124027E-17  PUC1     = 1.659763E-23   KT1L     = 0
+PRT     = 0              CJ       = cjn3           PB       = 0.7076023
+MJ      = 0.3259624      CJSW     = cjswn3         PBSW     = 0.7076023
+MJSW    = 0.1513672      CJSWG    = cjswgn3        PBSWG    = 0.7076023
+MJSWG   = 0.3513672      CGDO     = cgon3          CGSO     = cgon3
+TCJ     = 0.0009923959   TCJSW    = 0.0005019466     TCJSWG   = 0.0005019466   TPB      = 0.001687207
+TPBSW   = 0.001687207    TPBSWG  = 0.001687207    JS       = 7.93E-06       JSW      = 7E-11
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              LLC      = -0.0165              )


.MODEL nch3.8            NMOS   (                   LMIN     = '5E-07-dxl3'
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = '1.2E-06-dxl3' WMIN     = '6E-07-dxw3'   WMAX     = '1.28E-06-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.7689854+dvthn3' LVTH0    = 3.026468E-08   WVTH0    = -4.697823E-09
+PVTH0   = -8.196644E-15  K1       = 0.8861683      LK1      = 1.673369E-08
+WK1     = -2.91489E-08   PK1      = 2.924842E-14   K2       = 0.02180065
+LK2     = -1.130009E-08  WK2      = 1.29102E-08    PK2      = -1.277887E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 94142.86       LVSAT    = -0.001257143
+UA      = -5.102217E-10  LUA      = -1.876634E-16  WUA      = -3.10803E-17
+PUA     = 4.330535E-23   UB       = 1.982197E-18   LUB      = 2.022277E-25
+WUB     = -8.141091E-26  PUB      = -1.030332E-31  UC       = 8.230983E-11
+LUC     = 2.992356E-17   WUC      = -8.941094E-18  PUC      = -1.074942E-23
+RDSW    = 545            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.03780241     LU0      = 1.274373E-09
+WU0     = 2.96312E-11    PU0      = 3.321875E-16   A0       = 0.4478717
+LA0     = 1.012597E-07   WA0      = -7.485548E-09  PA0      = 1.466777E-14
+KETA    = -0.002142804   LKETA    = -1.483747E-08  WKETA    = 3.194802E-09
+PKETA   = 2.722807E-15   A1       = 0              A2       = 0.99
+AGS     = 0.04285714     LAGS     = -2.514286E-08  B0       = 0
+B1      = 0              VOFF     = -0.1190345     LVOFF    = 8.491217E-09
+WVOFF   = -8.803048E-10  PVOFF    = -1.248333E-15  NFACTOR  = 1
+CIT     = 0.0005450084   LCIT     = -1.353274E-11  WCIT     = -2.214453E-11
+PCIT    = 7.307682E-18   CDSC     = 0              CDSCB    = 0
+CDSCD   = 0              ETA0     = -0.00027       LETA0    = 3.08E-10
+ETAB    = 0.00027        LETAB    = -3.08E-10      DSUB     = 0
+PCLM    = 0.6959662      LPCLM    = -1.739469E-08  WPCLM    = -9.830809E-08
+PPCLM   = 1.575877E-13   PDIBLC1  = 1E-06          PDIBLC2  = 0.001453781
+LPDIBLC2= -4.991595E-10  WPDIBLC2 = -5.536135E-10  PPDIBLC2 = 6.089748E-16
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 3.028572E+08
+LPSCBE1 = 18.85714       PSCBE2   = 1E-06          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 7.049416       BETA0    = 21.5673
+KT1     = -0.2693291     LKT1     = -1.873571E-08  WKT1     = -3.061002E-08
+PKT1    = 2.82384E-14    KT2      = -0.02603787    LKT2     = -3.475346E-09
+WKT2    = -4.302735E-09  PKT2     = 5.177055E-15   AT       = 20000
+UTE     = -1.254761      LUTE     = -3.624948E-09  WUTE     = -1.046972E-08
+PUTE    = 1.581376E-14   UA1      = 2.04E-09       UB1      = -2.198809E-18
+LUB1    = 1.531553E-25   WUB1     = -2.70596E-26   PUB1     = 8.4627E-34
+UC1     = -3.98502E-11   LUC1     = 3.256968E-17   WUC1     = -6.007579E-18
+PUC1    = -1.583315E-25  KT1L     = 0              PRT      = 0
+CJ      = cjn3           PB       = 0.7076023      MJ       = 0.3259624
+CJSW    = cjswn3         PBSW     = 0.7076023      MJSW     = 0.1513672
+CJSWG   = cjswgn3        PBSWG    = 0.7076023      MJSWG    = 0.3513672
+CGDO    = cgon3          CGSO     = cgon3          TCJ      = 0.0009923959
+TCJSW   = 0.0005019466    TCJSWG  = 0.0005019466   TPB      = 0.001687207    TPBSW    = 0.001687207     TPBSWG   = 0.001687207
+JS      = 7.93E-06       JSW      = 7E-11          N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0   = 0             LLC      = -0.0165         )


.MODEL nch3.9            NMOS   (                    LMIN     = 3.5E-07
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = '5E-07-dxl3'   WMIN     = '6E-07-dxw3'   WMAX     = '1.28E-06-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.9132374+dvthn3' LVTH0    = -2.743611E-08  WVTH0    = -5.68282E-08
+PVTH0   = 1.26555E-14    K1       = 0.5408618      LK1      = 1.548563E-07
+WK1     = 1.520751E-07   PK1      = -4.324118E-14  K2       = 0.2333659
+LK2     = -9.59262E-08   WK2      = -4.480268E-08  PK2      = 1.030628E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 91980.39       LVSAT    = -0.0003921567
+WVSAT   = -0.003229412   PVSAT    = 1.291765E-09   UA       = -1.799389E-09
+LUA     = 3.280035E-16   WUA      = 3.791841E-16   PUA      = -1.208004E-22
+UB      = 2.599297E-18   LUB      = -4.461244E-26  WUB      = -4.38864E-26
+PUB     = -1.180431E-31  UC       = 1.619963E-10   LUC      = -1.951027E-18
+WUC     = 2.926589E-18   PUC      = -1.549649E-23  RDSW     = 545
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.03507218     LU0      = 2.366464E-09   WU0      = 2.59715E-10
+PU0     = 2.40154E-16    A0       = 0.7772963      LA0      = -3.051018E-08
+WA0     = 2.34723E-07    PA0      = -8.221565E-14  KETA     = -0.1263061
+LKETA   = 3.482785E-08   WKETA    = 4.148313E-08   PKETA    = -1.259252E-14
+A1      = 0              A2       = 0.99           AGS      = -0.02
+B0      = 0              B1       = 0              VOFF     = -0.09579701
+LVOFF   = -8.037886E-10  WVOFF    = -9.78065E-09   PVOFF    = 2.311804E-15
+NFACTOR = 1              CIT      = 0.0005231374   LCIT     = -4.78435E-12
+WCIT    = -1.03342E-11   PCIT     = 2.583549E-18   CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = -0.001166667
+LETA0   = 6.666667E-10   ETAB     = 0.002833334    LETAB    = -1.333333E-09
+DSUB    = 0              PCLM     = -0.1290468     LPCLM    = 3.126105E-07
+WPCLM   = 4.972059E-07   PPCLM    = -8.061792E-14  PDIBLC1  = 1E-06
+PDIBLC2 = -0.007784314   LPDIBLC2 = 3.196078E-09   WPDIBLC2 = 2.58353E-09
+PPDIBLC2= -6.458823E-16  PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 3.5E+08        PSCBE2   = 1E-06          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 7.049416       BETA0    = 21.5673
+KT1     = -0.5361856     LKT1     = 8.800688E-08   WKT1     = 1.919962E-07
+PKT1    = -6.080408E-14  KT2      = -0.03321741    LKT2     = -6.035301E-10
+WKT2    = 1.825889E-08   PKT2     = -3.847593E-15  AT       = 33235.29
+LAT     = -0.005294117   WAT      = -0.01614706    PAT      = 6.458824E-09
+UTE     = -0.7501735     LUTE     = -2.0546E-07    WUTE     = -1.299215E-07
+PUTE    = 6.359447E-14   UA1      = 1.82875E-09    LUA1     = 8.449981E-17
+WUA1    = 2.577245E-16   PUA1     = -1.030898E-22  UB1      = -1.524954E-18
+LUB1    = -1.16387E-25   WUB1     = -5.953524E-25  PUB1     = 2.281634E-31
+UC1     = 6.937149E-11   LUC1     = -1.111899E-17  WUC1     = -5.845231E-17
+PUC1    = 2.081956E-23   KT1L     = 0              PRT      = 0
+CJ      = cjn3           PB       = 0.7076023      MJ       = 0.3259624
+CJSW    = cjswn3         PBSW     = 0.7076023      MJSW     = 0.1513672
+CJSWG   = cjswgn3        PBSWG    = 0.7076023      MJSWG    = 0.3513672
+CGDO    = cgon3          CGSO     = cgon3          TCJ      = 0.0009923959
+TCJSW   = 0.0005019466    TCJSWG  = 0.0005019466   TPB      = 0.001687207    TPBSW    = 0.001687207     TPBSWG   = 0.001687207
+JS      = 7.93E-06       JSW      = 7E-11          N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0  = 0              LLC      = -0.0165         )


.MODEL nch3.10           NMOS   (                   LMIN     = '1.2E-06-dxl3'
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = 2.1E-05        WMIN     = 2.2E-07        WMAX     = '6E-07-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.729+dvthn3' LVTH0    = 4.950002E-08   K1       = 0.8626474
+LK1     = 3.543326E-08   WK1      = -2.239048E-09  PK1      = 3.521241E-15
+K2      = 0.03521829     LK2      = -1.693566E-08  WK2      = 3.147626E-10
+PK2     = -3.850769E-15  K3       = 0              DVT0     = 0
+DVT1    = 0              DVT2     = 0              DVT0W    = 0
+DVT1W   = 0              DVT2W    = 0              NLX      = 0
+W0      = 0              K3B      = 0              VSAT     = 100875
+LVSAT   = -0.008662499   UA       = -7.39225E-10   LUA      = 5.742918E-17
+WUA     = 4.520085E-17   PUA      = -3.692598E-23  UB       = 2.067768E-18
+LUB     = -2.751034E-25  WUB      = -5.829179E-26  PUB      = 7.846542E-32
+UC      = 9.626695E-11   LUC      = -1.287506E-17  WUC      = -1.009643E-17
+PUC     = 5.342185E-24   RDSW     = 545            PRWB     = 0
+PRWG    = 0              WR       = 1              U0       = 0.03474721
+LU0     = 3.363222E-10   WU0      = 2.11025E-09    PU0      = 3.648424E-16
+A0      = 0.6658016      LA0      = -4.311186E-08  WA0      = -1.697458E-09
+PA0     = -4.318888E-14  KETA     = 0.01506696     LKETA    = -1.286948E-08
+WKETA   = -1.655327E-09  PKETA    = -3.227371E-15  A1       = 0
+A2      = 0.99           AGS      = 0.02           B0       = 0
+B1      = 0              VOFF     = -0.1294947     LVOFF    = 2.095355E-08
+WVOFF   = 5.609493E-10   PVOFF    = -3.350047E-15  NFACTOR  = 1
+CIT     = 0.000504       CDSC     = 0              CDSCB    = 0
+CDSCD   = 0              ETA0     = 1E-05          ETAB     = -1E-05
+DSUB    = 0              PCLM     = 0.4708746      LPCLM    = 2.883417E-07
+WPCLM   = -2.05177E-09   PPCLM    = 2.031253E-14   PDIBLC1  = 1E-06
+PDIBLC2 = 0.0004375      LPDIBLC2 = 6.187499E-10   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 1.85E+08       LPSCBE1  = 148.5
+PSCBE2  = 1E-06          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 7.049416       BETA0    = 21.5673        KT1      = -0.295298
+LKT1    = -1.650355E-08  WKT1     = -4.162704E-10  PKT1     = 9.245442E-15
+KT2     = -0.02745233    LKT2     = -2.577811E-09  WKT2     = -8.1128E-10
+PKT2    = 1.691974E-15   AT       = 20000          UTE      = -1.245635
+LUTE    = -2.417547E-08  WUTE     = -1.44516E-08   PUTE     = 2.587016E-14
+UA1     = 2.04E-09       UB1      = -2.213691E-18  LUB1     = 1.849608E-25
+WUB1    = -9.703607E-26  PUB1     = 6.948495E-32   UC1      = -6.592916E-11
+LUC1    = 7.075916E-17   WUC1     = -1.410552E-17  PUC1     = 3.617977E-24
+KT1L    = 0              PRT      = 0              CJ       = cjn3
+PB      = 0.7076023      MJ       = 0.3259624      CJSW     = cjswn3
+PBSW    = 0.7076023      MJSW     = 0.1513672      CJSWG    = cjswgn3
+PBSWG   = 0.7076023      MJSWG    = 0.3513672      CGDO     = cgon3
+CGSO    = cgon3          TCJ      = 0.0009923959   TCJSW    = 0.0005019466     TCJSWG   = 0.0005019466
+TPB     = 0.001687207    TPBSW    = 0.001687207     TPBSWG   = 0.001687207    JS       = 7.93E-06
+JSW     = 7E-11          N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+LLC     = -0.0165          )


.MODEL nch3.11           NMOS   (                   LMIN     = '5E-07-dxl3'
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = '1.2E-06-dxl3' WMIN     = 2.2E-07        WMAX     = '6E-07-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.7602858+dvthn3' LVTH0    = 1.508571E-08   K1       = 0.7846072
+LK1     = 1.212774E-07   WK1      = 2.56941E-08    PK1      = -2.720521E-14
+K2      = 0.061295       LK2      = -4.562004E-08  WK2      = -8.416753E-09
+PK2     = 5.753899E-15   K3       = 0              DVT0     = 0
+DVT1    = 0              DVT2     = 0              DVT0W    = 0
+DVT1W   = 0              DVT2W    = 0              NLX      = 0
+W0      = 0              K3B      = 0              VSAT     = 94142.86
+LVSAT   = -0.001257143   UA       = -5.93494E-10   LUA      = -1.028748E-16
+WUA     = 1.388678E-17   PUA      = -2.480506E-24  UB       = 1.624129E-18
+LUB     = 2.128987E-25   WUB      = 1.119455E-25   PUB      = -1.087956E-31
+UC      = 4.957017E-11   LUC      = 3.849138E-17   WUC      = 8.738324E-18
+PUC     = -1.537604E-23  RDSW     = 545            PRWB     = 0
+PRWG    = 0              WR       = 1              U0       = 0.03231074
+LU0     = 3.016439E-09   WU0      = 2.995133E-09   PU0      = -6.08528E-16
+A0      = 0.4760925      LA0      = 1.655681E-07   WA0      = -2.272483E-08
+PA0     = -2.005877E-14  KETA     = 0.02182036     LKETA    = -2.029821E-08
+WKETA   = -9.745306E-09  PKETA    = 5.671606E-15   A1       = 0
+A2      = 0.99           AGS      = 0.04285714     LAGS     = -2.514286E-08
+B0      = 0              B1       = 0              VOFF     = -0.110812
+LVOFF   = 4.025578E-10   WVOFF    = -5.320496E-09  PVOFF    = 3.119543E-15
+NFACTOR = 1              CIT      = 0.000539991    LCIT     = -3.959006E-11
+WCIT    = -1.943513E-11  PCIT     = 2.137864E-17   CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = -0.00027
+LETA0   = 3.08E-10       ETAB     = 0.00027        LETAB    = -3.08E-10
+DSUB    = 0              PCLM     = 0.6036025      LPCLM    = 1.42341E-07
+WPCLM   = -4.843162E-08  PPCLM    = 7.133036E-14   PDIBLC1  = 1E-06
+PDIBLC2 = 0.0004285714   LPDIBLC2 = 6.285714E-10   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 3.028572E+08   LPSCBE1  = 18.85714
+PSCBE2  = 1E-06          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 7.049416       BETA0    = 21.5673        KT1      = -0.3535531
+LKT1    = 4.757709E-08   WKT1     = 1.487097E-08   PKT1     = -7.57052E-15
+KT2     = -0.03701827    LKT2     = 7.944719E-09   WKT2     = 1.626678E-09
+PKT2    = -9.897803E-16  AT       = 20000          UTE      = -1.350212
+LUTE    = 9.085895E-08   WUTE     = 4.107359E-08   PUTE     = -3.520755E-14
+UA1     = 2.04E-09       UB1      = -2.148257E-18  LUB1     = 1.129834E-25
+WUB1    = -5.435801E-26  PUB1     = 2.253908E-32   UC1      = -1.247552E-11
+LUC1    = 1.196017E-17   WUC1     = -2.078991E-17  PUC1     = 1.097081E-23
+KT1L    = 0              PRT      = 0              CJ       = cjn3
+PB      = 0.7076023      MJ       = 0.3259624      CJSW     = cjswn3
+PBSW    = 0.7076023      MJSW     = 0.1513672      CJSWG    = cjswgn3
+PBSWG   = 0.7076023      MJSWG    = 0.3513672      CGDO     = cgon3
+CGSO    = cgon3          TCJ      = 0.0009923959   TCJSW    = 0.0005019466     TCJSWG   = 0.0005019466
+TPB     = 0.001687207    TPBSW    = 0.001687207     TPBSWG   = 0.001687207    JS       = 7.93E-06
+JSW     = 7E-11          N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+LLC     = -0.0165          )


.MODEL nch3.12           NMOS   (                   LMIN     = 3.5E-07
+NOIMOD  = 3              EF       = 0.907          AF       = 0.9065         KF       = 8.704E-29
+LMAX    = '5E-07-dxl3'   WMIN     = 2.2E-07        WMAX     = '6E-07-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxn3          XJ       = 1.7E-07        NCH      = 5.26E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 4E-08          LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifn3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.808+dvthn3' LVTH0    = -3.999988E-09  K1       = 1.017662
+LK1     = 2.805551E-08   WK1      = -1.05397E-07   PK1      = 2.523122E-14
+K2      = 0.1146846      LK2      = -6.697589E-08  WK2      = 1.928521E-08
+PK2     = -5.326886E-15  K3       = 0              DVT0     = 0
+DVT1    = 0              DVT2     = 0              DVT0W    = 0
+DVT1W   = 0              DVT2W    = 0              NLX      = 0
+W0      = 0              K3B      = 0              VSAT     = 92182.8
+LVSAT   = -0.0004731185  WVSAT    = -0.00333871    PVSAT    = 1.335484E-09
+UA      = -1.506922E-10  LUA      = -2.799955E-16  WUA      = -5.111123E-16
+PUA     = 2.075191E-22   UB       = 1.452744E-18   LUB      = 2.81453E-25
+WUB     = 5.752526E-25   PUB      = -2.941184E-31  UC       = 1.836934E-10
+LUC     = -1.51579E-17   WUC      = -8.789836E-18  PUC      = -8.364778E-24
+RDSW    = 545            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.05033468     LU0      = -4.193137E-09
+WU0     = -7.982036E-09  PU0      = 3.782339E-15   A0       = 1.100795
+LA0     = -8.431294E-08  WA0      = 6.003363E-08   PA0      = -5.316214E-14
+KETA    = -0.08461745    LKETA    = 2.227691E-08   WKETA    = 1.897124E-08
+PKETA   = -5.81501E-15   A1       = 0              A2       = 0.99
+AGS     = 0.004731186    LAGS     = -9.892474E-09  WAGS     = -1.335484E-08
+PAGS    = 5.341936E-15   B0       = 0              B1       = 0
+VOFF    = -0.1261481     LVOFF    = 6.537034E-09   WVOFF    = 6.608962E-09
+PVOFF   = -1.65224E-15   NFACTOR  = 1              CIT      = 0.0003360421
+LCIT    = 4.198947E-11   WCIT     = 9.069727E-11   PCIT     = -2.267432E-17
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -0.001166667   LETA0    = 6.666667E-10   ETAB     = 0.002833333
+LETAB   = -1.333333E-09  DSUB     = 0              PCLM     = 0.6313016
+LPCLM   = 1.312614E-07   WPCLM    = 8.661782E-08   PPCLM    = 1.731058E-14
+PDIBLC1 = 1E-06          PDIBLC2  = -0.003         LPDIBLC2 = 2E-09
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 3.5E+08
+PSCBE2  = 1E-06          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 7.049416       BETA0    = 21.5673        KT1      = -0.1488888
+LKT1    = -3.428864E-08  WKT1     = -1.714408E-08  PKT1     = 5.235498E-15
+KT2     = 0.003193967    LKT2     = -8.140173E-09  WKT2     = -1.403258E-09
+PKT2    = 2.221941E-16   AT       = 9516.13        LAT      = 0.004193548
+WAT     = -0.00333871    PAT      = 1.335484E-09   UTE      = -0.966265
+LUTE    = -6.271973E-08  WUTE     = -1.323212E-08  PUTE     = -1.348526E-14
+UA1     = 1.410231E-09   LUA1     = 2.519074E-16   WUA1     = 4.837248E-16
+PUA1    = -1.934899E-22  UB1      = -9.210595E-19  LUB1     = -3.778954E-25
+WUB1    = -9.214554E-25  PUB1     = 3.69378E-31    UC1      = 4.875426E-11
+LUC1    = -1.253173E-17  WUC1     = -4.7319E-17    PUC1     = 2.158244E-23
+KT1L    = 0              PRT      = 0              CJ       = cjn3
+PB      = 0.7076023      MJ       = 0.3259624      CJSW     = cjswn3
+PBSW    = 0.7076023      MJSW     = 0.1513672      CJSWG    = cjswgn3
+PBSWG   = 0.7076023      MJSWG    = 0.3513672      CGDO     = cgon3
+CGSO    = cgon3          TCJ      = 0.0009923959   TCJSW    = 0.0005019466     TCJSWG   = 0.0005019466
+TPB     = 0.001687207    TPBSW    = 0.001687207     TPBSWG   = 0.001687207    JS       = 7.93E-06
+JSW     = 7E-11          N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+LLC     = -0.0165          )


.MODEL pch3.1            PMOS   (                   LMIN     = '1.2E-06-dxl3'
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = 2.1E-05        WMIN     = '1.004E-05-dxw3'  WMAX     = 0.000101
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.7002539+dvthp3' LVTH0    = -1.919726E-08  WVTH0    = 3.591137E-08
+PVTH0   = 8.306469E-14   K1       = 0.8495906      LK1      = 1.78338E-08
+K2      = 0.07384637     LK2      = -6.087654E-09  K3       = 0
+DVT0    = 0              DVT1     = 0              DVT2     = 0
+DVT0W   = 0              DVT1W    = 0              DVT2W    = 0
+NLX     = 0              W0       = 0              K3B      = 0
+VSAT    = 153784.1       LVSAT    = -0.03750033    UA       = 1.615505E-09
+LUA     = -2.618972E-17  WUA      = 7.454936E-16   PUA      = -8.274978E-22
+UB      = 2.680371E-19   LUB      = 7.671914E-26   WUB      = 4.874356E-27
+PUB     = -5.410513E-33  UC       = -9.426324E-11  LUC      = 2.628488E-17
+WUC     = -1.393919E-16  PUC      = -6.836683E-23  RDSW     = 900
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.01324276     LU0      = -1.535924E-09  WU0      = -9.448248E-11
+PU0     = 1.048759E-16   A0       = 0.9807275      LA0      = -8.056325E-08
+KETA    = 0.0207524      LKETA    = -1.162278E-08  A1       = 0
+A2      = 0.99           AGS      = 0.02           B0       = 0
+B1      = 0              VOFF     = -0.1121799     LVOFF    = 2.535671E-09
+WVOFF   = 2.793362E-09   PVOFF    = -2.768221E-14  NFACTOR  = 1
+CIT     = 0.0004476298   LCIT     = 6.03509E-11    CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = 1E-05
+ETAB    = -1E-05         DSUB     = 0              PCLM     = 0.4845122
+LPCLM   = 1.534836E-07   PDIBLC1  = 1E-06          PDIBLC2  = 1E-05
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 1.873864E+08
+LPSCBE1 = 125.0011       PSCBE2   = 5E-07          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 0.143217238    BETA0    = 16.10832
+KT1     = -0.2986702     LKT1     = -3.917211E-09  WKT1     = 8.215068E-08
+PKT1    = -4.70297E-14   KT2      = -0.02675693    LKT2     = 2.22723E-09
+WKT2    = 8.907755E-09   PKT2     = -2.487828E-14  AT       = -50000
+UTE     = -0.753471      LUTE     = 1.179202E-07   WUTE     = -5.510299E-07
+PUTE    = 8.305973E-14   UA1      = 2.031E-09      UB1      = -2.275932E-18
+LUB1    = 8.909157E-26   WUB1     = -3.600904E-24  PUB1     = 4.787674E-31
+UC1     = 7.759261E-12   LUC1     = 3.206287E-17   WUC1     = -5.867228E-18
+PUC1    = -9.798401E-23  KT1L     = 0              PRT      = 0
+CJ      = cjp3           PB       = 0.8049122      MJ       = 0.3954951
+CJSW    = cjswp3         PBSW     = 0.8049122      MJSW     = 0.2573111
+CJSWG   = cjswgp3        PBSWG    = 0.8049122      MJSWG    = 0.2573111
+CGDO    = cgop3          CGSO     = cgop3          TCJ      = 0.0009940197
+TCJSW   = 0.0006908749    TCJSWG  = 0.0006908749   TPB      = 0.001625007    TPBSW    = 0.001625007    TPBSWG   = 0.001625007
+JS      = 3.102E-06      JSW      = 2.8E-11        N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0   = 0              LLC     = -0.0165         )


.MODEL pch3.2            PMOS   (                   LMIN     = '5E-07-dxl3'
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = '1.2E-06-dxl3' WMIN     = '1.004E-05-dxw3'  WMAX     = 0.000101
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.7188592+dvthp3' LVTH0    = 1.454569E-09   WVTH0    = 1.21713E-07
+PVTH0   = -1.217505E-14  K1       = 0.8549396      LK1      = 1.189636E-08
+WK1     = -7.410818E-09  PK1      = 8.225988E-15   K2       = 0.07341911
+LK2     = -5.613394E-09  WK2      = 2.179005E-09   PK2      = -2.418701E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 125857.2       LVSAT    = -0.006501434
+UA      = 2.140223E-09   LUA      = -6.086267E-16  WUA      = -7.96105E-16
+PUA     = 8.836769E-22   UB       = -7.129454E-21  LUB      = 3.82154E-25
+WUB     = 1.074003E-24   PUB      = -1.192143E-30  UC       = -1.137223E-10
+LUC     = 4.788439E-17   WUC      = -1.568522E-16  PUC      = -4.898588E-23
+RDSW    = 900            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01328317     LU0      = -1.580777E-09
+WU0     = -2.618766E-09  PU0      = 2.906831E-15   A0       = 0.9244761
+LA0     = -1.812418E-08  WA0      = -3.701309E-07  PA0      = 4.108454E-13
+KETA    = 0.02045372     LKETA    = -1.129124E-08  WKETA    = -5.245644E-10
+PKETA   = 5.822689E-16   A1       = 0              A2       = 0.99
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1134681     LVOFF    = 3.965551E-09   WVOFF    = -3.411959E-08
+PVOFF   = 1.329116E-14   NFACTOR  = 1              CIT      = 0.0005022595
+LCIT    = -2.880878E-13  WCIT     = -2.594607E-11  PCIT     = 2.880013E-17
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -4.27143E-05   LETA0    = 5.851286E-11   ETAB     = 4.27143E-05
+LETAB   = -5.851286E-11  DSUB     = 0              PCLM     = 0.6081869
+LPCLM   = 1.620478E-08   WPCLM    = -2.160213E-07  PPCLM    = 2.397836E-13
+PDIBLC1 = 1E-06          PDIBLC2  = -0.0005698573  LPDIBLC2 = 6.436415E-10
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 2.707143E+08
+LPSCBE1 = 32.50714       PSCBE2   = 5E-07          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 0.143217238    BETA0    = 16.10832
+KT1     = -0.3036847     LKT1     = 1.648807E-09   WKT1     = 7.443872E-08
+PKT1    = -3.846941E-14  KT2      = -0.02365481    LKT2     = -1.216114E-09
+WKT2    = -1.071819E-08  PKT2     = -3.093476E-15  AT       = -50000
+UTE     = -0.6638418     LUTE     = 1.84318E-08    WUTE     = -8.070108E-07
+PUTE    = 3.671984E-13   UA1      = 2.031E-09      UB1      = -2.245602E-18
+LUB1    = 5.542465E-26   WUB1     = -5.274253E-24  PUB1     = 2.336185E-30
+UC1     = 4.522943E-11   LUC1     = -9.529012E-18  WUC1     = -1.811905E-16
+PUC1    = 9.662475E-23   KT1L     = 0              PRT      = 0
+CJ      = cjp3           PB       = 0.8049122      MJ       = 0.3954951
+CJSW    = cjswp3         PBSW     = 0.8049122      MJSW     = 0.2573111
+CJSWG   = cjswgp3        PBSWG    = 0.8049122      MJSWG    = 0.2573111
+CGDO    = cgop3          CGSO     = cgop3          TCJ      = 0.0009940197
+TCJSW   = 0.0006908749    TCJSWG  = 0.0006908749   TPB      = 0.001625007    TPBSW    = 0.001625007    TPBSWG   = 0.001625007
+JS      = 3.102E-06      JSW      = 2.8E-11        N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0   = 0             LLC      = -0.0165          )


.MODEL pch3.3            PMOS   (                    LMIN     = 3E-07
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = '5E-07-dxl3'   WMIN     = '1.004E-05-dxw3'   WMAX     = 0.000101
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.742778+dvthp3' LVTH0    = 1.126129E-08   WVTH0    = -2.269821E-07
+PVTH0   = 1.307899E-13   K1       = 0.7934595      LK1      = 3.710321E-08
+WK1     = -2.36273E-07   PK1      = 1.020595E-13   K2       = 0.1087443
+LK2     = -2.009671E-08  WK2      = 2.00312E-07    PK2      = -8.36532E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 128090.3       LVSAT    = -0.00741703
+WVSAT   = -0.07567549    PVSAT    = 3.102694E-08   UA       = 1.224679E-09
+LUA     = -2.332535E-16  WUA      = -3.390562E-17  PUA      = 5.711747E-22
+UB      = -3.19518E-20   LUB      = 3.923312E-25   WUB      = 1.418736E-24
+PUB     = -1.333483E-30  UC       = -1.25976E-10   LUC      = 5.290843E-17
+WUC     = 3.642353E-16   PUC      = -2.626317E-22  RDSW     = 900
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.009404771    LU0      = 9.367195E-12   WU0      = 6.196634E-09
+PU0     = -7.074835E-16  A0       = 1.009167       LA0      = -5.284729E-08
+WA0     = 1.460912E-06   PA0      = -3.398821E-13  KETA     = -0.02429991
+LKETA   = 7.057745E-09   WKETA    = 1.43634E-07    PKETA    = -5.852275E-14
+A1      = 0              A2       = 0.99           AGS      = 0.02
+B0      = 0              B1       = 0              VOFF     = -0.1341474
+LVOFF   = 1.24441E-08    WVOFF    = 9.004226E-08   PVOFF    = -3.76152E-14
+NFACTOR = 1              CIT      = 0.0004451524   LCIT     = 2.312585E-11
+WCIT    = 1.004454E-09   PCIT     = -3.936639E-16  CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = -0.0006236127
+LETA0   = 2.966812E-10   WETA0    = 3.02702E-09    PETA0    = -1.241078E-15
+ETAB    = 0.001528129    LETAB    = -6.675328E-10  WETAB    = -6.810794E-09
+PETAB   = 2.792425E-15   DSUB     = 0              PCLM     = 0.5880852
+LPCLM   = 2.444646E-08   WPCLM    = 8.019048E-07   PPCLM    = -1.775661E-13
+PDIBLC1 = 1E-06          PDIBLC2  = 0.001465267    LPDIBLC2 = -1.907594E-10
+WPDIBLC2= -4.651272E-08  PPDIBLC2 = 1.907021E-14   PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 3.138194E+08   LPSCBE1  = 14.83406
+WPSCBE1 = 151.3509       PPSCBE1  = -6.205388E-05  PSCBE2   = 5E-07
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 0.143217238
+BETA0   = 16.10832       KT1      = -0.3438452     LKT1     = 1.811465E-08
+WKT1    = 9.021878E-08   PKT1     = -4.493923E-14  KT2      = -0.02070433
+LKT2    = -2.425813E-09  WKT2     = -9.925297E-08  PKT2     = 3.320578E-14
+AT      = -50000         UTE      = -0.6557475     LUTE     = 1.511314E-08
+WUTE    = 4.852873E-06   PUTE     = -1.953354E-12  UA1      = 1.874849E-09
+LUA1    = 6.402185E-17   WUA1     = 1.56104E-14    PUA1     = -6.400264E-21
+UB1     = -2.203607E-18  LUB1     = 3.820685E-26   WUB1     = -2.955436E-24
+PUB1    = 1.38547E-30    UC1      = -3.657716E-12  LUC1     = 1.051472E-17
+WUC1    = 5.702285E-16   PUC1     = -2.11457E-22   KT1L     = 0
+PRT     = 0              CJ       = cjp3           PB       = 0.8049122
+MJ      = 0.3954951      CJSW     = cjswp3         PBSW     = 0.8049122
+MJSW    = 0.2573111      CJSWG    = cjswgp3        PBSWG    = 0.8049122
+MJSWG   = 0.2573111      CGDO     = cgop3          CGSO     = cgop3
+TCJ     = 0.0009940197   TCJSW    = 0.0006908749    TCJSWG   = 0.0006908749   TPB      = 0.001625007
+TPBSW   = 0.001625007     TPBSWG  = 0.001625007    JS       = 3.102E-06      JSW      = 2.8E-11
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              LLC     = -0.0165          )


.MODEL pch3.4            PMOS   (                   LMIN     = '1.2E-06-dxl3'
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = 2.1E-05        WMIN     = '1.25E-06-dxw3'  WMAX   = '1.004E-05-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.6973843+dvthp3' LVTH0    = -1.064243E-08  WVTH0    = 7.301034E-09
+PVTH0   = -2.227047E-15  K1       = 0.8484179      LK1      = 1.926063E-08
+WK1     = 1.169194E-08   PK1      = -1.422556E-14  K2       = 0.07413068
+LK2     = -6.409639E-09  WK2      = -2.834594E-09  PK2      = 3.210199E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 153784.1       LVSAT    = -0.03750033
+UA      = 1.69803E-09    LUA      = -1.299964E-16  WUA      = -7.728051E-17
+PUA     = 2.074547E-22   UB       = 2.978617E-19   LUB      = 8.640265E-26
+WUB     = -2.924768E-25  PUB      = -1.019551E-31  UC       = -1.018339E-10
+LUC     = 2.091565E-17   WUC      = -6.391267E-17  PUC      = -1.48356E-23
+RDSW    = 900            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.0133002      LU0      = -1.553775E-09
+WU0     = -6.671325E-10  PU0      = 2.828525E-16   A0       = 0.9774354
+LA0     = -7.758442E-08  WA0      = 3.282189E-08   PA0      = -2.969891E-14
+KETA    = 0.02095419     LKETA    = -1.166661E-08  WKETA    = -2.011852E-09
+PKETA   = 4.370354E-16   A1       = 0              A2       = 0.99
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1118244     LVOFF    = -9.702055E-11  WVOFF    = -7.50668E-10
+PVOFF   = -1.434273E-15  NFACTOR  = 1              CIT      = 0.0004462897
+LCIT    = 6.660675E-11   WCIT     = 1.336093E-11   PCIT     = -6.237083E-17
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 1E-05          ETAB     = -1E-05         DSUB     = 0
+PCLM    = 0.4849731      LPCLM    = 1.489169E-07   WPCLM    = -4.594348E-09
+PPCLM   = 4.552996E-14   PDIBLC1  = 1E-06          PDIBLC2  = 1E-05
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 1.873864E+08
+LPSCBE1 = 125.0011       PSCBE2   = 5E-07          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 0.143217238    BETA0    = 16.10832
+KT1     = -0.2907273     LKT1     = -9.27485E-09   WKT1     = 2.960051E-09
+PKT1    = 6.385969E-15   KT2      = -0.02577542    LKT2     = -3.989765E-10
+WKT2    = -8.778435E-10  PKT2     = 1.305001E-15   AT       = -50000
+UTE     = -0.8212075     LUTE     = 1.260834E-07   WUTE     = 1.24303E-07
+PUTE    = 1.673002E-15   UA1      = 2.031E-09      UB1      = -2.656782E-18
+LUB1    = 1.504547E-25   WUB1     = 1.961678E-25   PUB1     = -1.330226E-31
+UC1     = 2.205836E-12   LUC1     = 2.034624E-17   WUC1     = 4.950046E-17
+PUC1    = 1.883079E-23   KT1L     = 0              PRT      = 0
+CJ      = cjp3           PB       = 0.8049122      MJ       = 0.3954951
+CJSW    = cjswp3         PBSW     = 0.8049122      MJSW     = 0.2573111
+CJSWG   = cjswgp3        PBSWG    = 0.8049122      MJSWG    = 0.2573111
+CGDO    = cgop3          CGSO     = cgop3          TCJ      = 0.0009940197
+TCJSW   = 0.0006908749    TCJSWG  = 0.0006908749   TPB      = 0.001625007    TPBSW    = 0.001625007    TPBSWG   = 0.001625007
+JS      = 3.102E-06      JSW      = 2.8E-11        N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0   = 0              LLC     = -0.0165         )


.MODEL pch3.5            PMOS   (                   LMIN     = '5E-07-dxl3'
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = '1.2E-06-dxl3'  WMIN    = '1.25E-06-dxw3' WMAX     = '1.004E-05-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.7062229+dvthp3' LVTH0    = -8.315608E-10  WVTH0    = -4.270778E-09
+PVTH0   = 1.061766E-14   K1       = 0.8531952      LK1      = 1.395785E-08
+WK1     = 9.981616E-09   PK1      = -1.232709E-14  K2       = 0.07376267
+LK2     = -6.001147E-09  WK2      = -1.246302E-09  PK2      = 1.447195E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 125857.2       LVSAT    = -0.006501434
+UA      = 2.061101E-09   LUA      = -5.330049E-16  WUA      = -7.256245E-18
+PUA     = 1.297278E-22   UB       = 1.272111E-19   LUB      = 2.758248E-25
+WUB     = -2.65373E-25   PUB      = -1.320404E-31  UC       = -1.221303E-10
+LUC     = 4.344465E-17   WUC      = -7.302436E-17  PUC      = -4.721635E-24
+RDSW    = 900            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01306322     LU0      = -1.290725E-09
+WU0     = -4.258277E-10  PU0      = 1.500427E-17   A0       = 0.8886115
+LA0     = 2.101012E-08   WA0      = -1.256126E-08  PA0      = 2.067638E-14
+KETA    = 0.02046689     LKETA    = -1.112571E-08  WKETA    = -6.558525E-10
+PKETA   = -1.068124E-15  A1       = 0              A2       = 0.99
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1170738     LVOFF    = 5.729818E-09   WVOFF    = 1.829783E-09
+PVOFF   = -4.298573E-15  NFACTOR  = 1              CIT      = 0.0005044247
+LCIT    = 2.07693E-12    WCIT     = -4.753252E-11  PCIT     = 5.220899E-18
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -4.27143E-05   LETA0    = 5.851286E-11   ETAB     = 4.27143E-05
+LETAB   = -5.851286E-11  DSUB     = 0              PCLM     = 0.5834919
+LPCLM   = 3.956098E-08   WPCLM    = 3.018742E-08   PPCLM    = 6.922207E-15
+PDIBLC1 = 1E-06          PDIBLC2  = -0.0005698573  LPDIBLC2 = 6.436415E-10
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 2.707143E+08
+LPSCBE1 = 32.50714       PSCBE2   = 5E-07          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 0.143217238    BETA0    = 16.10832
+KT1     = -0.2971405     LKT1     = -2.1562E-09    WKT1     = 9.193795E-09
+PKT1    = -5.334868E-16  KT2      = -0.02473424    LKT2     = -1.554691E-09
+WKT2    = 4.365983E-11   PKT2     = 2.821329E-16   AT       = -50000
+UTE     = -0.755203      LUTE     = 5.281836E-08   WUTE     = 1.038603E-07
+PUTE    = 2.436439E-14   UA1      = 2.031E-09      UB1      = -2.784323E-18
+LUB1    = 2.920252E-25   WUB1     = 9.679837E-26   PUB1     = -2.272243E-32
+UC1     = 1.926205E-11   LUC1     = 1.413834E-18   WUC1     = 7.770427E-17
+PUC1    = -1.247543E-23  KT1L     = 0              PRT      = 0
+CJ      = cjp3           PB       = 0.8049122      MJ       = 0.3954951
+CJSW    = cjswp3         PBSW     = 0.8049122      MJSW     = 0.2573111
+CJSWG   = cjswgp3        PBSWG    = 0.8049122      MJSWG    = 0.2573111
+CGDO    = cgop3          CGSO     = cgop3          TCJ      = 0.0009940197
+TCJSW   = 0.0006908749    TCJSWG  = 0.0006908749   TPB      = 0.001625007    TPBSW    = 0.001625007    TPBSWG   = 0.001625007
+JS      = 3.102E-06      JSW      = 2.8E-11        N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0   = 0              LLC     = -0.0165         )


.MODEL pch3.6            PMOS   (                   LMIN     = 3E-07
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = '5E-07-dxl3'   WMIN     = '1.25E-06-dxw3'  WMAX   = '1.004E-05-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.7794082+dvthp3' LVTH0    = 2.91744E-08    WVTH0    = 1.382205E-07
+PVTH0   = -4.780377E-14  K1       = 0.7703792      LK1      = 4.791238E-08
+WK1     = -6.162721E-09  PK1      = -5.707916E-15  K2       = 0.1315091
+LK2     = -2.967716E-08  WK2      = -2.665298E-08  PK2      = 1.186393E-14
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 119582.7       LVSAT    = -0.003928895
+WVSAT   = 0.009145788    PVSAT    = -3.749772E-09  UA       = 1.141662E-09
+LUA     = -1.560352E-16  WUA      = 7.937682E-16   PUA      = -1.986922E-22
+UB      = 2.525025E-19   LUB      = 2.244554E-25   WUB      = -1.417272E-24
+PUB     = 3.402383E-31   UC       = -7.136963E-11  LUC      = 2.263279E-17
+WUC     = -1.801905E-16  PUC      = 3.921649E-23   RDSW     = 900
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.01008642     LU0      = -7.023669E-11  WU0      = -5.993958E-10
+PU0     = 8.616718E-17   A0       = 1.14074        LA0      = -8.236271E-08
+WA0     = 1.491209E-07   PA0      = -4.56133E-14   KETA     = -0.01135291
+LKETA   = 1.920411E-09   WKETA    = 1.455242E-08   PKETA    = -7.303516E-15
+A1      = 0              A2       = 0.99           AGS      = 0.02
+B0      = 0              B1       = 0              VOFF     = -0.1249071
+LVOFF   = 8.941456E-09   WVOFF    = -2.084134E-09  PVOFF    = -2.693866E-15
+NFACTOR = 1              CIT      = 0.0005624254   LCIT     = -2.170337E-11
+WCIT    = -1.647581E-10  PCIT     = 5.328336E-17   CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = -0.0002833068
+LETA0   = 1.571558E-10   WETA0    = -3.658315E-10  PETA0    = 1.499909E-16
+ETAB    = 0.0008787847   LETAB    = -4.013017E-10  WETAB    = -3.368325E-10
+PETAB   = 1.381013E-16   DSUB     = 0              PCLM     = 0.6642304
+LPCLM   = 6.458212E-09   WPCLM    = 4.273733E-08   PPCLM    = 1.77674E-15
+PDIBLC1 = 1E-06          PDIBLC2  = -0.003763823   LPDIBLC2 = 1.953167E-09
+WPDIBLC2= 5.621312E-09   PPDIBLC2 = -2.304738E-15  PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 3.308347E+08   LPSCBE1  = 7.857789
+WPSCBE1 = -18.29158      PPSCBE1  = 7.499546E-06   PSCBE2   = 5E-07
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 0.143217238
+BETA0   = 16.10832       KT1      = -0.3348261     LKT1     = 1.329489E-08
+WKT1    = 2.981252E-10   PKT1     = 3.113737E-15   KT2      = -0.03065495
+LKT2    = 8.728006E-10   WKT2     = -4.528868E-11  PKT2     = 3.186017E-16
+AT      = -50000         UTE      = -0.13083       LUTE     = -2.031745E-07
+WUTE    = -3.805539E-07  PUTE     = 2.229742E-13   UA1      = 3.629814E-09
+LUA1    = -6.555138E-16  WUA1     = -1.886601E-15  PUA1     = 7.735063E-22
+UB1     = -2.563672E-18  LUB1     = 2.015583E-25   WUB1     = 6.344118E-25
+PUB1    = -2.431439E-31  UC1      = 4.85224E-11    LUC1     = -1.058291E-17
+WUC1    = 4.999271E-17   PUC1     = -1.113694E-24  KT1L     = 0
+PRT     = 0              CJ       = cjp3           PB       = 0.8049122
+MJ      = 0.3954951      CJSW     = cjswp3         PBSW     = 0.8049122
+MJSW    = 0.2573111      CJSWG    = cjswgp3        PBSWG    = 0.8049122
+MJSWG   = 0.2573111      CGDO     = cgop3          CGSO     = cgop3
+TCJ     = 0.0009940197   TCJSW    = 0.0006908749    TCJSWG   = 0.0006908749   TPB      = 0.001625007
+TPBSW   = 0.001625007     TPBSWG  = 0.001625007    JS       = 3.102E-06      JSW      = 2.8E-11
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              LLC      = -0.0165                    )


.MODEL pch3.7            PMOS   (                   LMIN     = '1.2E-06-dxl3'
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = 2.1E-05        WMIN     = '5.6E-07-dxw3' WMAX     = '1.25E-06-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.6913373+dvthp3' LVTH0    = -1.780899E-08  WVTH0    = 1.656491E-10
+PVTH0   = 6.229505E-15   K1       = 0.8544281      LK1      = 1.474613E-09
+WK1     = 4.599906E-09   PK1      = 6.761944E-15   K2       = 0.07308947
+LK2     = -8.244109E-10  WK2      = -1.605963E-09  PK2      = -3.380371E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 153784.1       LVSAT    = -0.03750033
+UA      = 2.433433E-09   LUA      = 7.65709E-17    WUA      = -9.450557E-16
+PUA     = -3.629472E-23  UB       = 5E-20          UC       = -1.420792E-10
+LUC     = 1.647117E-17   WUC      = -1.64232E-17   PUC      = -9.591111E-24
+RDSW    = 900            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01528026     LU0      = -1.695105E-09
+WU0     = -3.003604E-09  PU0      = 4.496227E-16   A0       = 0.9523371
+LA0     = -1.395394E-07  WA0      = 6.243793E-08   PA0      = 4.340799E-14
+KETA    = 0.0199098      LKETA    = -1.133909E-08  WKETA    = -7.794653E-10
+PKETA   = 5.055713E-17   A1       = 0              A2       = 0.99
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1128344     LVOFF    = -2.059409E-09  WVOFF    = 4.411647E-10
+PVOFF   = 8.813456E-16   NFACTOR  = 1              CIT      = 0.0004373701
+LCIT    = 1.73009E-11    WCIT     = 2.388599E-11   PCIT     = -4.189925E-18
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 1E-05          ETAB     = -1E-05         DSUB     = 0
+PCLM    = 0.4855583      LPCLM    = 1.431172E-07   WPCLM    = -5.284932E-09
+PPCLM   = 5.237368E-14   PDIBLC1  = 1E-06          PDIBLC2  = 1E-05
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 1.873864E+08
+LPSCBE1 = 125.0011       PSCBE2   = 5E-07          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 0.143217238    BETA0    = 16.10832
+KT1     = -0.2912052     LKT1     = -6.17853E-09   WKT1     = 3.523903E-09
+PKT1    = 2.732311E-15   KT2      = -0.02736462    LKT2     = 1.471901E-09
+WKT2    = 9.974067E-10   PKT2     = -9.026338E-16  AT       = -50000
+UTE     = -0.7909815     LUTE     = 1.470303E-07   WUTE     = 8.863637E-08
+PUTE    = -2.304436E-14  UA1      = 2.031E-09      UB1      = -2.561598E-18
+LUB1    = 4.855629E-26   WUB1     = 8.385015E-26   PUB1     = -1.278251E-32
+UC1     = 4.235901E-11   LUC1     = 2.602498E-17   WUC1     = 2.11971E-18
+PUC1    = 1.212988E-23   KT1L     = 0              PRT      = 0
+CJ      = cjp3           PB       = 0.8049122      MJ       = 0.3954951
+CJSW    = cjswp3         PBSW     = 0.8049122      MJSW     = 0.2573111
+CJSWG   = cjswgp3        PBSWG    = 0.8049122      MJSWG    = 0.2573111
+CGDO    = cgop3          CGSO     = cgop3          TCJ      = 0.0009940197
+TCJSW   = 0.0006908749    TCJSWG  = 0.0006908749   TPB      = 0.001625007    TPBSW    = 0.001625007    TPBSWG   = 0.001625007
+JS      = 3.102E-06      JSW      = 2.8E-11        N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0   = 0             LLC      = -0.0165         )


.MODEL pch3.8            PMOS   (                   LMIN     = '5E-07-dxl3'
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = '1.2E-06-dxl3' WMIN     = '5.6E-07-dxw3'  WMAX     = '1.25E-06-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.723493+dvthp3' LVTH0    = 1.788377E-08   WVTH0    = 1.610793E-08
+PVTH0   = -1.146642E-14  K1       = 0.8617752      LK1      = -6.680662E-09
+WK1     = -1.428007E-10  PK1      = 1.202635E-14   K2       = 0.07514823
+LK2     = -3.109633E-09  WK2      = -2.881261E-09  PK2      = -1.964791E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 125857.2       LVSAT    = -0.006501434
+UA      = 3.15235E-09    LUA      = -7.214267E-16  WUA      = -1.29493E-15
+PUA     = 3.520655E-22   UB       = -2.025564E-19  LUB      = 2.803376E-25
+WUB     = 1.237526E-25   PUB      = -1.373654E-31  UC       = -1.768895E-10
+LUC     = 5.511059E-17   WUC      = -8.408499E-18  PUC      = -1.848744E-23
+RDSW    = 900            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01568054     LU0      = -2.139411E-09
+WU0     = -3.514264E-09  PU0      = 1.016455E-15   A0       = 0.7766607
+LA0     = 5.546133E-08   WA0      = 1.195407E-07   PA0      = -1.997605E-14
+KETA    = 0.02084103     LKETA    = -1.237276E-08  WKETA    = -1.097336E-09
+PKETA   = 4.033962E-16   A1       = 0              A2       = 0.99
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1128435     LVOFF    = -2.049371E-09  WVOFF    = -3.162009E-09
+PVOFF   = 4.880869E-15   NFACTOR  = 1              CIT      = 0.0004466835
+LCIT    = 6.963108E-12   WCIT     = 2.060209E-11   PCIT     = -5.447892E-19
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -4.271431E-05  LETA0    = 5.851287E-11   ETAB     = 4.271431E-05
+LETAB   = -5.851287E-11  DSUB     = 0              PCLM     = 0.5643186
+LPCLM   = 5.569328E-08   WPCLM    = 5.281198E-08   PPCLM    = -1.21139E-14
+PDIBLC1 = 1E-06          PDIBLC2  = -0.0005698575  LPDIBLC2 = 6.436416E-10
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 2.707143E+08
+LPSCBE1 = 32.50714       PSCBE2   = 5E-07          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 0.143217238    BETA0    = 16.10832
+KT1     = -0.2928363     LKT1     = -4.367969E-09  WKT1     = 4.114815E-09
+PKT1    = 2.076399E-15   KT2      = -0.02268223    LKT2     = -3.725555E-09
+WKT2    = -2.377716E-09  PKT2     = 2.843752E-15   AT       = -50000
+UTE     = -0.7338582     LUTE     = 8.362347E-08   WUTE     = 7.867354E-08
+PUTE    = -1.198563E-14  UA1      = 2.031E-09      UB1      = -2.799526E-18
+LUB1    = 3.126563E-25   WUB1     = 1.147372E-25   PUB1     = -4.706711E-32
+UC1     = 7.808395E-11   LUC1     = -1.362969E-17  WUC1     = 8.294437E-18
+PUC1    = 5.275929E-24   KT1L     = 0              PRT      = 0
+CJ      = cjp3           PB       = 0.8049122      MJ       = 0.3954951
+CJSW    = cjswp3         PBSW     = 0.8049122      MJSW     = 0.2573111
+CJSWG   = cjswgp3        PBSWG    = 0.8049122      MJSWG    = 0.2573111
+CGDO    = cgop3          CGSO     = cgop3          TCJ      = 0.0009940197
+TCJSW   = 0.0006908749    TCJSWG  = 0.0006908749   TPB      = 0.001625007    TPBSW    = 0.001625007    TPBSWG   = 0.001625007
+JS      = 3.102E-06      JSW      = 2.8E-11        N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0   = 0             LLC      = -0.0165         )


.MODEL pch3.9            PMOS   (                    LMIN     = 3E-07
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = '5E-07-dxl3'   WMIN     = '5.6E-07-dxw3'  WMAX     = '1.25E-06-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.6280999+dvthp3' LVTH0    = -2.122741E-08  WVTH0    = -4.032327E-08
+PVTH0   = 1.167037E-14   K1       = 0.692555       LK1      = 6.26996E-08
+WK1     = 8.566985E-08   PK1      = -2.315684E-14  K2       = 0.1249961
+LK2     = -2.354725E-08  WK2      = -1.896766E-08  PK2      = 4.630635E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 127333.3       LVSAT    = -0.007106668
+UA      = 2.754258E-09   LUA      = -5.582093E-16  WUA      = -1.109095E-15
+PUA     = 2.758731E-22   UB       = -1.657709E-18  LUB      = 8.769503E-25
+WUB     = 8.367777E-25   PUB      = -4.297057E-31  UC       = -2.343E-10
+LUC     = 7.864889E-17   WUC      = 1.206725E-17   PUC      = -2.68825E-23
+RDSW    = 900            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.01054931     LU0      = -3.560923E-11
+WU0     = -1.14561E-09   PU0      = 4.530677E-17   A0       = 1.242906
+LA0     = -1.356991E-07  WA0      = 2.856588E-08   PA0      = 1.732362E-14
+KETA    = 0.00115498     LKETA    = -4.301479E-09  WKETA    = -2.068924E-10
+PKETA   = 3.831368E-17   A1       = 0              A2       = 0.99
+AGS     = 0.02           B0       = 0              B1       = 0
+VOFF    = -0.1456152     LVOFF    = 1.138703E-08   WVOFF    = 2.235144E-08
+PVOFF   = -5.579647E-15  NFACTOR  = 1              CIT      = 0.0003941574
+LCIT    = 2.849879E-11   WCIT     = 3.379819E-11   PCIT     = -5.955194E-18
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -0.0005933334  LETA0    = 2.842667E-10   ETAB     = 0.0002240581
+LETAB   = -1.328638E-10  WETAB    = 4.35745E-10    PETAB    = -1.786555E-16
+DSUB    = 0              PCLM     = 0.7313919      LPCLM    = -1.280678E-08
+WPCLM   = -3.651321E-08  PPCLM    = 2.450943E-14   PDIBLC1  = 1E-06
+PDIBLC2 = 0.001          PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 3.153333E+08   LPSCBE1  = 14.21334       PSCBE2   = 5E-07
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 0.143217238
+BETA0   = 16.10832       KT1      = -0.3592708     LKT1     = 2.287018E-08
+WKT1    = 2.914287E-08   PKT1     = -8.185104E-15  KT2      = -0.04482412
+LKT2    = 5.352623E-09   WKT2     = 1.667433E-08   PKT2     = -4.967589E-15
+AT      = -50000         UTE      = -0.4743063     LUTE     = -2.279284E-08
+WUTE    = 2.47481E-08    PUTE     = 1.012381E-14   UA1      = 2.031E-09
+UB1     = -1.879602E-18  LUB1     = -6.451224E-26  WUB1     = -1.727907E-25
+PUB1    = 7.081931E-32   UC1      = 1.10664E-10    LUC1     = -2.698751E-17
+WUC1    = -2.333436E-17  PUC1     = 1.824374E-23   KT1L     = 0
+PRT     = 0              CJ       = cjp3           PB       = 0.8049122
+MJ      = 0.3954951      CJSW     = cjswp3         PBSW     = 0.8049122
+MJSW    = 0.2573111      CJSWG    = cjswgp3        PBSWG    = 0.8049122
+MJSWG   = 0.2573111      CGDO     = cgop3          CGSO     = cgop3
+TCJ     = 0.0009940197   TCJSW    = 0.0006908749    TCJSWG   = 0.0006908749   TPB      = 0.001625007
+TPBSW   = 0.001625007     TPBSWG  = 0.001625007    JS       = 3.102E-06      JSW      = 2.8E-11
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              LLC      = -0.0165                   )


.MODEL pch3.10           PMOS   (                   LMIN     = '1.2E-06-dxl3'
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = 2.1E-05        WMIN     = 2.2E-07        WMAX     = '5.6E-07-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.6890861+dvthp3' LVTH0    = -9.8116E-09    WVTH0    = -9.374661E-10
+PVTH0   = 2.310781E-15   K1       = 0.8462622      LK1      = 1.737874E-08
+WK1     = 8.601185E-09   PK1      = -1.03108E-15   K2       = 0.07800844
+LK2     = -8.875218E-09  WK2      = -4.016258E-09  PK2      = 5.645247E-16
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 153784.1       LVSAT    = -0.03750033
+UA      = 5.00707E-10    LUA      = 4.25436E-17    WUA      = 1.979954E-18
+PUA     = -1.962135E-23  UB       = 5E-20          UC       = -1.475279E-10
+LUC     = 1.066435E-17   WUC      = -1.375334E-17  PUC      = -6.745771E-24
+RDSW    = 900            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.007724789    LU0      = -4.806926E-10
+WU0     = 6.985776E-10   PU0      = -1.454396E-16  A0       = 1.025261
+LA0     = -7.873648E-09  WA0      = 2.670523E-08   PA0      = -2.110824E-14
+KETA    = 0.01948166     LKETA    = -1.210574E-08  WKETA    = -5.69679E-10
+PKETA   = 4.262146E-16   A1       = 0              A2       = 0.99
+AGS     = 0.01571612     LAGS     = 4.245321E-08   WAGS     = 2.0991E-09
+PAGS    = -2.080207E-14  B0       = 0              B1       = 0
+VOFF    = -0.1080444     LVOFF    = -4.186274E-09  WVOFF    = -1.905964E-09
+PVOFF   = 1.923509E-15   NFACTOR  = 1              CIT      = 0.0009602004
+LCIT    = -5.278497E-10  WCIT     = -2.323009E-10  PCIT     = 2.629338E-16
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 1E-05          ETAB     = -1E-05         DSUB     = 0
+PCLM    = 0.4747727      LPCLM    = 2.500022E-07   PDIBLC1  = 1E-06
+PDIBLC2 = 1E-05          PDIBLCB  = 0.01           DROUT    = 0
+PSCBE1  = 1.873864E+08   LPSCBE1  = 125.0011       PSCBE2   = 5E-07
+PVAG    = 0              DELTA    = 0.01           ALPHA1   = 0.143217238
+BETA0   = 16.10832       KT1      = -0.2882728     LKT1     = -3.288603E-09
+WKT1    = 2.08704E-09    PKT1     = 1.316247E-15   KT2      = -0.02679297
+LKT2    = -2.79495E-09   WKT2     = 7.172971E-10   PKT2     = 1.188123E-15
+AT      = -50000         UTE      = -0.6359714     LUTE     = 2.614514E-07
+WUTE    = 1.268143E-08   PUTE     = -7.91107E-14   UA1      = 1.969475E-09
+LUA1    = 6.097175E-16   WUA1     = 3.014749E-17   PUA1     = -2.987616E-22
+UB1     = -2.651082E-18  LUB1     = -3.723891E-25  WUB1     = 1.276977E-25
+PUB1    = 1.934807E-31   UC1      = 5.887153E-11   LUC1     = 1.648043E-17
+WUC1    = -5.971426E-18  PUC1     = 1.68067E-23    KT1L     = 0
+PRT     = 0              CJ       = cjp3           PB       = 0.8049122
+MJ      = 0.3954951      CJSW     = cjswp3         PBSW     = 0.8049122
+MJSW    = 0.2573111      CJSWG    = cjswgp3        PBSWG    = 0.8049122
+MJSWG   = 0.2573111      CGDO     = cgop3          CGSO     = cgop3
+TCJ     = 0.0009940197   TCJSW    = 0.0006908749    TCJSWG   = 0.0006908749   TPB      = 0.001625007
+TPBSW   = 0.001625007     TPBSWG  = 0.001625007    JS       = 3.102E-06      JSW      = 2.8E-11
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              LLC     = -0.0165               )


.MODEL pch3.11           PMOS   (                   LMIN     = '5E-07-dxl3'
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = '1.2E-06-dxl3'  WMIN     = 2.2E-07       WMAX     = '5.6E-07-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.6975839+dvthp3' LVTH0    = -3.790473E-10  WVTH0    = 3.412466E-09
+PVTH0   = -2.517644E-15  K1       = 0.842974       LK1      = 2.102866E-08
+WK1     = 9.06978E-09    PK1      = -1.55122E-15   K2       = 0.07621089
+LK2     = -6.879946E-09  WK2      = -3.401967E-09  PK2      = -1.173375E-16
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 125857.2       LVSAT    = -0.006501434
+UA      = 5.372262E-10   LUA      = 2.007313E-18   WUA      = -1.351932E-17
+PUA     = -2.417151E-24  UB       = 5E-20          UC       = -1.532828E-10
+LUC     = 1.705233E-17   WUC      = -1.997575E-17  PUC      = 1.611036E-25
+RDSW    = 900            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.007578494    LU0      = -3.183063E-10
+WU0     = 4.557371E-10   PU0      = 1.241133E-16   A0       = 1.056145
+LA0     = -4.215433E-08  WA0      = -1.740636E-08  PA0      = 2.785563E-14
+KETA    = 0.02265681     LKETA    = -1.563016E-08  WKETA    = -1.987073E-09
+PKETA   = 1.999523E-15   A1       = 0              A2       = 0.99
+AGS     = 0.0576968      LAGS     = -4.145342E-09  WAGS     = -1.847143E-08
+PAGS    = 2.031218E-15   B0       = 0              B1       = 0
+VOFF    = -0.1187365     LVOFF    = 7.681949E-09   WVOFF    = -2.744444E-10
+PVOFF   = 1.125222E-16   NFACTOR  = 1              CIT      = 0.0004634161
+LCIT    = 2.358113E-11   WCIT     = 1.240311E-11   PCIT     = -8.68762E-18
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -4.27143E-05   LETA0    = 5.851286E-11   ETAB     = 4.27143E-05
+LETAB   = -5.851286E-11  DSUB     = 0              PCLM     = 0.6932496
+LPCLM   = 7.492927E-09   WPCLM    = -1.036421E-08  PPCLM    = 1.150428E-14
+PDIBLC1 = 1E-06          PDIBLC2  = -0.0005698573  LPDIBLC2 = 6.436415E-10
+PDIBLCB = 0.01           DROUT    = 0              PSCBE1   = 2.707143E+08
+LPSCBE1 = 32.50714       PSCBE2   = 5E-07          PVAG     = 0
+DELTA   = 0.01           ALPHA1   = 0.143217238    BETA0    = 16.10832
+KT1     = -0.2951284     LKT1     = 4.321107E-09   WKT1     = 5.237936E-09
+PKT1    = -2.181248E-15  KT2      = -0.03065884    LKT2     = 1.496166E-09
+WKT2    = 1.530824E-09   PKT2     = 2.851086E-16   AT       = -50000
+UTE     = -0.3962178     LUTE     = -4.675185E-09  WUTE     = -8.677028E-08
+PUTE    = 3.128071E-14   UA1      = 2.804463E-09   LUA1     = -3.171199E-16
+WUA1    = -3.78997E-16   PUA1     = 1.553888E-22   UB1      = -3.443699E-18
+LUB1    = 5.074158E-25   WUB1     = 4.303823E-25   PUB1     = -1.424993E-31
+UC1     = 5.874288E-11   LUC1     = 1.662325E-17   WUC1     = 1.777156E-17
+PUC1    = -9.548015E-24  KT1L     = 0              PRT      = 0
+CJ      = cjp3           PB       = 0.8049122      MJ       = 0.3954951
+CJSW    = cjswp3         PBSW     = 0.8049122      MJSW     = 0.2573111
+CJSWG   = cjswgp3        PBSWG    = 0.8049122      MJSWG    = 0.2573111
+CGDO    = cgop3          CGSO     = cgop3          TCJ      = 0.0009940197
+TCJSW   = 0.0006908749    TCJSWG  = 0.0006908749   TPB      = 0.001625007    TPBSW    = 0.001625007    TPBSWG   = 0.001625007
+JS      = 3.102E-06      JSW      = 2.8E-11        N        = 1
+XTI     = 3              CAPMOD   = 3              NQSMOD   = 0
+XPART   = 1              CF       = 0              TLEV     = 1
+TLEVC   = 1              CALCACM  = 1              SFVTFLAG = 0
+ALPHA0   = 0              LLC     = -0.0165         )


.MODEL pch3.12           PMOS   (                    LMIN     = 3E-07
+NOIMOD  = 3              EF       = 1.152          AF       = 1.052          KF       = 8.262E-28
+LMAX    = '5E-07-dxl3'   WMIN     = 2.2E-07        WMAX     = '5.6E-07-dxw3'
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxp3          XJ       = 1.7E-07        NCH      = 4.95E+17
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 3.5E-08        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 3.5E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxl3'
+XW      = '0+dxw3'       DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifp3
+RSH     = 7.2            RD       = 0              RS       = 0
+VTH0    = '-0.7082442+dvthp3' LVTH0    = 3.991676E-09   WVTH0    = -1.052551E-09
+PVTH0   = -6.869867E-16  K1       = 0.9669317      LK1      = -2.979399E-08
+WK1     = -4.877473E-08  PK1      = 2.216503E-14   K2       = 0.06178322
+LK2     = -9.645982E-10  WK2      = 1.200664E-08   PK2      = -6.434864E-15
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 127333.3       LVSAT    = -0.007106668
+UA      = 5.477329E-10   LUA      = -2.300429E-18  WUA      = -2.78971E-17
+PUA     = 3.477736E-24   UB       = 5E-20          UC       = -2.194337E-10
+LUC     = 4.41742E-17    WUC      = 4.78279E-18    PUC      = -9.989899E-24
+RDSW    = 900            PRWB     = 0              PRWG     = 0
+WR      = 1              U0       = 0.00755848     LU0      = -3.101005E-10
+WU0     = 3.198976E-10   PU0      = 1.798075E-16   A0       = 1.277182
+LA0     = -1.327796E-07  WA0      = 1.17706E-08    PA0      = 1.589307E-14
+KETA    = -0.008870148   LKETA    = -2.704106E-09  WKETA    = 4.70542E-09
+PKETA   = -7.443992E-16  A1       = 0              A2       = 0.99
+AGS     = 0.04553097     LAGS     = 8.426507E-10   WAGS     = -1.251017E-08
+PAGS    = -4.128996E-16  B0       = 0              B1       = 0
+VOFF    = -0.1           NFACTOR  = 1              CIT      = 0.0005009237
+LCIT    = 8.202983E-12   WCIT     = -1.851731E-11  PCIT     = 3.989753E-18
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -0.0005933335  LETA0    = 2.842667E-10   ETAB     = 0.001113334
+LETAB   = -4.974668E-10  DSUB     = 0              PCLM     = 0.8998926
+LPCLM   = -7.723069E-08  WPCLM    = -1.190785E-07  PPCLM    = 5.607715E-14
+PDIBLC1 = 1E-06          PDIBLC2  = 0.001          PDIBLCB  = 0.01
+DROUT   = 0              PSCBE1   = 3.153333E+08   LPSCBE1  = 14.21334
+PSCBE2  = 5E-07          PVAG     = 0              DELTA    = 0.01
+ALPHA1  = 0.143217238    BETA0    = 16.10832       KT1      = -0.2930027
+LKT1    = 3.449585E-09   WKT1     = -3.328495E-09  PKT1     = 1.330989E-15
+KT2     = -0.02032981    LKT2     = -2.738734E-09  WKT2     = 4.67212E-09
+PKT2    = -1.002823E-15  AT       = -50000         UTE      = -0.4102473
+LUTE    = 1.076929E-09   WUTE     = -6.640789E-09  PUTE     = -1.572383E-15
+UA1     = 2.031E-09      UB1      = -2.294264E-18  LUB1     = 3.614712E-26
+WUB1    = 3.039328E-26   PUB1     = 2.149622E-32   UC1      = 9.41543E-11
+LUC1    = 2.104574E-18   WUC1     = -1.524461E-17  PUC1     = 3.988613E-24
+KT1L    = 0              PRT      = 0              CJ       = cjp3
+PB      = 0.8049122      MJ       = 0.3954951      CJSW     = cjswp3
+PBSW    = 0.8049122      MJSW     = 0.2573111      CJSWG    = cjswgp3
+PBSWG   = 0.8049122      MJSWG    = 0.2573111      CGDO     = cgop3
+CGSO    = cgop3          TCJ      = 0.0009940197   TCJSW    = 0.0006908749    TCJSWG   = 0.0006908749
+TPB     = 0.001625007    TPBSW    = 0.001625007    TPBSWG   = 0.001625007    JS       = 3.102E-06
+JSW     = 2.8E-11        N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+LLC     = -0.0165          )


.ENDL MOS_3V

***************************************************************
*                                                             *
*              1.8V native NMOS DEVICE MODEL                  *
*                                                             *
***************************************************************
*
.LIB MOSNA

.MODEL nanch.1          NMOS   (                    LMIN     = '8.2E-07-dxlna'
+NOIMOD  = 3              EF       = 0.95           AF       = 0.95           KF       = 2.92E-28
+LMAX    = 2.1E-05        WMIN     = 2.2E-07        WMAX     = 0.000101
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxna          XJ       = 2E-07          NCH      = 1.052E+15
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 2.675E-08      LL       = 0
+LW      = 0              LWL      = 0              WINT     = 2.6E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxlna'
+XW      = '0+dxwna'      DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifna
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '-0.01774261+dvthna' LVTH0    = 6.182923E-08   WVTH0    = -3.753495E-09
+PVTH0   = -5.377128E-15  K1       = 0.01953682     LK1      = -3.977839E-09
+WK1     = 8.240465E-09   PK1      = -1.371659E-15  K2       = -0.0009140425
+LK2     = -8.184622E-10  WK2      = -4.367525E-10  PK2      = 1.205304E-16
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 97603.5        LVSAT    = 0.01646395
+WVSAT   = 0.003378191    PVSAT    = 5.871035E-11   UA       = 9.102442E-11
+LUA     = 2.508072E-19   WUA      = -1.036519E-17  PUA      = -2.537652E-24
+UB      = 2.023123E-18   LUB      = 7.463114E-25   WUB      = -1.589492E-26
+PUB     = -1.60874E-31   UC       = -2.064959E-11  LUC      = 6.691113E-18
+WUC     = -1.462443E-17  PUC      = 5.745368E-24   RDSW     = 68
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.0544471      LU0      = 9.232913E-10   WU0      = 2.605018E-09
+PU0     = -1.181193E-15  A0       = 1.318223       LA0      = -3.152826E-07
+WA0     = -2.414332E-07  PA0      = 2.113845E-13   KETA     = -0.007562
+A1      = 0              A2       = 0.99           AGS      = 0.01817691
+LAGS    = 1.359381E-09   WAGS     = 1.844599E-08   PAGS     = -1.375421E-14
+B0      = 0              B1       = 0              VOFF     = -0.1437579
+LVOFF   = -1.670469E-08  WVOFF    = 4.828936E-10   PVOFF    = 5.80468E-15
+NFACTOR = 1              CIT      = 0.0002597791   LCIT     = 4.032749E-10
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = 0.003399928    LETA0    = 8.502075E-10   WETA0    = 1.186005E-09
+PETA0   = -1.969099E-16  ETAB     = 0.001011681    LETAB    = -4.725199E-10
+WETAB   = 4.574829E-10   PETAB    = -1.154549E-16  DSUB     = 0
+PCLM    = 0.4528076      LPCLM    = 2.005277E-07   WPCLM    = 2.740156E-07
+PPCLM   = 1.122796E-14   PDIBLC1  = 0.03034016     LPDIBLC1 = -2.539301E-10
+WPDIBLC1= -3.441731E-09  PPDIBLC1 = 2.569253E-15   PDIBLC2  = 0.00225
+PDIBLCB = 0.1804105      LPDIBLCB = -5.115617E-10  WPDIBLCB = 2.114142E-08
+PPDIBLCB= 5.175938E-15   DROUT    = 0              PSCBE1   = 3.030791E+08
+LPSCBE1 = -0.7799484     WPSCBE1  = -0.03412339    PPSCBE1  = 2.05864E-07
+PSCBE2  = 1.5243E-07     PVAG     = 0              DELTA    = 0.003
+ALPHA1  = 1.876E-2       BETA0    = 8.1            KT1      = -0.322786
+LKT1    = 3.214286E-08   WKT1     = -4.367528E-09  PKT1     = 1.205308E-15
+KT2     = -0.002         AT       = 10000          UTE      = -1.570186
+LUTE    = 1.603067E-07   WUTE     = 4.146074E-08   PUTE     = 1.015063E-14
+UA1     = 4E-09          UB1      = -6E-18         UC1      = -2.8E-12
+KT1L    = 0              PRT      = 0              CJ       = cjna
+PB      = 0.5667062      MJ       = 0.3904209      CJSW     = cjswna
+PBSW    = 0.5667062      MJSW     = 0.0428681      CJSWG    = cjswgna
+PBSWG   = 0.5667062      MJSWG    = 0.4305378      CGDO     = cgona
+CGSO    = cgona          TCJ      = 0.001812677    TCJSW    = 0.001103346    TCJSWG   = 0.001103346
+TPB     = 0.001711098    TPBSW    = 0.001711098     TPBSWG   = 0.001711098    JS       = 2E-06
+JSW     = 1.5E-10        N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+LLC     = -0.03           )


.MODEL nanch.2          NMOS   (                    LMIN     = 5E-07
+NOIMOD  = 3              EF       = 0.95           AF       = 0.95           KF       = 2.92E-28
+LMAX    = '8.2E-07-dxlna'  WMIN     = 2.2E-07        WMAX     = 0.000101
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxna          XJ       = 2E-07          NCH      = 1.052E+15
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 2.675E-08      LL       = 0
+LW      = 0              LWL      = 0              WINT     = 2.6E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-08+dxlna'
+XW      = '0+dxwna'      DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifna
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '0.02792398+dvthna' LVTH0    = 2.773913E-08   WVTH0    = -1.438199E-08
+PVTH0   = 2.557044E-15   K1       = 0.01404253     LK1      = 1.23647E-10
+WK1     = 8.078899E-09   PK1      = -1.25105E-15   K2       = -0.0004382913
+LK2     = -1.17361E-09   WK2      = -6.966282E-10  PK2      = 3.145276E-16
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 154073         LVSAT    = -0.02569051
+WVSAT   = 0.00243878     PVSAT    = 7.599806E-10   UA       = 9.171293E-11
+LUA     = -2.631544E-19  WUA      = -1.733133E-17  PUA      = 2.662571E-24
+UB      = 2.770609E-18   LUB      = 1.88313E-25    WUB      = -1.480558E-25
+PUB     = -6.221591E-32  UC       = -2.834392E-11  LUC      = 1.243493E-17
+WUC     = -6.156361E-18  PUC      = -5.760438E-25  RDSW     = 68
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.05722036     LU0      = -1.146955E-09  WU0      = 9.626542E-10
+PU0     = 4.483137E-17   A0       = 0.6052103      LA0      = 2.169814E-07
+WA0     = -1.144547E-07  PA0      = 1.165951E-13   KETA     = -0.007562
+A1      = 0              A2       = 0.99           AGS      = 0.01999473
+LAGS    = 2.377243E-12   WAGS     = 5.327309E-11   PAGS     = -2.40528E-17
+B0      = 0              B1       = 0              VOFF     = -0.1601644
+LVOFF   = -4.457263E-09  WVOFF    = 2.527387E-08   PVOFF    = -1.270178E-14
+NFACTOR = 1              CIT      = 0.001565254    LCIT     = -5.712622E-10
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -0.002726106   LETA0    = 5.423292E-09   WETA0    = -2.225066E-09
+PETA0   = 2.349455E-15   ETAB     = 0.0003545133   LETAB    = 1.805535E-11
+WETAB   = 5.475407E-10   PETAB    = -1.826831E-16  DSUB     = 0
+PCLM    = 1.5367825      LPCLM    = -6.086595E-07  WPCLM    = 5.564588E-07
+PPCLM   = -1.996159E-13  PDIBLC1  = 0.01805861     LPDIBLC1 = 8.914247E-09
+WPDIBLC1= -3.062515E-09  PPDIBLC1 = 2.286167E-15   PDIBLC2  = 0.00225
+PDIBLCB = 0.1798815      LPDIBLCB = -1.166351E-10  WPDIBLCB = 2.649413E-08
+PPDIBLCB= 1.180139E-15   DROUT    = 0              PSCBE1   = 3.005564E+08
+LPSCBE1 = 1.103308       WPSCBE1  = 0.6114948      PPSCBE1  = -2.760899E-07
+PSCBE2  = 1.5243E-07     PVAG     = 0              DELTA    = 0.003
+ALPHA1  = 1.876E-2       BETA0    = 8.1            KT1      = -0.3252268
+LKT1    = 3.396488E-08   WKT1     = -6.966276E-09  PKT1     = 3.145274E-15
+KT2     = -0.002         AT       = 10000          UTE      = -1.327971
+LUTE    = -2.05067E-08   WUTE     = 8.682543E-08   PUTE     = -2.371411E-14
+UA1     = 4E-09          UB1      = -6E-18         UC1      = -2.8E-12
+KT1L    = 0              PRT      = 0              CJ       = cjna
+PB      = 0.5667062      MJ       = 0.3904209      CJSW     = cjswna
+PBSW    = 0.5667062      MJSW     = 0.0428681      CJSWG    = cjswgna
+PBSWG   = 0.5667062      MJSWG    = 0.4305378      CGDO     = cgona
+CGSO    = cgona          TCJ      = 0.001812677    TCJSW    = 0.001103346    TCJSWG   = 0.001103346
+TPB     = 0.001711098    TPBSW    = 0.001711098     TPBSWG   = 0.001711098    JS       = 2E-06
+JSW     = 1.5E-10        N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+LLC     = -0.03           )

.ENDL MOSNA

***************************************************************
*                                                             *
*              3.3V native NMOS DEVICE MODEL                  *
*                                                             *
***************************************************************
*
.LIB MOSNA3

.MODEL nanch3.1         NMOS   (                    LMIN     = '1.52E-06-dxlna3'
+LMAX    = 2.1E-05        WMIN     = 2.2E-07        WMAX     = 1.01E-04
+NOIMOD  = 3              EF       = 1.01           AF       = 1.01           KF       = 3.24E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxna3         XJ       = 1.7E-07        NCH      = 5.8E+15
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.1E-07        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.64E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-8+dxlna3'
+XW      = '0+dxwna3'     DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifna3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '-0.09478436+dvthna3' LVTH0    = -3.815484E-08  WVTH0    = -1.353864E-08
+PVTH0   = -9.114775E-16  K1       = 0.07518722     LK1      = -2.494324E-08
+WK1     = 3.240441E-08   PK1      = 1.425852E-14   K2       = -0.002
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 103854         LVSAT    = -3.55722E-05
+WVSAT   = 0.001478785    PVSAT    = 3.602473E-10   UA       = 4.923768E-11
+LUA     = 4.496429E-16   WUA      = 6.08351E-17    PUA      = -8.462483E-23
+UB      = 2.081755E-18   LUB      = 7.512439E-25   WUB      = -1.655545E-25
+PUB     = -1.596647E-31  UC       = 3.085943E-13   LUC      = -1.032446E-19
+WUC     = -5.505085E-18  PUC      = 1.045582E-24   RDSW     = 220
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.05171998     LU0      = 5.906318E-11   WU0      = 8.10373E-10
+PU0     = -5.98144E-16   A0       = 1              KETA     = -0.01830086
+LKETA   = 4.266525E-11   WKETA    = -1.773655E-09  PKETA    = -4.320807E-16
+A1      = 0              A2       = 1              AGS      = 0.79888
+LAGS    = -4.465664E-07  WAGS     = -4.177232E-08  PAGS     = 5.346858E-14
+B0      = 0              B1       = 0              VOFF     = -0.1081457
+LVOFF   = 2.321209E-09   WVOFF    = 1.475376E-09   PVOFF    = -2.350736E-14
+NFACTOR = 1              CIT      = 0.000162       CDSC     = 0
+CDSCB   = 0              CDSCD    = 0              ETA0     = 0.00172966
+LETA0   = 8.846976E-09   WETA0    = -2.508041E-10  PETA0    = -2.15119E-16
+ETAB    = 0.0009718285   LETAB    = 3.797812E-10   WETAB    = -9.240519E-11
+PETAB   = -1.219557E-16  DSUB     = 0              PCLM     = 0.5239226
+LPCLM   = 2.677888E-06   WPCLM    = -9.599169E-08  PPCLM    = 1.394485E-12
+PDIBLC1 = 9.767E-07      PDIBLC2  = 0.001081524    LPDIBLC2 = 1.821685E-10
+WPDIBLC2= -2.440943E-11  PPDIBLC2 = 2.406769E-16   PDIBLCB  = 0
+DROUT   = 0              PSCBE1   = 5.76E+08       PSCBE2   = 1E-06
+PVAG    = 8              DELTA    = 0.002          ALPHA1   = 1.771E-03
+BETA0   = 7.2            KT1      = -0.2806568     LKT1     = -1.599956E-10
+WKT1    = 6.651208E-09   PKT1     = 1.620303E-15   KT2      = -0.013
+AT      = 10000          UTE      = -1.904673      LUTE     = 1.879744E-07
+WUTE    = 5.345823E-08   PUTE     = 3.291194E-14   UA1      = 8.047672E-10
+LUA1    = -2.766493E-18  WUA1     = -4.82784E-17   PUA1     = 2.801685E-23
+UB1     = -2.512189E-18  LUB1     = -5.333165E-28  WUB1     = 2.217068E-26
+PUB1    = 5.401006E-33   UC1      = -1.3E-11       KT1L     = 0
+PRT     = 0              CJ       = cjna3          PB       = 0.5947797
+MJ      = 0.4342894      CJSW     = cjswna3        PBSW     = 0.5947797
+MJSW    = 0.0158148      CJSWG    = cjswgna3       PBSWG    = 0.5947797
+MJSWG   = 0.541221       CGDO     = cgona3         CGSO     = cgona3
+TCJ     = 0.0046087      TCJSW    = 0.007157987    TCJSWG   = 0.007157987    TPB      = 0.002492415
+TPBSW   = 0.002492415    TPBSWG  = 0.002492415    JS       = 2E-06          JSW      = 1.25E-8
+N       = 1              XTI      = 3              CAPMOD   = 3
+NQSMOD  = 0              XPART    = 1              CF       = 0
+TLEV    = 1              TLEVC    = 1              CALCACM  = 1
+SFVTFLAG= 0              ALPHA0   = 0              LLC     = -0.0135                 )


.MODEL nanch3.2          NMOS   (                    LMIN     = 1.2E-06
+LMAX    = '1.52E-06-dxlna3' WMIN     = 2.2E-07     WMAX     = 1.01E-04
+NOIMOD  = 3              EF       = 1.01           AF       = 1.01           KF       = 3.24E-28
+LEVEL   = 49             TNOM     = 25             VERSION  = 3.2
+TOX     = toxna3         XJ       = 1.7E-07        NCH      = 5.8E+15
+LLN     = -1             LWN      = 1              WLN      = 1
+WWN     = 1              LINT     = 1.1E-07        LL       = 0
+LW      = 0              LWL      = 0              WINT     = 1.64E-08
+WL      = 0              WW       = 0              WWL      = 0
+MOBMOD  = 1              BINUNIT  = 2              XL       = '-2E-8+dxlna3'
+XW      = '0+dxwna3'     DWG      = 0              DWB      = 0
+ACM     = 12             LDIF     = 9E-08          HDIF     = hdifna3
+RSH     = 6.8            RD       = 0              RS       = 0
+VTH0    = '-0.05361792+dvthna3' LVTH0    = -9.084788E-08  WVTH0    = -5.219657E-09
+PVTH0   = -1.155977E-14  K1       = 0.0548448      LK1      = 1.095044E-09
+WK1     = 5.220765E-08   PK1      = -1.108962E-14  K2       = -0.002
+K3      = 0              DVT0     = 0              DVT1     = 0
+DVT2    = 0              DVT0W    = 0              DVT1W    = 0
+DVT2W   = 0              NLX      = 0              W0       = 0
+K3B     = 0              VSAT     = 118376.8       LVSAT    = -0.01862484
+WVSAT   = -0.002351273   PVSAT    = 5.262721E-09   UA       = 3.333493E-10
+LUA     = 8.597997E-17   WUA      = 1.334063E-17   PUA      = -2.383191E-23
+UB      = 2.656073E-18   LUB      = 1.611759E-26   WUB      = -1.627728E-25
+PUB     = -1.632252E-31  UC       = -9.803229E-14  LUC      = 4.17237E-19
+WUC     = -1.387119E-18  PUC      = -4.225415E-24  RDSW     = 220
+PRWB    = 0              PRWG     = 0              WR       = 1
+U0      = 0.05668826     LU0      = -6.300333E-09  WU0      = 1.190146E-10
+PU0     = 2.867948E-16   A0       = -9.648092      LA0      = 1.362956E-05
+WA0     = 1.972317E-06   PA0      = -2.524565E-12  KETA     = -0.03065319
+LKETA   = 1.585364E-08   WKETA    = -9.007868E-09  PKETA    = 8.827711E-15
+A1      = 0              A2       = 1              AGS      = 0.6133333
+LAGS    = -2.090666E-07  B0       = 0              B1       = 0
+VOFF    = -0.103894      LVOFF    = -3.1209E-09    WVOFF    = -4.158169E-08
+PVOFF   = 3.160569E-14   NFACTOR  = 1              CIT      = 0.000162
+CDSC    = 0              CDSCB    = 0              CDSCD    = 0
+ETA0    = -0.0006868758  LETA0    = 1.194014E-08   WETA0    = -1.888288E-09
+PETA0   = 1.88086E-15    ETAB     = -4.851932E-05  LETAB    = 1.685826E-09
+WETAB   = -8.2514E-11    PETAB    = -1.346164E-16  DSUB     = 0
+PCLM    = -0.7794965     LPCLM    = 4.346263E-06   WPCLM    = 2.298267E-06
+PPCLM   = -1.670166E-12  PDIBLC1  = 9.767E-07      PDIBLC2  = 0.001225951
+LPDIBLC2= -2.697764E-12  WPDIBLC2 = 1.422751E-10   PPDIBLC2 = 2.732071E-17
+PDIBLCB = 0              DROUT    = 0              PSCBE1   = 5.76E+08
+PSCBE2  = 1E-06          PVAG     = 8              DELTA    = 0.002
+ALPHA1  = 1.771E-3       BETA0    = 7.2            KT1      = -0.2833356
+LKT1    = 3.268843E-09   WKT1     = 3.377951E-08   PKT1     = -3.310392E-14
+KT2     = -0.013         AT       = 10000          UTE      = -1.677388
+LUTE    = -1.029496E-07  WUTE     = 2.571094E-07   PUTE     = -2.277616E-13
+UA1     = 1.137785E-09   LUA1     = -4.290296E-16  WUA1     = -1.125984E-16
+PUA1    = 1.103464E-22   UB1      = -2.521118E-18  LUB1     = 1.089613E-26
+WUB1    = 1.125983E-25   PUB1     = -1.103463E-31  UC1      = -1.3E-11
+KT1L    = 0              PRT      = 0              CJ       = cjna3
+PB      = 0.5947797      MJ       = 0.4342894      CJSW     = cjswna3
+PBSW    = 0.5947797      MJSW     = 0.0158148      CJSWG    = cjswgna3
+PBSWG   = 0.5947797      MJSWG    = 0.541221       CGDO     = cgona3
+CGSO    = cgona3         TCJ      = 0.0046087      TCJSW    = 0.007157987    TCJSWG   = 0.007157987
+TPB     = 0.002492415    TPBSW    = 0.002492415     TPBSWG   = 0.002492415    JS       = 2E-06
+JSW     = 1.25E-8        N        = 1              XTI      = 3
+CAPMOD  = 3              NQSMOD   = 0              XPART    = 1
+CF      = 0              TLEV     = 1              TLEVC    = 1
+CALCACM = 1              SFVTFLAG = 0              ALPHA0   = 0
+LLC     = -0.0135           )

.ENDL MOSNA3

**************************
*                        *
* 0.18um    1.8V bipolar *
*                        *
**************************
.LIB BIP
*
.MODEL PNP5 PNP (                                   LEVEL  = 1
+ BF     = 2.775           NF     = 0.9928534       IS     = 2.5351E-18
+ ISE    = 2.5351E-18      ISC    = 2.5351E-18      NE     = 1.3977142
+ RB     = 54.76734        IRB    = 1.401332E-3     RBM    = 1.0965611
+ RE     = 1.3979963       IKF    = 8.2254E-4       NKF    = 0.477972
+ VAF    = 372.731         BR     = 4.4013E-3       NR     = 0.993881
+ NC     = 0.98076         RC     = 20.08           IKR    = 1.98804E-4
+ VAR    = 20.84541        XTI    = 3               EG     = 1.17
+ XTB    = 0               TRB1   = 1.493714E-3     TIRB1  = 1.375303E-5
+ TRM1   = 1.074565E-5     TRE1   = 1.068665E-4     TIKF1  = -2.512025E-3
+ TIKR1  = -3.93E-3        TRC1   = 8E-5            TBF1   = 4.9E-3
+ TBF2   = 1.1E-6          TNF1   = -1.056025E-4    TNE1   = 2.152336E-4
+ TVAF1  = -4E-5           TBR1   = -1.01E-3        TBR2   = 1.3E-5
+ TNC1   = 1.122277E-4     TNC2   = 0               TNR1   = -1.026101E-4
+ TNR2   = 0               CJE    = 3.2987E-14      VJE    = 0.895226
+ MJE    = 0.4345495       FC     = 0               CJC    = 3.965229E-14
+ VJC    = 0.5846489       MJC    = 0.2933243       TLEV   = 0
+ TLEVC  = 1               CTE    = 2.0325E-3       CTC    = 8.900197E-4
+ TVJE   = 1.572025E-3     TVJC   = 2.819E-3        TREF   = 25
+ SUBS   = 1               )
*
.MODEL PNP10 PNP (                                  LEVEL  = 1
+ BF     = 2.715           NF     = 0.9931534       IS     = 9.0353E-18
+ ISE    = 9.0353E-18      ISC    = 9.0353E-18      NE     = 1.2977142
+ RB     = 36.063401       IRB    = 1.401332E-3     RBM    = 1.0965611
+ RE     = 1.3979963       IKF    = 1.72254E-3      NKF    = 0.477972
+ VAF    = 361.145         BR     = 0.0114433       NR     = 0.9908706
+ NC     = 0.9007513       RC     = 20.08           IKR    = 1.98804E-4
+ VAR    = 20.84541        XTI    = 3               EG     = 1.17
+ XTB    = 0               TRB1   = 1.493714E-3     TIRB1  = 1.375303E-5
+ TRM1   = 1.074565E-5     TRE1   = 1.068665E-4     TIKF1  = -3.912025E-3
+ TIKR1  = -3.93E-3        TRC1   = 8E-5            TBF1   = 4.91E-3
+ TBF2   = 1E-6            TNF1   = -1.0025E-4      TNE1   = 2.00234E-4
+ TVAF1  = -5E-3           TBR1   = -3.15E-3        TBR2   = 3.5E-5
+ TNC1   = 8.022278E-5     TNC2   = 0               TNR1   = -2.025978E-4
+ TNR2   = 0               CJE    = 1.22024E-13     VJE    = 0.895226
+ MJE    = 0.4405495       FC     = 0               CJC    = 6.837658E-14
+ VJC    = 0.5846489       MJC    = 0.3033243       TLEV   = 0
+ TLEVC  = 1               CTE    = 9.300197E-4     CTC    = 2.1425E-3
+ TVJE   = 1.572025E-3     TVJC   = 2.819E-3        TREF   = 25
+ SUBS   = 1               )
*
.MODEL PNP2 PNP (                                   LEVEL  = 1
+ BF     = 2.7551          NF     = 1.006853        IS     = 8.03515E-19
+ ISE    = 8.03515E-19     ISC    = 8.03515E-19     NE     = 1.2977142
+ RB     = 102.76734       IRB    = 1.401332E-3     RBM    = 1.0965611
+ RE     = 1.297997        IKF    = 3.02541E-4      NKF    = 0.427981
+ VAF    = 126.168         BR     = 1.3713E-3       NR     = 0.993671
+ NC     = 0.920748        RC     = 20.08           IKR    = 1.98804E-4
+ VAR    = 15.6151         XTI    = 3               EG     = 1.17
+ XTB    = 0               TRB1   = 1.493714E-3     TIRB1  = 1.375303E-5
+ TRM1   = 1.074565E-5     TRE1   = 1.068665E-4     TIKF1  = -4.31203E-3
+ TIKR1  = -3.93E-3        TRC1   = 8E-5            TBF1   = 5.85E-3
+ TBF2   = 3E-6            TNF1   = -1.056025E-4    TNE1   = 2.152336E-4
+ TVAF1  = -1E-3           TBR1   = -1.5E-3         TBR2   = 1.85E-5
+ TNC1   = 1.122198E-4     TNC2   = 0               TNR1   = -2.425601E-4
+ TNR2   = 0               CJE    = 6.4688E-15      VJE    = 0.895226
+ MJE    = 0.4205495       FC     = 0               CJC    = 2.562787E-14
+ VJC    = 0.5846489       MJC    = 0.2833243       TLEV   = 0
+ TLEVC  = 1               CTE    = 8.000197E-4     CTC    = 1.9025E-3
+ TVJE   = 1.572025E-3     TVJC   = 2.819E-3        TREF   = 25
+ SUBS   = 1               )
*
.ENDL BIP
*************************
*                       *
* 0.18um   3.3V bipolar *
*                       *
*************************
.LIB BIP3
*
.MODEL PNP10_3 PNP (                                  LEVEL  = 1
+ BF     = 2.715           NF     = 0.9931534       IS     = 9.0353E-18
+ ISE    = 9.0353E-18      ISC    = 9.0353E-18      NE     = 1.2977142
+ RB     = 33.063401       IRB    = 1.401332E-3     RBM    = 1.0965611
+ RE     = 1.3979963       IKF    = 2.05254E-3      NKF    = 0.477972
+ VAF    = 361.145         BR     = 9.0433E-3       NR     = 0.9908706
+ NC     = 0.9007513       RC     = 20.08           IKR    = 1.98804E-4
+ VAR    = 27.84541        XTI    = 3               EG     = 1.17
+ XTB    = 0               TRB1   = 1.493714E-3     TIRB1  = 1.375303E-5
+ TRM1   = 1.074565E-5     TRE1   = 1.068665E-4     TIKF1  = -3.912025E-3
+ TIKR1  = -3.93E-3        TRC1   = 8E-5            TBF1   = 5.11E-3
+ TBF2   = 1E-6            TNF1   = -1.0025E-4      TNE1   = 2.00234E-4
+ TVAF1  = -5E-3           TBR1   = -1.95E-3        TBR2   = 2.25E-5
+ TNC1   = 8.022278E-5     TNC2   = 0               TNR1   = -2.025978E-4
+ TNR2   = 0               CJE    = 1.124556E-13    VJE    = 0.8049122
+ MJE    = 0.3845495       FC     = 0               CJC    = 6.353976E-14
+ VJC    = 0.5846489       MJC    = 0.2883243       TLEV   = 0
+ TLEVC  = 1               CTE    = 9.700197E-4     CTC    = 1.9425E-3
+ TVJE   = 1.625007E-3     TVJC   = 2.819E-3        TREF   = 25
+ SUBS   = 1               )
*
.MODEL PNP5_3 PNP (                                   LEVEL  = 1
+ BF     = 2.725           NF     = 0.9928534       IS     = 2.5351E-18
+ ISE    = 2.5351E-18      ISC    = 2.5351E-18      NE     = 1.3977142
+ RB     = 54.76734        IRB    = 1.401332E-3     RBM    = 1.0965611
+ RE     = 1.3979963       IKF    = 1.1254E-3       NKF    = 0.477972
+ VAF    = 372.731         BR     = 3.5513E-3       NR     = 0.993881
+ NC     = 0.98076         RC     = 20.08           IKR    = 1.98804E-4
+ VAR    = 22.44541        XTI    = 3               EG     = 1.17
+ XTB    = 0               TRB1   = 1.493714E-3     TIRB1  = 1.375303E-5
+ TRM1   = 1.074565E-5     TRE1   = 1.068665E-4     TIKF1  = -2.752025E-3
+ TIKR1  = -3.93E-3        TRC1   = 8E-5            TBF1   = 5.2E-3
+ TBF2   = 1.1E-6          TNF1   = -1.056025E-4    TNE1   = 2.152336E-4
+ TVAF1  = -4E-5           TBR1   = -1.01E-3        TBR2   = 1.3E-5
+ TNC1   = 1.122277E-4     TNC2   = 0               TNR1   = -1.026101E-4
+ TNR2   = 0               CJE    = 3.034505E-14    VJE    = 0.8049122
+ MJE    = 0.3745495       FC     = 0               CJC    = 3.728498E-14
+ VJC    = 0.5846489       MJC    = 0.2783243       TLEV   = 0
+ TLEVC  = 1               CTE    = 9.500197E-4     CTC    = 2.0325E-3
+ TVJE   = 1.625007E-3     TVJC   = 3.009E-3        TREF   = 25
+ SUBS   = 1               )
*
.MODEL PNP2_3 PNP (                                   LEVEL  = 1
+ BF     = 2.7351          NF     = 1.006853        IS     = 8.03515E-19
+ ISE    = 8.03515E-19     ISC    = 8.03515E-19     NE     = 1.2977142
+ RB     = 102.76734       IRB    = 1.401332E-3     RBM    = 1.0965611
+ RE     = 1.297997        IKF    = 4.02541E-4      NKF    = 0.427981
+ VAF    = 126.168         BR     = 1.1153E-3       NR     = 1.013671
+ NC     = 0.920748        RC     = 20.08           IKR    = 1.98804E-4
+ VAR    = 20.0151         XTI    = 3               EG     = 1.17
+ XTB    = 0               TRB1   = 1.493714E-3     TIRB1  = 1.375303E-5
+ TRM1   = 1.074565E-5     TRE1   = 1.068665E-4     TIKF1  = -4.31203E-3
+ TIKR1  = -3.93E-3        TRC1   = 8E-5            TBF1   = 5.85E-3
+ TBF2   = 3E-6            TNF1   = -1.056025E-4    TNE1   = 2.152336E-4
+ TVAF1  = -1E-3           TBR1   = -1.5E-3         TBR2   = 1.65E-5
+ TNC1   = 1.122198E-4     TNC2   = 0               TNR1   = -2.425601E-4
+ TNR2   = 0               CJE    = 5.92616E-15     VJE    = 0.8049122
+ MJE    = 0.3495495       FC     = 0               CJC    = 2.432423E-14
+ VJC    = 0.5846489       MJC    = 0.2673243       TLEV   = 0
+ TLEVC  = 1               CTE    = 9.000197E-4     CTC    = 1.9025E-3
+ TVJE   = 1.625007E-3     TVJC   = 2.959E-3        TREF   = 25
+ SUBS   = 1               )
*
.ENDL BIP3
*
*************************
*                       *
* 0.18um   1.8V diode   *
*                       *
*************************
*
.LIB DIO
*
.MODEL NDIO D (                                     LEVEL  = 3
+ IS     = 8.38E-6         RS     = 1.0E-10         N      = 1.3217
+ BV     = 10.72           IBV    = 1E-3            IK     = 1E20
+ IKR    = 1E10            JSW    = 1.24E-11        AREA   = 7.5E-8
+ PJ     = 1.1E-3          CJ     = 1.000266E-3     PB     = 0.6882682
+ MJ     = 0.3595262       CJSW   = 2.040547E-10    PHP    = 0.6882682
+ MJSW   = 0.2003879       TLEV   = 1               EG     = 1.17
+ XTI    = 3               TCV    = -9.3E-4         TRS    = 1.62E-3
+ TLEVC  = 1               CTA    = 1.040287E-3     CTP    = 6.45489E-4
+ TPB    = 1.554306E-3     TPHP   = 1.554306E-3     TREF   = 25
+ FC     = 0               FCS    = 0               )
*
.MODEL PDIO D (                                     LEVEL  = 3
+ IS     = 4.92E-6         RS     = 1.0E-10         N      = 1.25
+ BV     = 10.2            IBV    = 1E-3            IK     = 1E20
+ IKR    = 1E10            JSW    = 1.02E-11        AREA   = 7.5E-8
+ PJ     = 1.1E-3          CJ     = 1.121E-3        PB     = 0.895226
+ MJ     = 0.4476          CJSW   = 2.481E-10       PHP    = 0.895226
+ MJSW   = 0.3683619       TLEV   = 1               EG     = 1.17
+ XTI    = 3               TCV    = -8.8E-4         TRS    = 1.2E-4
+ TLEVC  = 1               CTA    = 9.739001E-4     CTP    = 4.130718E-4
+ TPB    = 1.572025E-3     TPHP   = 1.572025E-3     TREF   = 25
+ FC     = 0               FCS    = 0               )
*
.MODEL NWDIO D (                                    LEVEL  = 3
+ IS     = 1.55E-5         RS     = 1.0E-10         N      = 1.38
+ BV     = 14.75           IBV    = 1E-3            IK     = 1E20
+ IKR    = 1E10            JSW    = 4.75E-11        AREA   = 7.5E-8
+ PJ     = 1.1E-3          CJ     = 1.337566E-4     PB     = 0.5846489
+ MJ     = 0.3883243       CJSW   = 5.333577E-10    PHP    = 0.5846489
+ MJSW   = 0.2345684       TLEV   = 1               EG     = 1.17
+ XTI    = 3               TCV    = -9.6E-4         TRS    = 1.125E-3
+ TLEVC  = 1               CTA    = 2.8425E-3       CTP    = 1.5284E-3
+ TPB    = 2.819E-3        TPHP   = 2.819E-3        TREF   = 25
+ FC     = 0               FCS    = 0               )
*
.ENDL DIO
*
*********************************
*                               *
* 0.18um   3.3V and ESD diode   *
*                               *
*********************************
*
.LIB DIO3
*
.MODEL NDIO_3 D (                                     LEVEL  = 3
+ IS     = 7.93E-6         RS     = 1.0E-10         N      = 1.3217
+ BV     = 10.84           IBV    = 1E-3            IK     = 1E20
+ IKR    = 1E10            JSW    = 1.74E-11        AREA   = 7.5E-8
+ PJ     = 1.1E-3          CJ     = 8.964788E-4     PB     = 0.7076023
+ MJ     = 0.3259624       CJSW   = 2.50664E-10     PHP    = 0.7076023
+ MJSW   = 0.1513672       TLEV   = 1               EG     = 1.17
+ XTI    = 3               TCV    = -8.33E-4        TRS    = 1.62E-3
+ TLEVC  = 1               CTA    = 9.923959E-4     CTP    = 5.019466E-4
+ TPB    = 1.687207E-3     TPHP   = 1.687207E-3     TREF   = 25
+ FC     = 0               FCS    = 0               )
*
.MODEL PDIO_3 D (                                     LEVEL  = 3
+ IS     = 3.102E-6        RS     = 1.0E-10         N      = 1.25
+ BV     = 10.3            IBV    = 1E-3            IK     = 1E20
+ IKR    = 1E10            JSW    = 1.02E-11        AREA   = 7.5E-8
+ PJ     = 1.1E-3          CJ     = 1.03531E-3      PB     = 0.8049122
+ MJ     = 0.3954951       CJSW   = 2.23115E-10     PHP    = 0.8049122
+ MJSW   = 0.2573111       TLEV   = 1               EG     = 1.17
+ XTI    = 3               TCV    = -8.1E-4         TRS    = 1.2E-4
+ TLEVC  = 1               CTA    = 9.940197E-4     CTP    = 6.908749E-4
+ TPB    = 1.625007E-3     TPHP   = 1.625007E-3     TREF   = 25
+ FC     = 0               FCS    = 0               )
*
.MODEL NWDIO_3 D (                                    LEVEL  = 3
+ IS     = 2.05E-5         RS     = 1.0E-10         N      = 1.38
+ BV     = 14.55           IBV    = 1E-3            IK     = 1E20
+ IKR    = 1E10            JSW    = 6.17E-11        AREA   = 7.5E-8
+ PJ     = 1.1E-3          CJ     = 1.163383E-4     PB     = 0.5529009
+ MJ     = 0.3581039       CJSW   = 5.274555E-10    PHP    = 0.5529009
+ MJSW   = 0.2203          TLEV   = 1               EG     = 1.17
+ XTI    = 3               TCV    = -9.6E-4         TRS    = 1.125E-3
+ TLEVC  = 1               CTA    = 2.8425E-3       CTP    = 1.5284E-3
+ TPB    = 2.819E-3        TPHP   = 2.819E-3        TREF   = 25
+ FC     = 0               FCS    = 0               )
*
***************************************************************
*                                                             *
*                                                             *
*                      MODEL OF ESD DIODE                     *
*                                                             *
*                                                             *
*                                                             *
***************************************************************
.MODEL ENDIO D (                                     LEVEL  = 3
+ CJ     = 1.416999E-3     PB     = 0.6798575
+ MJ     = 0.3357974       TREF   = 25
+ FC     = 0               FCS    = 0               )
*
.ENDL DIO3

**************************************************************************
*
*   0.18um  resistor model
*
**************************************************************************
*
.lib RES
**************************************************************************
.subckt rnod n1 n2 l=length w=width
.param rsh=6.8 dw=-0.165u ptc1=3.35e-3 ptc2=4.31e-7 pvc1=7.56e-5 pvc2=1.24e-3 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rnod

.subckt rnodw n1 n2 l=length w=width
.param rsh=4.1 dw=-0.165u ptc1=3.35e-3 ptc2=4.31e-7 pvc1=7.56e-5 pvc2=1.24e-3 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rnodw

.subckt rpod n1 n2 l=length w=width
.param rsh=7.2 dw=-0.148u ptc1=3.44e-3 ptc2=5.02e-7 pvc1=-2.51e-4 pvc2=1.03e-3 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rpod

.subckt rpodw n1 n2 l=length w=width
.param rsh=4.4 dw=-0.148u ptc1=3.44e-3 ptc2=5.02e-7 pvc1=-2.51e-4 pvc2=1.03e-3 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rpodw

.subckt rnodrpo n1 n2 l=length w=width
.param rsh=59 dw=0.0u ptc1=1.47e-3 ptc2=8.32e-7 pvc1=7.55e-4 pvc2=1.97e-4 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rnodrpo

.subckt rpodrpo n1 n2 l=length w=width
.param rsh=133 dw=0.00u ptc1=1.43e-3 ptc2=7.82e-7 pvc1=-1.19e-3 pvc2=-1.80e-4 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rpodrpo

.subckt rnwod n1 n2 l=length w=width
.param rsh=440 dw=0.141u ptc1=3.68e-3 ptc2=9.54e-6 pvc1=2.77e-3 pvc2=2.49e-4 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rnwod

.subckt rnwsti n1 n2 l=length w=width
.param rsh=927 dw=0.182u ptc1=2.97e-3 ptc2=1.10e-5 pvc1=8.06e-3 pvc2=-3.32e-4 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rnwsti

.subckt rnpo1 n1 n2 l=length w=width
.param rsh=7.4 dw=-0.065u ptc1=2.92e-3 ptc2=2.66e-7 pvc1=1.35e-3 pvc2=7.15e-3 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rnpo1

.subckt rnpo1w n1 n2 l=length w=width
.param rsh=5.7 dw=-0.065u ptc1=2.92e-3 ptc2=2.66e-7 pvc1=1.35e-3 pvc2=7.15e-3 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rnpo1w

.subckt rppo1 n1 n2 l=length w=width
.param rsh=7.8 dw=-0.051u ptc1=2.88e-3 ptc2=5.01e-7 pvc1=-7.89e-4 pvc2=6.19e-3 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rppo1

.subckt rppo1w n1 n2 l=length w=width
.param rsh=6.7 dw=-0.051u ptc1=2.88e-3 ptc2=5.01e-7 pvc1=-7.89e-4 pvc2=6.19e-3 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rppo1w

.SUBCKT rnpo1rpo n1 n2 l=length w=width
.param rx=1.477e-5 rgrain=37.16 rp=292 dl=0.07616e-6 dw=0.08333e-6 rc=7.8 nc=2
.param pt='temper'
.param pvcx1=3.785e-1 pvcx2=8.434e-6 pvcx3=-1.430 ptcx1=-2.278e-3 ptcx2=-21.29e-6
.param pvcp1=-2.843e-2 pvcp2=1.496e-5 pvcp3=-2.100 ptcp1=-1.102e-3 ptcp2=1.747e-6
.param pvcg1=2.527e-1 pvcg2=6.918e-6 pvcg3=-1.283 ptcg1=4.235e-3 ptcg2=-6.211e-6
.param tfacx='1.0+ptcx1*(pt-25.0)+ptcx2*(pt-25.0)*(pt-25.0)'
.param tfacp='1.0+ptcp1*(pt-25.0)+ptcp2*(pt-25.0)*(pt-25.0)'
.param tfacg='1.0+ptcg1*(pt-25.0)+ptcg2*(pt-25.0)*(pt-25.0)'
rc1 n1 5 'rc/nc'
rg1 5 7 'rgrain*tfacg*(1+pvcg1*(tanh(pvcg2*abs(v(3,4)/(l-dl))+pvcg3)-tanh(pvcg3)))'
rx1 7 3 'rx/(w-dw)*tfacx*(1+pvcx1*(tanh(pvcx2*abs(v(3,4)/(l-dl))+pvcx3)-tanh(pvcx3)))'
rp1 3 4 'rp*(l-dl)/(w-dw)*tfacp*(1+pvcp1*(tanh(pvcp2*abs(v(3,4)/(l-dl))+pvcp3)-tanh(pvcp3)))'
rx2 4 6 'rx/(w-dw)*tfacx*(1+pvcx1*(tanh(pvcx2*abs(v(3,4)/(l-dl))+pvcx3)-tanh(pvcx3)))'
rg2 6 8 'rgrain*tfacg*(1+pvcg1*(tanh(pvcg2*abs(v(3,4)/(l-dl))+pvcg3)-tanh(pvcg3)))'
rc2 8 n2 'rc/nc'
.ENDS rnpo1rpo

.SUBCKT rppo1rpo n1 n2 l=length w=width
.param rx=6.752e-5 rgrain=39.411 rp=311 dl=0.04696e-6 dw=0.06061e-6 rc=7.8 nc=2
.param pt='temper'
.param pvcx1=-1.311e-2 pvcx2=2.171e-5 pvcx3=-3.211 ptcx1=-1.790e-3 ptcx2=-7.245e-6
.param pvcp1=-5.405e-3 pvcp2=2.134e-5 pvcp3=-3.820 ptcp1=-13.80e-5 ptcp2=581.1e-9
.param pvcg1=6.667e-2 pvcg2=4.141e-6 pvcg3=0.140 ptcg1=2.979e-3 ptcg2=-2.295e-6
.param tfacx='1.0+ptcx1*(pt-25.0)+ptcx2*(pt-25.0)*(pt-25.0)'
.param tfacp='1.0+ptcp1*(pt-25.0)+ptcp2*(pt-25.0)*(pt-25.0)'
.param tfacg='1.0+ptcg1*(pt-25.0)+ptcg2*(pt-25.0)*(pt-25.0)'
rc1 n1 5 'rc/nc'
rg1 5 7 'rgrain*tfacg*(1+pvcg1*(tanh(pvcg2*abs(v(3,4)/(l-dl))+pvcg3)-tanh(pvcg3)))'
rx1 7 3 'rx/(w-dw)*tfacx*(1+pvcx1*(tanh(pvcx2*abs(v(3,4)/(l-dl))+pvcx3)-tanh(pvcx3)))'
rp1 3 4 'rp*(l-dl)/(w-dw)*tfacp*(1+pvcp1*(tanh(pvcp2*abs(v(3,4)/(l-dl))+pvcp3)-tanh(pvcp3)))'
rx2 4 6 'rx/(w-dw)*tfacx*(1+pvcx1*(tanh(pvcx2*abs(v(3,4)/(l-dl))+pvcx3)-tanh(pvcx3)))'
rg2 6 8 'rgrain*tfacg*(1+pvcg1*(tanh(pvcg2*abs(v(3,4)/(l-dl))+pvcg3)-tanh(pvcg3)))'
rc2 8 n2 'rc/nc'
.ENDS rppo1rpo

.subckt rm1 n1 n2 l=length w=width
.param rsh=0.078 dw=0.03u ptc1=3.43e-3 ptc2=-1.08e-6 pvc1=0 pvc2=0 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rm1

.subckt rm2 n1 n2 l=length w=width
.param rsh=0.078 dw=0.03u ptc1=3.43e-3 ptc2=-1.08e-6 pvc1=0 pvc2=0 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rm2

.subckt rm3 n1 n2 l=length w=width
.param rsh=0.078 dw=0.03u ptc1=3.43e-3 ptc2=-1.08e-6 pvc1=0 pvc2=0 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rm3

.subckt rm4 n1 n2 l=length w=width
.param rsh=0.078 dw=0.03u ptc1=3.43e-3 ptc2=-1.08e-6 pvc1=0 pvc2=0 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rm4

.subckt rm5 n1 n2 l=length w=width
.param rsh=0.078 dw=0.03u ptc1=3.43e-3 ptc2=-1.08e-6 pvc1=0 pvc2=0 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rm5

.subckt rm6 n1 n2 l=length w=width
.param rsh=0.036 dw=0.04u ptc1=3.60e-3 ptc2=-1.16e-7 pvc1=0 pvc2=0 pt='temper'
.param tfac='1.0+ptc1*(pt-25.0)+ptc2*(pt-25.0)*(pt-25.0)'
r1 n1 n2 'rsh*l/(w-dw)*(1+pvc1*abs(v(n2,n1))+pvc2*v(n2,n1)*v(n2,n1))*tfac'
.ends rm6

.endl RES
