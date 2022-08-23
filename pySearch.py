import argparse, sys
import time, datetime
import re
import shutil
import os, platform
from os import walk
import re
import shlex

#TODO list:
# * - number of context lines isn't implemented yet
# * - Handle files with no extension - keyword __NONE__?
# * - Argparser help shouldn't print the name of the calling script - needs to always be pySearch
# * - Init with string for arguments doesn't work
# * - type parameter instead -df
# * - instead of passing around 'args', define self variables for all options
# * - implement contents for directory search

#------------------------------------------
# ARGUMENTS
#    source (positional) - Source directory from which to search
#    -name      a string the name of the file must contain
#    -contents  a string that should appear in the contents of the file. If searching for directories, contents matches filenames in the directory
#    -maxCont   a number - maximum number of content matches to return for a given file. Default is 5. Set to 0 for no limit.
#    -after     the earliest time stamp to return files for, e.g. 1/01/2022:9:1
#    -before    the latest time stamp to return files for, e.g. 05/11/2022:16:05
#    -within    sets the timestamp min (after arg) relative to current time, e.g. -within 5min, -within 1.3hr, -within 45sec -within 5day
#    -ext       Comma-separated list of file extensions to include (all others ignored). Can not be used with Xext
#    -Xext      Comma-separated list of file extensions to ignore. Can not be used with ext
#    -context   number of context lines to display when searching contents (files only) (not implemented yet)
#    -c         Perform a case-sensitive search
#    -e         Exact name match - matches full file/directory name. Matching is not case sensitive without specifying -c also
#    -f         Search for files (defaults to true)
#    -d         Search for directories (defaults to false)
#    -q         Quiet mode (don't show file access errors, etc)
#    -r         Regex search

