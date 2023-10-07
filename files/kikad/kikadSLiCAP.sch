EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "SLiCAP symbols"
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
Wire Wire Line
	2750 2050 3600 2050
Wire Wire Line
	3600 2050 3600 2250
Wire Wire Line
	3600 2650 3600 2850
Wire Wire Line
	3600 2850 2750 2850
Text Label 2750 2850 0    50   ~ 0
0
$Comp
L SLiCAP:V V1
U 1 1 5F6CE0F7
P 2750 2450
F 0 "V1" H 2878 2678 50  0000 L CNN
F 1 "V" H 2878 2587 50  0001 L CNN
F 2 "" H 2750 2400 50  0001 C CNN
F 3 "" H 2750 2400 50  0001 C CNN
F 4 "value={V}" H 2878 2496 50  0000 L CNN "value"
F 5 "noise=0" H 2878 2405 50  0000 L CNN "noise"
F 6 "dc=0" H 2878 2314 50  0000 L CNN "dc"
F 7 "dcvar=0" H 2878 2223 50  0000 L CNN "dcvar"
	1    2750 2450
	1    0    0    -1  
$EndComp
$Comp
L SLiCAP:R R1
U 1 1 5F6CE863
P 3200 2450
F 0 "R1" H 3668 2541 50  0000 L CNN
F 1 "R" H 3668 2450 50  0001 L CNN
F 2 "" H 3200 2450 50  0001 C CNN
F 3 "" H 3200 2450 50  0001 C CNN
F 4 "value={R}" H 3668 2359 50  0000 L CNN "value"
	1    3200 2450
	1    0    0    -1  
$EndComp
Wire Wire Line
	2750 2050 2750 2250
Wire Wire Line
	2750 2850 2750 2650
Text Label 2950 2050 0    50   ~ 0
in
$Comp
L SLiCAP:I I1
U 1 1 5F6CF100
P 4400 2450
F 0 "I1" H 4528 2678 50  0000 L CNN
F 1 "I" H 4528 2587 50  0001 L CNN
F 2 "" H 4400 2400 50  0001 C CNN
F 3 "" H 4400 2400 50  0001 C CNN
F 4 "value={I}" H 4528 2496 50  0000 L CNN "value"
F 5 "noise=0" H 4528 2405 50  0000 L CNN "noise"
F 6 "dc=0" H 4528 2314 50  0000 L CNN "dc"
F 7 "dcvar=0" H 4528 2223 50  0000 L CNN "dcvar"
	1    4400 2450
	1    0    0    -1  
$EndComp
Wire Wire Line
	3600 2050 4400 2050
Wire Wire Line
	4400 2050 4400 2250
Connection ~ 3600 2050
Wire Wire Line
	4400 2650 4400 2850
Wire Wire Line
	4400 2850 3600 2850
Connection ~ 3600 2850
$EndSCHEMATC
