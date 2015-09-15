#!/usr/bin/env python

"""
Script to create and run a lot of WCSim .mac files

Run examples:

e.g. 10000 events per configuration  in the SK geometry, with the SKI digitizer, 25 NHits trigger (automatically adjusted for dark noise rate), 0 or 8.4 kHZ dark noise in a window 2000 ns (+/-1000ns) around hits, with 5,10,20,50 MeV electrons using a fixed position & direction
(produces 8 files total)

python generate_mac_files.py --batchmode local --WCgeom SuperK --HKwatertanklength 24750 --PMTQEMethod Stacking_Only --SavePi0 false --DAQdigitizer SKI --DAQtrigger NHits --DAQnhitsthreshold 25 --DAQnhitsignorenoise --DAQnhitswindow 200 --DAQsavefailuresmode 0 --DAQsavefailurestime 250 --DarkNoiseRate 0,8.4 --DarkNoiseConvert 1.367 --DarkNoiseMode 1 --DarkNoiseWindow 2000 --GunParticle e- --GunEnergy 5,10,20,50 --GunPosition 0,0,0 --GunDirection 1,0,0 --NEvents 10000

e.g. the same, but producing the particles at random positions and directions
(produces 8 files total)

python generate_mac_files.py --batchmode local --WCgeom SuperK --HKwatertanklength 24750 --PMTQEMethod Stacking_Only --SavePi0 false --DAQdigitizer SKI --DAQtrigger NHits --DAQnhitsthreshold 25 --DAQnhitsignorenoise --DAQnhitswindow 200 --DAQsavefailuresmode 0 --DAQsavefailurestime 250 --DarkNoiseRate 0,8.4 --DarkNoiseConvert 1.367 --DarkNoiseMode 1 --DarkNoiseWindow 2000 --GunParticle e- --GunEnergy 5,10,20,50 --GunPosition random --GunDirection 4pi --NEvents 10000

"""

import argparse
import shutil
import sys
import os
import itertools

delim_list = lambda s: list(set(s.split(',')))
delim_list_str = lambda s: s.split(',') if len(s.split(',')) == 3 else s

DAQdigitizer_choices = ['SKIV', 'SKI', 'SKI_SKDETSIM']
DAQtrigger_choices = ['NHits', 'SKI_SKDETSIM', 'NHits2', 'NHitsThenLocalNHits']
DAQtrigger_nhits_choices = ['NHits', 'SKI_SKDETSIM', 'NHits2', 'NHitsThenLocalNHits']
DAQtrigger_localnhits_choices = ['NHitsThenLocalNHits']
WCgeom_choices = ['HyperK', \
                      'HyperK_withHPD', \
                      'SuperK', \
                      'SuperK_20inchPMT_20perCent', \
                      'SuperK_20inchBandL_20perCent', \
                      'SuperK_12inchBandL_15perCent', \
                      'SuperK_20inchBandL_14perCent', \
                      'Cylinder_12inchHPD_15perCent', \
                      'Cylinder_60x74_20inchBandL_14perCent', \
                      'Cylinder_60x74_20inchBandL_40perCent']
HKwatertargetlength_choices = ['HyperK', 'HyperK_withHPD']
PMTQEMethod_choices = ['Stacking_Only', 'Stacking_And_SensitiveDetector', 'SensitiveDetector_Only']
PMTCollEff_choices = ['on', 'off']
GunPositionChoices = ['center', 'random', 'wall', 'minusx', 'plusx', 'minusz', 'plusz']
GunDirectionChoices = ['towall', 'tocap', '4pi', 'wall']
GunParticleChoices=['e-','e+','mu-','mu+','pi-','pi+','pi0','gamma','p+','n0']
BatchChoices=['local','condor']

def ListAsString(l):
    return ' '.join(str(o)+',' for o in l)[:-1]