class pySearch:

    def __init__(self, argString=None):
        self.defaultContextLines = 2
        self.maxContentMatches = 5
        self.createtArgParser()
        if argString == None:
            self.args = self.parser.parse_args()
        else:
            self.args = parser.parse_args(shlex.split(argString))
        
        #display file access errors?
        self.quietMode = self.args.q
        
        #results object init
        self.results = searchResults()

        #Max content lines
        if self.args.maxCont != None:
            if re.compile('\d+').match(self.args.maxCont) == None:
                sys.exit('Invalid value for maxCont. maximum number of content matches should be a non-negative integer')
            self.maxContentMatches = int(self.args.maxCont)
        
        #Check that context lines makes sense
        if self.args.context != None:
            if re.compile('\d+').match(self.args.context) == None:
                sys.exit('Invalid value for context. Number of context lines should be an integer less than 11')
            self.results.setNumContextLines(float(self.args.context))
        else:
            self.results.setNumContextLines(float(self.defaultContextLines))

        # Are we looking for files, directories, both?
        self.filesFlag = self.args.f or (not self.args.f and not self.args.d) #if neither -f or -d is specified, searchf or files
        self.directoriesFlag = self.args.d

        #Which directory are we looking in?
        self.source = self.args.source

        #Construct the name search string
        self.searchName = self.args.name
        if self.searchName != None:
            if not self.args.c:
                self.searchName = self.searchName.lower()

        #Process contents search string
        self.searchContents = self.args.contents
        if self.searchContents != None:
            if not self.args.c:
                self.searchContents = self.searchContents.lower()

        #Catch some incompatible choices:
        if self.args.r and self.args.e:
            sys.exit('Unable to perform an exact search AND a regex search; choose one.')

        #Process the timestamp arguments
        self.processTimeStampArgs()
        
        #Extension options
        self.processExtensionArgs()

    def __call__(self):
        #Actual search happens here
        for (dirpath, dirnames, filenames) in walk(self.source):
            if (self.filesFlag and len(filenames) > 0):
                for filename in filenames:
                    self.checkFile(dirpath, filename)
                    
            if (self.directoriesFlag and len(dirnames) > 0):
                for dirname in dirnames:
                    self.checkDirectory(dirpath, dirname)
        self.results.display(self.filesFlag,self.directoriesFlag)

    def createtArgParser(self):
        self.parser = argparse.ArgumentParser(description='Search for files and/or folders')
        self.parser.add_argument('source', help='Source directory from which to search')
        self.parser.add_argument('-name', help='Specify a string the name of the file must contain', required=False)
        self.parser.add_argument('-contents', help='Specify a string that should appear in the contents of the file. If searching for directories, contents matches filenames in the directory (i.e. only return directories that contain files with names matching contents)', required=False)
        self.parser.add_argument('-maxCont', help='A number - maximum number of content matches to return for a given file. Default is 5. Set to 0 for no limit.', required=False)
        self.parser.add_argument('-after', help='Specify the earliest time stamp to return files for, e.g. 1/01/2022:9:1')
        self.parser.add_argument('-before', help='Specify the latest time stamp to return files for, e.g. 05/11/2022:16:05')
        self.parser.add_argument('-within', help='Set timestamp min relative to current time, e.g. -within 5min, -within 1.3hr, -within 45sec -within 5day')
        self.parser.add_argument('-ext', help='Comma-separated list of file extensions. Can not be used with Xext', required=False)
        self.parser.add_argument('-Xext', help='Comma-separated list of file extensions to exclude. Can not be used with ext', required=False)
        self.parser.add_argument('-context', help='Number of context lines to display when searching contents.')
        self.parser.add_argument('-c', help='Perform a case-sensitive search', action='store_true')
        self.parser.add_argument('-e', help='Exact name match - matches full file/directory name. Matching is not case sensitive without specifying -c also.', action='store_true')
        self.parser.add_argument('-f', help='Search for files (defaults to true)', action='store_true')
        self.parser.add_argument('-d', help='Search for directories (defaults to false)', action='store_true')
        self.parser.add_argument('-q', help='Quiet mode', action='store_true')
        self.parser.add_argument('-r', help='Regex search', action='store_true')

    # Determine if a file meets the criteria of the search 
    def checkFile(self, path, name):       
        #Initialize the foundFileObject to (possibly) return
        thisFile = foundFileObject("file",name,path,self)
        
        #Check the file extensions
        if len(self.ext) > 0:
            if not thisFile.ext in self.ext:
                return False
        elif len(self.Xext) > 0:
            if thisFile.ext in self.Xext:
                return False
        
        #First do a name check (returns true if no name argument was passed in)
        if not self.checkName(name):
            return False

        #Check if timestamp meets criteria
        if not self.checkTimeStamp(thisFile.ts):
            return False

        #Check file contents
        if not self.checkFileContents(thisFile,self.results):
            return False

        self.results.addFile(thisFile)
        thisFile.display()
        return True

    # Determine if a directory meets the criteria of the search 
    def checkDirectory(self, path, name):
        #Initialize the foundFileObject to (possibly) return
        thisDir = foundFileObject("directory",name,path,self)
        
        #First do a name check (returns true if no name argument was passed in)
        if not self.checkName(name):
            return False

        #Check if timestamp meets criteria
        if not self.checkTimeStamp(thisDir.ts):
            return False

        self.results.addDir(thisDir)
        thisDir.display()
        return True

    # Determine if a file/directory name meets the criteria of the search 
    def checkName(self, name):
        match = True
        if self.searchName != None:
            matchName = name
            if not self.args.c:
                matchName = matchName.lower()
            if self.args.r:
                regExp = re.compile(self.searchName)
                return regExp.search(name) != None
            if self.args.e:
                match = (self.searchName == matchName)
            else:
                match = self.searchName in matchName
                
        return match

    #Check time stamp
    def checkTimeStamp(self, ts):
        if self.timeMinValue != None:
            if not ts > self.timeMinValue:
                return False
        if self.timeMaxValue != None:
            if not ts < self.timeMaxValue:
                return False
        return True

    #Check file contents for match.
    def checkFileContents(self, fileObj, resultsObj):
        match = True
        if self.searchContents != None:
            match = False
            try:
                searchfile = open(fileObj.fullQualPath, "r")
            except OSError as error:
                if not self.quietMode:
                    print(error)
                return False
            try:
                numMathes = 0
                for lineNo,line in enumerate(searchfile,1):
                    #print("Line is: \n   {}\nSearch string is:\n{}".format(line,self.searchContents))
                    # Not implemented yet
                    # if resultsObj.getNumContextLines() > 0:
                    if self.checkFileContentsLine(line):
                        match = True
                        numMathes += 1
                        fileObj.addContentMatch(lineNo,[line])
                        if self.maxContentMatches > 0 and numMathes >= self.maxContentMatches:
                            fileObj.addNote("possibly more content matches - stopped after {} matches".format(numMathes))
                            break
            except:
                if not self.quietMode:
                    print("Unable to read contents of {}".format(fileObj.fullQualPath))
                match = False
            finally:
                searchfile.close()
        return match

    def checkFileContentsLine(self, line):
        # return (re.compile('self.searchContents').match(line) != None)
        if not self.args.c:
            line = line.lower()
        if not self.args.r:
            return self.searchContents in line 
        else:
            #regex search
            regExp = re.compile(self.searchContents)
            if regExp.search(line) != None:
                print(line)
                return True

    def processTimeStampArgs(self):
        self.timeMinValue = None
        self.timeMaxValue = None
        if self.args.within != None:
            #Can't have within AND (before/after) self.args
            if (self.args.after != None or self.args.before != None):
                sys.exit("Use of 'within' option not compatible with 'after' and 'before'")

            #Based on current time, get a timeMinValue 
            currentTime = time.time()
            value = re.compile('\d*\.?\d+').match(self.args.within).group()
            unit = re.compile('[\d\.]+([a-zA-Z]+)').match(self.args.within).group(1)
            mult = None
            if unit.lower() == "sec":
                mult = 1
            elif unit.lower() == "min":
                mult = 60
            elif unit.lower() == "hr":
                mult = 3600
            elif unit.lower() == "day":
                mult = 86400
            else:
                sys.exit("Invalid value for -within; {}. See help for usage".format(unit))
            try:
                value = float(value)
            except:
                sys.exit("Invalid value for -within. See help for usage")
            self.timeMinValue = currentTime - value*mult

        #Convert before and after argf to numeric timestamps (number of seconds since Dec 31, 1969)
        if self.args.after != None:
            self.validateTimeArg("after")
            timeMin = self.args.after.split(":")
            dateMin = timeMin[0]
            hourMin = 0
            minMin = 0
            if len(timeMin) > 1:
                hourMin = float(timeMin[1])
                minMin = float(timeMin[2])
            self.timeMinValue = time.mktime(datetime.datetime.strptime(dateMin, "%d/%m/%Y").timetuple()) + hourMin*60*60 + minMin*60
        if self.args.before != None:
            self.validateTimeArg("before")
            timeMax = self.args.before.split(":")
            dateMax = timeMax[0]
            hourMax = 0
            minMax = 0
            if len(timeMax) > 1:
                hourMax = float(timeMax[1])
                minMax = float(timeMax[2])
            self.timeMaxValue = time.mktime(datetime.datetime.strptime(dateMax, "%d/%m/%Y").timetuple()) + hourMax*60*60 + minMax*60

    def processExtensionArgs(self):
        self.ext = []
        self.Xext = []
        if self.args.ext != None and self.args.Xext != None:
            sys.exit('ext and Xext options can not both be specified')
        if self.args.ext != None:
            self.ext = self.args.ext.split(",")
        if self.args.Xext != None:
            self.Xext = self.args.Xext.split(",")

    #Validate before / after arguments (d/m/yyyy:h:m)
    #Valid value examples:
    #   1/1/2000:9:1
    #   05/11/2022:16:05 
    def validateTimeArg(self,argName):
        if re.compile('\d\d?/\d\d?/\d\d\d\d:\d\d?:\d\d?').match(getattr(self.args,argName)) == None:
            sys.exit("Invalid value for '{}': {}\n{}".format(argName,getattr(self.args,argName),self.parser.format_help()))

