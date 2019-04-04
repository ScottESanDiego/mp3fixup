#!/usr/bin/env python3
#
# ToDo:
# Make extension case insensitive
# Only make non-empty output file
# Signal handling

import os
import glob
import subprocess
import multiprocessing
import argparse

# Constants
MP3Extension='*.mp3'
FailedPackExtension='.PACKFAIL'

# Find all ".mp3" files in directory and below
# Note: Case sensitive
def find_files(directory,extension):
    filenames = []
    for mp3name in glob.glob(directory+'/**/'+extension, recursive=True):
        filenames.append(mp3name)
    return filenames

# Build list of all directories with ".mp3" files
def find_directories(mp3files):
    directories = []
    for mp3name in mp3files:
        dirname=os.path.dirname(mp3name)
        if dirname not in directories:
            directories.append(dirname)
    return directories

# Function bundles for MP3Val
def val_subprocess(mp3name):
    print("MP3Val: "+mp3name)
    return subprocess.run([MP3ValExe]+MP3ValArgs+[mp3name], capture_output=True)

def run_val_parallel(numprocesses,mp3names):
    pool_output = []
    pool = multiprocessing.Pool(processes=numprocesses)

    for myfile in mp3names:
        pool_output.append(pool.apply_async(val_subprocess,(myfile,)))

    pool.close()
    pool.join()

    return pool_output


# Function bundles for MP3Packer
def pack_subprocess(mp3name):
    print("MP3Packer: "+mp3name)
    return subprocess.run([MP3PackerExe]+MP3PackerArgs+[mp3name], capture_output=True)

def run_pack_parallel(numprocesses,mp3names):
    pool_output = []
    pool = multiprocessing.Pool(processes=numprocesses)

    for myfile in mp3names:
        pool_output.append(pool.apply_async(pack_subprocess,(myfile,)))

    pool.close()
    pool.join()

    return pool_output


# Function bundles for MP3Gain
def gain_subprocess(directory,mp3names):
    print("MP3Gain in Directory: "+directory)
    return subprocess.run([MP3GainExe]+MP3GainArgs+mp3names, capture_output=True)

def run_gain_parallel(numprocesses,directories):
    pool_output = []
    pool = multiprocessing.Pool(processes=numprocesses)

    for dirname in directories:
        mp3names=glob.glob(dirname+'/'+MP3Extension)
        pool_output.append(pool.apply_async(gain_subprocess,(dirname,mp3names,)))

    pool.close()
    pool.join()

    return pool_output

def save_output(f,pool_output):
    for subproc_output in pool_output:
        result=subproc_output.get()
        for line in result.stdout.splitlines():
            f.write(str(line,'utf-8')+'\n')

def main():
    NumProcesses=multiprocessing.cpu_count()
    TopDirectory="."
    OutputFile="/tmp/mp3fixup.log"
    PreferredVolumeDB=89.0

    parser=argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-d", "--directory", help="directory to use", default=TopDirectory)
    parser.add_argument("-p", "--processes", help="number of concurrent processes", type=int, default=NumProcesses)
    parser.add_argument("-o", "--output", help="filename to save output to", default=OutputFile)
    parser.add_argument("--volume", help="volume level in dB", type=float, default=PreferredVolumeDB)
    parser.add_argument("-n", "--dryrun", help="echo commands rather than do them", action='store_true') 
    parser.add_argument("--track", help="use track gain instead of album gain", action='store_true') 
    parser.add_argument("--skipgain", help="do not run MP3Gain", action='store_true', default=False)
    parser.add_argument("--skipval", help="do not run MP3Val", action='store_true', default=False)
    parser.add_argument("--skippack", help="do not run MP3Packer", action='store_true', default=False)
    args=parser.parse_args()

    global MP3GainExe, MP3GainArgs
    # Have to parse Album vs Track gain arg here
    if not args.track:
        gaintype="-a"
    else:
        gaintype=""
        
    MP3GainExe="/usr/bin/mp3gain"
    MP3GainArgs=[gaintype, "-s", "s", "-d", str(args.volume-89.0), "-c", "-p"]

    global MP3ValExe, MP3ValArgs
    MP3ValExe="/usr/bin/mp3val"
    MP3ValArgs=["-f", "-nb", "-t"]

    global MP3PackerExe, MP3PackerArgs
    MP3PackerExe="/usr/bin/mp3packer"
    MP3PackerArgs=["-a", FailedPackExtension, "--keep-ok", "out", "--keep-bad", "both", "-z", "--process", "sse41", "--copy-time", "-f", "-u"]

    # Prepend "echo" to all the commands if we're doing a dry-run
    if args.dryrun:
        print("***Dry run - not executing***")
        DryMP3ValArgs=[MP3ValExe]+MP3ValArgs
        MP3ValArgs=DryMP3ValArgs
        MP3ValExe="/bin/echo"

        DryMP3PackerArgs=[MP3PackerExe]+MP3PackerArgs
        MP3PackerArgs=DryMP3PackerArgs
        MP3PackerExe="/bin/echo"

        DryMP3GainArgs=[MP3GainExe]+MP3GainArgs
        MP3GainArgs=DryMP3GainArgs
        MP3GainExe="/bin/echo"

    print("Using MP3Val command: "+MP3ValExe+" "+' '.join(MP3ValArgs))
    print("Using MP3Packer command: "+MP3PackerExe+" "+' '.join(MP3PackerArgs))
    print("Using MP3Gain command: "+MP3GainExe+" "+' '.join(MP3GainArgs))
    print("Normalizing to: "+str(args.volume)+"dB")

    if args.processes:
        NumProcesses=args.processes
    print("Concurrent Processes: "+str(NumProcesses))

    if args.directory:
        TopDirectory=args.directory
    print("Starting Directory: "+TopDirectory)

    if args.output:
        OutputFile=args.output
    print("Output File: "+OutputFile)

    mp3files=find_files(TopDirectory,MP3Extension)
    directories=find_directories(mp3files)

    # Open file for output
    # ToDo: Make this conditional on there BEING any output
    with open(OutputFile, 'w') as f:

        if args.skipval:
            print("Skipping MP3Val")
        else:
            pool_output=run_val_parallel(NumProcesses,mp3files)
            save_output(f,pool_output)

        if args.skippack:
            print("Skipping MP3Packer")
        else:
            pool_output=run_pack_parallel(NumProcesses,mp3files)
            save_output(f,pool_output)

        if args.skipgain:
            print("Skipping MP3Gain")
        else:
            pool_output=run_gain_parallel(NumProcesses,directories)
            save_output(f,pool_output)

    f.closed

    # Search for any files that failed mp3packer
    packfailfiles=find_files(TopDirectory,"*"+FailedPackExtension+"*")

    if packfailfiles:
        print("****Failed files to examine:****")
        for failfile in packfailfiles:
            print(failfile)
    else:
        print("Fixup successful!")

main()
