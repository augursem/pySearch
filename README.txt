OVERVIEW
	pySearch is a command line file search utility. It was built specifically for use on Windows, as I always found the native 
	command line file search utilities there to be less than useful. It searches for files and directories by name, date modified,
	and also by the contents of the file / directory. It allows for inexaxct name matching and regex matching.

"INSTALLING"
The entire search functionality is in a single python script at the moment, so using pySearch is as simple as having Python installed
and saving the file pySearch.py somewhere. 

To enable searching from Windows using the pySearch script without having to type 'Python pySearch.py ...'  you can do the following:
	1) Determine the path to your Python executable, e.g. C:\<path to Python install>\python.exe
		C:\>where Python
		C:\Users\steve\AppData\Local\Programs\Python\Python310\python.exe
	2) Still using command line, execute 'assoc .py=Python' and then 'ftype Python="C:\<path to Python install>\python.exe" "%1" %*
		C:\Windows\System32>assoc .py=Python
        .py=Python
		
		C:\> ftype Python="C:\<path to Python install>\python.exe" "%1" %*
		Python="C:\<path to Python install>\python.exe" "%1" %*
		
	3) Add '.py' to the PATHEXT system variable
	
	4) Add the full path to the folder where pySearch.py is saved to your PATH variable. If you save in the Python 'Scripts' folder, 
	   it should already be part of the path

	You should now be able to search from the command line using pySearch directly, e.g. 
		C:\GitRepos\pySearch\Test>pySearch . -name abc
		C:\GitRepos\pySearch\Test\abc.docx      2022-08-19 16:55:46
		C:\GitRepos\pySearch\Test\abc.txt       2022-08-19 16:54:14
		Matched 2 file(s)
		
USAGE
	C:\>pySearch -h
	usage: pySearch.py [-h] [-name NAME] [-contents CONTENTS] [-maxCont MAXCONT] [-after AFTER] [-before BEFORE]
					   [-within WITHIN] [-ext EXT] [-Xext XEXT] [-context CONTEXT] [-c] [-e] [-f] [-d] [-q] [-r]
					   source

	Search for files and/or folders in 'source' and all subdirectories of 'source'

	positional arguments:
	  source              Source directory from which to search

	options:
	  -h, --help          show this help message and exit
	  -name NAME          Specify a string the name of the file must contain
	  -contents CONTENTS  Specify a string that should appear in the contents of the file. If searching for
						  directories, contents matches filenames in the directory (i.e. only return directories that
						  contain files with names matching contents)
	  -maxCont MAXCONT    A number - maximum number of content matches to return for a given file. Default is 5. Set to
						  0 for no limit.
	  -after AFTER        Specify the earliest time stamp to return files for, e.g. 1/01/2022:9:1
	  -before BEFORE      Specify the latest time stamp to return files for, e.g. 05/11/2022:16:05
	  -within WITHIN      Set timestamp min relative to current time, e.g. -within 5min, -within 1.3hr, -within 45sec
						  -within 5day
	  -ext EXT            Comma-separated list of file extensions. Can not be used with Xext
	  -Xext XEXT          Comma-separated list of file extensions to exclude. Can not be used with ext
	  -context CONTEXT    Number of context lines to display when searching contents.
	  -c                  Perform a case-sensitive search
	  -e                  Exact name match - matches full file/directory name. Matching is not case sensitive without
						  specifying -c also.
	  -f                  Search for files (defaults to true)
	  -d                  Search for directories (defaults to false)
	  -q                  Quiet mode
	  -r                  Regex search
	  
EXAMPLES
	Search for all files with a '.json' extension in the current directory (and all subdirectories):
		pySearch . -ext json
		
	Search for all files with "help" in the name, ignoring case, in the C:\Users folder (and all subdirectories):
		pySearch  C:\Users -name help
		
	Search for all files containing the text 'pySearch' in a case-sensitive way
		pySearch . -contents pySearch -c
		
	Search for all files on the C:\ drive modified within the last hour:
		pySeach C:\ -within 1hr
		
		