import sys
import shutil
import mutator

import python_handler
import python3_handler
import c_handler
import cpp_handler
import java_handler
import swift_handler
import rust_handler
import subprocess

import os

def nullHandler(tmpMutantName, mutant, sourceFile, uniqueMutants):
    return "VALID"

def cmdHandler(tmpMutantName, mutant, sourceFile, uniqueMutants):
    global cmd

    with open(".um.mutant_output",'w') as file:
        r = subprocess.call([cmd.replace("MUTANT",tmpMutantName)],shell=True,stderr=file,stdout=file)
    if r == 0:
        return "VALID"
    else:
        return "INVALID"

def main():
    global cmd

    try:
        import custom_handler
    except:
        pass

    args = sys.argv
    
    if "--help" in args:
        print "USAGE: mutate <sourcefile> [<language>] [<rule1> <rule2>...] [--noCheck] [--cmd <command string>] [--mutantDir <dir>] [--lines <coverfile> [--tstl]]"
        print "       --noCheck: skips compilation/comparison and just generates mutant files"
        print "       --cmd executes command string, replacing MUTANT with the mutant name, and uses return code"
        print "             to determine mutant validity"
        print "       --mutantDir: directory to put generated mutants in; defaults to current directory"
        print "       --lines: only generate mutants for lines contained in <coverfile>"
        print "       --tstl: <coverfile> is TSTL output"
        sys.exit(0)

    noCheck = False
    if "--noCheck" in args:
        noCheck = True
        args.remove("--noCheck")

    cmd = None
    try:
        cmdpos = args.index("--cmd")
    except ValueError:
        cmdpos = -1
        
    tstl = False
    if "--tstl" in args:
        tstl = True
        args.remove("--tstl")

    if cmdpos != -1:
        cmd = args[cmdpos+1]
        args.remove("--cmd")
        args.remove(cmd)

    sourceFile = args[1]
    ending = "." + sourceFile.split(".")[-1]
        
    lineFile = None
    try:
        linepos = args.index("--lines")
    except ValueError:
        linepos = -1
        
    if linepos != -1:
        lineFile = args[linepos+1]
        args.remove("--lines")
        args.remove(lineFile)

    if lineFile != None:
        with open(lineFile) as file:
            if not tstl:
                lines = map(int,file.read().split())
            else:
                lines = []
                for l in file:
                    if "LINES" in l:
                        if sourceFile not in l:
                            continue
                        db = l.split("[")[1]
                        d = db[:-2].split(",")
                        for line in d:
                            lines.append(int(line))

    mdir = ""
    try:
        mdirpos = args.index("--mutantDir")
    except ValueError:
        mdirpos = -1
        
    if mdirpos != -1:
        mdir = args[mdirpos+1]
        args.remove("--mutantDir")
        args.remove(mdir)
        mdir += "/"

    handlers = {"python": python_handler,
                "python3": python3_handler,
                "c": c_handler,
                "c++": cpp_handler,
                "cpp": cpp_handler,            
                "java": java_handler,
                "swift": swift_handler,
                "rust": rust_handler}

    languages = {".c": "c",
                 ".cpp": "cpp",
                 ".c++": "cpp",             
                 ".py": "python",
                 ".java": "java",
                 ".swift": "swift"
                 ".rs": "rust"}    

    cLikeLanguages = ["c", "java", "swift", "cpp", "c++", "rust"]

    try:
        handlers["custom"] == "custom_handler"
    except:
        pass

    sourceFile = args[1]
    ending = "." + sourceFile.split(".")[-1]

    if len(args) < 3:
        language = languages[ending]
        otherRules = []
    else:
        language = args[2]
        otherRules = args[3:]

    base = (".".join((sourceFile.split(".")[:-1]))).split("/")[-1]

    if language in cLikeLanguages:
        otherRules.append("c_like.rules")

    rules = ["universal.rules",language + ".rules"] + otherRules

    source = []

    with open(sourceFile,'r') as file:
        for l in file:
            source.append(l)

    mutants = mutator.mutants(source, rules = rules)

    print len(mutants),"MUTANTS GENERATED BY RULES"

    validMutants = []
    invalidMutants = []
    redundantMutants = []
    uniqueMutants = {}

    if not noCheck:
        if cmd != None:
            handler = cmdHandler
        elif language == "none":
            handler = nullHandler
        else:
            handler = handlers[language].handler
    else:
        handler = nullHandler

    mutantNo = 0
    for mutant in mutants:
        if (lineFile != None) and mutant[0] not in lines:
            # skip if not a line to mutate
            continue
        tmpMutantName = "tmp_mutant" + ending
        print "PROCESSING MUTANT:",str(mutant[0])+":",source[mutant[0]-1][:-1]," ==> ",mutant[1][:-1],"...",
        mutator.makeMutant(source, mutant, tmpMutantName)
        mutantResult = handler(tmpMutantName, mutant, sourceFile, uniqueMutants)
        print mutantResult,
        mutantName = mdir + base + ".mutant." + str(mutantNo) + ending
        if mutantResult == "VALID":
            print "[written to",mutantName+"]",
            shutil.copy(tmpMutantName, mutantName)
            validMutants.append(mutant)
            mutantNo += 1
        elif mutantResult == "INVALID":
            invalidMutants.append(mutant)
        elif mutantResult == "REDUNDANT":
            redundantMutants.append(mutant)
        print

    print len(validMutants),"VALID MUTANTS"
    print len(invalidMutants),"INVALID MUTANTS"
    print len(redundantMutants),"REDUNDANT MUTANTS"

if __name__ == '__main__':
    main()