class foundFileObject:
    def __init__(self,type,name,path,searchObject):
        self.name = name
        self.path = path
        self.quietMode = searchObject.quietMode
        self.notes = []
        
        #Get the full file path (e.g. replace ~ with /usr/myName)
        self.fullPath = os.path.abspath(path)
        #\\?prefix to an absolute path in Windows to handle extended path lengths
        if platform.system().lower() == 'windows':
            self.fullPathExtended = '\\\\?\\'+self.fullPath
        else:
            self.fullPathExtended = self.fullPath
        #Fully qualified path (includes name)
        self.fullQualPath = os.path.join(self.fullPathExtended,self.name)
            
        #file object type (directory or file)
        self.type = type
        self.valid_types=["file","directory"]
        if not self.type in self.valid_types:
            sys.exit("The foundFileObject type \"{}\" is not valid. Valid types are: \"{}\"".format(self.type,self.valid_types))
         
        #get the timestamp for this file
        self.ts = self.getTimeStamp()
        if self.ts == None:
            return None
        self.timestampString = datetime.datetime.fromtimestamp(self.ts).strftime('%Y-%m-%d %H:%M:%S')
        
        if self.type == "file":
            #get the file extension
            self.ext = ""
            ind = self.name.rfind(".")
            if ind < len(self.name) -1:
                self.ext = self.name[ind+1:]
            
            #Initialize context lines
            self.lineMatchNums = []
            self.contextLines = {}
            self.contextLines['numContextLines'] = searchObject.results.getNumContextLines()
            

    def getTimeStamp(self):
        try:
            ts = os.path.getmtime(self.fullQualPath)
            return ts
        except OSError as error:
            if not self.quietMode:
                print(error)
            return None

    def addContentMatch(self,lineNo,contextLines):
        self.lineMatchNums.append(lineNo)
        self.contextLines[lineNo] = contextLines
    
    def addNote(self, theNote):
        self.notes.append(theNote)
    
    def display(self):
        print("{}\t{}".format(os.path.join(self.fullPath,self.name),self.timestampString))
        if self.type == "file":
            for lineNo in self.lineMatchNums:
                print("   {}: {}".format(lineNo,self.contextLines[lineNo]))
        for note in self.notes:
            print("   -"+note)

#Collection of all search results
class searchResults:
    def __init__(self):
        self.fileMatches = []
        self.dirMatches = []
        self.numContextLines = 0
    def setNumContextLines(self,numContextLines):
        self.numContextLines = numContextLines
    def getNumContextLines(self):
        return self.numContextLines
    def addFile(self,newFile):
        self.fileMatches.append(newFile)
    def addDir(self,newDir):
        self.dirMatches.append(newDir)
    def display(self,filesFlag,dirsFlag):
        if filesFlag:
            print("Matched {} file(s)".format(len(self.fileMatches)))

        if dirsFlag:
            print("{} directory matches".format(len(self.dirMatches)))


def main():
    performSearch = pySearch()
    performSearch()
    
if __name__ == "__main__":
    main()