parser = argparse.ArgumentParser(description='Run many WCSim jobs with different options. Use , to delimit multiple options', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
#options about how to run this script
parser.add_argument('--onlycreatefiles', action='store_true', help="Do a test run where you create all the files, but don't run WCSim?")
parser.add_argument('--batchmode', type=str, default='local', choices=BatchChoices, help='Where to submit the jobs.')
parser.add_argument('--vis', action='store_true', help='Turn on the visulation? Not yet implemented')
parser.add_argument('--reusedaqfolder', action='store_true', help='Reuse the DAQ folders? (i.e. don\'t exit if mkdir fails)')
#options for the .mac files
# geometry
parser.add_argument('--WCgeom', type=delim_list, default='SuperK', help='The water tank geometry. Specify multiple with comma separated list. Choices: '+ListAsString(WCgeom_choices))
parser.add_argument('--HKwatertanklength', type=delim_list, default='49500', help='The size of a HyperK geometry (mm)')
# trigger & digitization
parser.add_argument('--DAQsavefailuresmode', type=delim_list, default='0', help='Save failed triggers mode. 0: save only events which pass the trigger. 1: save only events which fail the trigger. 2: save both')
parser.add_argument('--DAQsavefailurestime', type=delim_list, default='200', help='For mode 1 & 2, give events which fail the trigger the trigger time')
parser.add_argument('--DAQdigitizer', type=delim_list, default='SKI', help='Which digitizer class to use? Specify multiple with comma separated list. Choices: '+ListAsString(DAQdigitizer_choices))
parser.add_argument('--DAQtrigger', type=delim_list, default='NHits', help='Which trigger class to use? Specify multiple with comma separated list. Choices: '+ListAsString(DAQtrigger_choices))
#nhits trigger
parser.add_argument('--DAQnhitsthreshold', type=delim_list, default='25', help='What value of the nhits trigger threshold should be used (i.e. number of hits/digits)? Specify multiple with comma separated list')
parser.add_argument('--DAQnhitswindow', type=delim_list, default='200', help='What value of the nhits trigger window should be used (ns)? Specify multiple with comma separated list')
parser.add_argument('--DAQnhitsignorenoise', action='store_true', help='Adjust the NHits and LocalNHits threshold automatically for the dark noise rate?')
#local nhits trigger
parser.add_argument('--DAQlocalnhitsneighbours', type=delim_list, default='50', help='What value of the localnhits trigger neighbours should be used (i.e. number of hits/digits)? Specify multiple with comma separated list')
parser.add_argument('--DAQlocalnhitsthreshold', type=delim_list, default='10', help='What value of the localnhits trigger threshold should be used (i.e. number of hits/digits)? Specify multiple with comma separated list')
parser.add_argument('--DAQlocalnhitswindow', type=delim_list, default='50', help='What value of the localnhits trigger window should be used (ns)? Specify multiple with comma separated list')
# dark noise
parser.add_argument('--DarkNoiseRate', type=delim_list, default='4.2', help='Dark noise rate (kHz). Specify multiple with comma separated list')
parser.add_argument('--DarkNoiseConvert', type=delim_list, default='1.367', help='Convert dark noise frequency before digitization to after digitization by setting suitable factor. Specify multiple with comma separated list')
parser.add_argument('--DarkNoiseMode', type=int, default=1, choices=[0,1], help='0: apply noise in a specified time window. 1: apply noise around hits. Choose exactly one')
parser.add_argument('--DarkNoiseWindow', type=delim_list, default='1500', help=' Mode 0: Apply dark noise in range x:y (use : as delimeter!). Mode 1: Apply dark noise in a window around each hit (+-window/2). Specify multiple (for the same mode) with a comma separated list')
# pmt
parser.add_argument('--PMTQEMethod', type=delim_list, default='Stacking_Only', help='How the QE is applied? Specify multiple with comma separated list. Choices: '+ListAsString(PMTQEMethod_choices))
parser.add_argument('--PMTCollEff', type=delim_list, default='on', help='Turn on/off the PMT collection efficiency? Specify multiple with comma separated list. Choices: '+ListAsString(PMTCollEff_choices))
# other
parser.add_argument('--SavePi0', action='store_true', help='Save Pi0 info?')
# particle gun
parser.add_argument('--GunParticle', type=str, default='e-', choices=GunParticleChoices, help='Particle gun particle. Choose exactly one (default e-)')
parser.add_argument('--GunEnergy', type=delim_list, default='500', help='Particle gun energy (MeV). Specify multiple with comma separated list')
parser.add_argument('--GunPosition', type=delim_list_str, default='0,0,0', help='Particle gun position. Either a comma-separated 3 vector OR exactly one of '+ListAsString(GunPositionChoices))
parser.add_argument('--GunDirection', type=delim_list_str, default='1,0,0', help='Particle gun direction. Either a comma-separated 3 vector OR exactly one of '+ListAsString(GunDirectionChoices))
parser.add_argument('--NEvents', type=int, default=10, help='Number of events per configuration')

def check_input_list(arglist, allowed, parser):
    #check for options that aren't allowed
    for arg in arglist:
        if arg not in allowed:
            print arg, "is incorrect"
            parser.print_help()
            sys.exit(1)

def main(args_to_parse = None):

    #parse the arguments and check that they're valid
    args = parser.parse_args(args_to_parse)
    check_input_list(args.WCgeom, WCgeom_choices, parser)
    check_input_list(args.PMTQEMethod, PMTQEMethod_choices, parser)
    check_input_list(args.PMTCollEff, PMTCollEff_choices, parser)
    check_input_list(args.DAQdigitizer, DAQdigitizer_choices, parser)
    check_input_list(args.DAQtrigger, DAQtrigger_choices, parser)
    if (type(args.GunPosition) is list and len(args.GunPosition) != 3) \
        or (type(args.GunDirection) is list and len(args.GunDirection) != 3):
        print "GunPosition and GunDirection are three vectors. Specify exactly 3 options!"
        parser.print_help()
        sys.exit(1)
    if (type(args.GunPosition) is str and args.GunPosition not in GunPositionChoices):
        print "GunPosition", args.GunPosition, "not one of", GunPositionChoices
        parser.print_help()
        sys.exit(1)
    if (type(args.GunDirection) is str and args.GunDirection not in GunDirectionChoices):
        print "GunDirection", args.GunDirection, "not one of", GunDirectionChoices
        parser.print_help()
        sys.exit(1)
    if type(args.GunDirection) != type(args.GunPosition):
        print "Must use consistent GunPosition and GunDirection options (i.e. both 3 vectors or both MakeKin.py str options)"
        parser.print_help()
        sys.exit(1)


    
    #Grab the other .mac files
    shutil.copy2(os.path.expandvars("$WCSIMDIR") + "/jobOptions.mac", "./")
    shutil.copy2(os.path.expandvars("$WCSIMDIR") + "/jobOptions2.mac", "./")
    shutil.copy2(os.path.expandvars("$WCSIMDIR") + "/tuning_parameters.mac", "./")
    #and the exectuable
    if args.batchmode == 'condor':
        if not os.path.islink('WCSim'):
            os.symlink(os.path.expandvars("$WCSIMDIR") + "/bin/" + os.path.expandvars("$G4SYSTEM") + "/WCSim", "WCSim")


    #methods to construct sets of .mac file options
    def ConstructVerbosity(args):
        verboptions = "/run/verbose 0 \n" \
            "/tracking/verbose 0 \n" \
            "/hits/verbose 0 \n"
        return [verboptions]

    def ConstructGeometry(args):
        #the detector construction options
        geoms = []
        filestubs = []
        for WCgeom in args.WCgeom:
            for HKwatertanklength in args.HKwatertanklength:
                constructoptions = ''
                if WCgeom == 'SuperK':
                    pass
                else:
                    constructoptions = "/WCSim/WCgeom " + WCgeom + "\n"
                filestub = WCgeom
                if WCgeom in HKwatertargetlength_choices:
                    constructoptions += "/WCSim/HyperK/waterTank_Length " + HKwatertanklength + "\n"
                    filestub += "_" + HKwatertanklength
                constructoptions += "/WCSim/Construct \n"
                geoms.append(constructoptions)
                filestubs.append(filestub)
        return [geoms, filestubs]

    def ConstructPMT(args):
        #the PMT behaviour options
        pmts = []
        filestubs = []
        for PMTQEMethod in args.PMTQEMethod:
            for PMTCollEff in args.PMTCollEff:
                pmtoptions = "/WCSim/PMTQEMethod " + PMTQEMethod + "\n" \
                    "/WCSim/CollEff " + PMTCollEff + "\n"
                pmts.append(pmtoptions)
                filestubs.append(PMTQEMethod + "_PMTCollEff_" + PMTCollEff)
        return [pmts, filestubs]

    def ConstructDAQ(args):
        #make the DAQ digitizer / trigger options
        daqs = []
        filestubs = []
        for DAQdigitizer in args.DAQdigitizer:
            for DAQtrigger in args.DAQtrigger:
                if DAQtrigger == 'SKI_SKDETSIM' and DAQdigitizer != 'SKI_SKDETSIM':
                    continue
                if DAQtrigger != 'SKI_SKDETSIM' and DAQdigitizer == 'SKI_SKDETSIM':
                    continue
                for DAQsavefailuresmode in args.DAQsavefailuresmode:
                    for DAQsavefailurestime in args.DAQsavefailurestime:
                        for DAQnhitsthreshold in args.DAQnhitsthreshold:
                            for DAQnhitswindow in args.DAQnhitswindow:
                                for DAQlocalnhitsneighbours in args.DAQlocalnhitsneighbours:
                                    for DAQlocalnhitsthreshold in args.DAQlocalnhitsthreshold:
                                        for DAQlocalnhitswindow in args.DAQlocalnhitswindow:
                                            filestub = DAQdigitizer + "_" + DAQtrigger + "_fails" + DAQsavefailuresmode
                                            if DAQsavefailuresmode != '0':
                                                filestub += "_" + DAQsavefailurestime
                                            if DAQtrigger in DAQtrigger_nhits_choices:
                                                filestub += "_NHits" + str(DAQnhitsthreshold) + "_" + str(DAQnhitswindow)
                                            if DAQtrigger in DAQtrigger_localnhits_choices:
                                                filestub += "_LocalNHits" + str(DAQlocalnhitsneighbours) + "_" \
                                                                  + str(DAQlocalnhitsthreshold) + "_" \
                                                                  + str(DAQlocalnhitswindow)
                                            noise_agnostic = 'true' if args.DAQnhitsignorenoise else 'false'
                                            daqoptions = "/DAQ/Digitizer " + DAQdigitizer + "\n" \
                                                "/DAQ/Trigger " + DAQtrigger + "\n" \
                                                "/DAQ/TriggerSaveFailures/Mode " + DAQsavefailuresmode + "\n" \
                                                "/DAQ/TriggerSaveFailures/TriggerTime " + DAQsavefailurestime + "\n"
                                            if DAQtrigger in DAQtrigger_nhits_choices:
                                                daqoptions += "/DAQ/TriggerNHits/Threshold " + DAQnhitsthreshold + "\n" \
                                                    "/DAQ/TriggerNHits/Window " + DAQnhitswindow + "\n" \
                                                    "/DAQ/TriggerNHits/AdjustForNoise " + noise_agnostic + "\n"
                                            if DAQtrigger in DAQtrigger_localnhits_choices:
                                                daqoptions += "/DAQ/TriggerLocalNHits/Neighbours " + DAQlocalnhitsneighbours + "\n" \
                                                    "/DAQ/TriggerLocalNHits/Threshold " + DAQlocalnhitsthreshold + "\n" \
                                                    "/DAQ/TriggerLocalNHits/Window " + DAQlocalnhitswindow + "\n" \
                                                    "/DAQ/TriggerLocalNHits/AdjustForNoise " + noise_agnostic + "\n"
                                            daqs.append(daqoptions)
                                            filestubs.append(filestub)
        return [daqs, filestubs]


    def ConstructDarkNoise(args):
        noises = []
        filestubs = []
        for DarkNoiseRate in args.DarkNoiseRate:
            for DarkNoiseConvert in args.DarkNoiseConvert:
                for DarkNoiseWindow in args.DarkNoiseWindow:
                    #DarkNoiseWindow should be treated specially, as it depends on DarkNoiseMode
                    darknoisewindow = ""
                    if args.DarkNoiseMode == 1:
                        try:
                            int(DarkNoiseWindow)
                        except ValueError:
                            print "For DarkNoiseMode == 1, DarkNoiseWindow should be a single number (not colon separated)"
                            sys.exit(1)
                        darknoisewindow = "/DarkRate/SetDarkWindow " + DarkNoiseWindow + "\n"
                    elif args.DarkNoiseMode == 0:
                        if len(DarkNoiseWindow.split(':')[0]) != 2:
                            print "For DarkNoiseMode == 0, DarkNoiseWindow should be exactly two numbers, separated with a colon"
                            sys.exit(1)
                        darknoisewindow = "/DarkRate/SetDarkLow  " + DarkNoiseWindow.split(':')[0] + "\n" \
                            "/DarkRate/SetDarkHigh " + DarkNoiseWindow.split(':')[1] + "\n"
                    else:
                        print "Unknown DarkNoiseMode", args.DarkNoiseMode
                        sys.exit(1)
                    darkoptions = "/DarkRate/SetDarkRate " + DarkNoiseRate + " kHz \n" \
                        "/DarkRate/SetConvert " + DarkNoiseConvert + "\n" \
                        "/DarkRate/SetDarkMode " + str(args.DarkNoiseMode) + "\n" \
                        "" + darknoisewindow
                    noises.append(darkoptions)
                    filestubs.append("DarkNoiseM" + str(args.DarkNoiseMode) + "R" + DarkNoiseRate + "W" + DarkNoiseWindow.strip())
        return [noises, filestubs]

    def ConstructParticleGun(args):
        guns = []
        filestubs = []
        for GunEnergy in args.GunEnergy:
            if type(args.GunPosition) is str:
                #if GunPosition and GunDirection are string's
                #we need to call MakeKin.py to generate distributions of different positions/directions
                command = '$WCSIMDIR/sample-root-scripts/MakeKin.py -N 1 ' \
                    '-n ' + str(args.NEvents) + ' ' \
                    '-t ' + args.GunParticle  + ' ' \
                    '-e ' + GunEnergy  + ' ' \
                    '-v ' + args.GunPosition  + ' ' \
                    '-d ' + args.GunDirection
                print command
                os.system(command)
                #now create the .kin filename
                kinname = "%s_%.0fMeV__%s_%s_%03i.kin" % (args.GunParticle.replace("+","plus").replace("-","minus"), float(GunEnergy), args.GunPosition, args.GunDirection, 0)
                print kinname
                #and finally get the .mac options
                gunoptions = '/mygen/vecfile ' + kinname + '\n'
                guns.append(gunoptions)
            else:
                #we're using the simple GEANT4 particle gun
                gunoptions = "/mygen/generator normal " + "\n" \
                    "/gun/particle " + args.GunParticle + "\n" \
                    "/gun/energy " + GunEnergy + " MeV \n" \
                    "/gun/direction " + " ".join(i for i in args.GunDirection) + "\n" \
                    "/gun/position " + " ".join(i for i in args.GunPosition) + "\n"
                guns.append(gunoptions)
            filestubs.append(GunEnergy + args.GunParticle)
        return [guns, filestubs]

    #construct the .mac options and parts of filenames for the different groups
    o1     = ConstructVerbosity(args)
    o2, f2 = ConstructGeometry(args)
    o3, f3 = ConstructPMT(args)
    o4, f4 = ConstructDAQ(args)
    o5, f5 = ConstructDarkNoise(args)
    o6, f6 = ConstructParticleGun(args)
    options   = [x1 + x2 + x3 + x4 + x5 + x6 for x1 in o1 for x2 in o2 for x3 in o3 for x4 in o4 for x5 in o5 for x6 in o6]
    #remember f1 doesn't exist
    filestubs = [x6 + '_' + x2 + '_' + x3 + '_' + x4 + '_' + x5 for x2 in f2 for x3 in f3 for x4 in f4 for x5 in f5 for x6 in f6]

    counter = 1
    for text, filenamestub in itertools.izip(options, filestubs):
        filenamestub = 'wcsim_' + filenamestub + ("_SavePi0" if args.SavePi0 else "")
        #add the final bits to the text
        text += "/WCSimIO/RootFile " + filenamestub + ".root" + "\n" \
            "/WCSim/SavePi0 " + ("true" if args.SavePi0 else "false") + "\n" \
            "/run/beamOn " + str(args.NEvents) + "\n"
            
        #write the novis.mac style file
        f = open(filenamestub + '.mac', 'w')
        f.write(text)
        f.close()

        #print the run information
        print "\n\nfile:", counter
        print '\n', filenamestub + '.mac:'
        print text

        counter += 1

        #Submit the job
        Submit(filenamestub, args)
                                        


def Submit(filenamestub, args):
    #generate the command to run
    if args.batchmode == 'local':
        command = '$WCSIMDIR/bin/$G4SYSTEM/WCSim ' + filenamestub + '.mac &> ' + filenamestub + '.out'
    elif args.batchmode == 'condor':
        fcondor = open(filenamestub + '.jdl', 'w')
        condor = '' \
            'executable     = WCSim \n' \
            'universe       = vanilla \n' \
            'arguments      = ' + filenamestub + '.mac \n' \
            'output         = ' + filenamestub + '.out \n' \
            'error          = ' + filenamestub + '.err \n' \
            'log            = ' + filenamestub + '.log \n' \
            'request_memory = 1000 \n' \
            'getenv         = True \n' \
            'queue 1 \n'
        fcondor.write(condor)
        fcondor.close()
        command = 'condor_submit ' + filenamestub + '.jdl'

    #run the job
    print command
    if not args.onlycreatefiles:
        os.system(command)
    else:
        print 'test run; not actually running WCSim'
                               
if __name__ == "__main__":
    main()
