import os
import os.path
import re
import Globals
import Helpers
import ExtractNamesFromText

# Take a file's pathname and, if it's a format we can handle, create a list of names found in it.
# We return a list of tuples (name, filepath)
# Otherwise, we return None
def processFile(dirRelPath: str, pname: str, fname: str, information: dict):

    # If we encounter them, skip the existing names index files!
    if re.match("^names-[a-zA-Z]{1,2}\.html$", fname):
        return None

    fullpath=os.path.join(dirRelPath, fname)
    relpathname=os.path.join(pname, fname)

    # We handle different file type differently.
    ext=os.path.splitext(fullpath)[1].lower()
    if ext in [".txt", ".html"]:    # The text file types
        with open(fullpath, "rb") as f:  # Reading in binary and doing the funny decode is to handle special characters embedded in some sources.
            source=f.read().decode("cp437")
        info=scanTextForInformation(source, dirRelPath, fname)
        if info is not None:
            information[relpathname]=info
        listOfNamesFound=ExtractNamesFromText.extractNamesFromText(source, relpathname)
        if listOfNamesFound is None or len(listOfNamesFound) == 0:
            return None

        # We also need to figure out what kind of page this is.
        # Right now, we'll look for two types:
        #   A standard fanzine page html file
        #       This is a specific kind of HTML page which frames a jpg.
        #       We look for some HTML which is standard on these pages
        #   Everything else
        prefix=""
        issueno=""
        pageno=""
        if source.find(r'<TABLE ALIGN="center" CLASS="navbar"><TR>') > -1 and \
                source.find(r'<TD CLASS="navbar"><FORM ACTION="/map.html"><INPUT TYPE="submit" VALUE="Site Map"></FORM>') > -1:
            # OK, this is probably a standard fanzine page
            # So we try to decode the name, which will (hopefully) be of the form <name><issue>-<page>.html
            m=re.match(r"^(.+?)(\d+)-(.+)\.html$", fname)
            if m is not None:
                prefix=m.groups()[0]
                issueno=m.groups()[1]
                pageno=m.groups()[2]
                print(m.groups()[0]+"  #"+m.groups()[1]+"  page "+m.groups()[2])

        return [(name, relpathname, pname, prefix, issueno, pageno) for name in listOfNamesFound]

    elif ext == ".pdf":
        return None    # Can't handle this yet

    return None


#***************************************************************************************
# Scan text for information useful for deciding what a given page references pertains to
def scanTextForInformation(source: str, dirRelPath: str, fname: str):
    fanzineName=None
    # If this is a fanzine, is it an index page?
    if dirRelPath.find("\\public\\fanzines\\") > -1 and fname == "index.html":
        # The page usually gives the fanzine name at the top, usually as the first line of an H2 block.
        match=re.search(r"(?i)<h2>(.*?)</h2>", source)
        if match is not None and len(match.groups()) == 1:
            s=match.groups()[0]
            if s.find("<br>") > -1:
                s=s.split("<br>")
            else:
                s=s.split("<BR>")
            fanzineName=s[0]

        # Now look for the table which will give an issue name and a link to the first page

    return (fanzineName)




#***************************************************************************************
#***************************************************************************************
# Main

# Read in the people names table from Fancyclopedia 3.  This will provide a rich set of names to look for in Fanac.org
print("Reading Fancy names")
fancyNamesPath=r"..\FancyNameExtractor\Peoples names.txt"
with open(fancyNamesPath, "r") as f:
    peopleNames=f.readlines()
peopleNames=[x[:-1] for x in peopleNames]

# We need to turn this into a form which can be efficiently searched.
# We'll tokenize the names, and create a list of names as the values of a dictionary based on the first token.
# The names themselves will be lists of the remaining tokens
print("Creating names sets")
information={}
for name in peopleNames:
    parts=name.split()
    if len(parts) > 1:
        if parts[0] not in Globals.gFancyPeopleNamesDict2.keys():
            Globals.gFancyPeopleNamesDict2[parts[0]]=[]
        Globals.gFancyPeopleNamesDict2[parts[0]].append(parts[1:])
    else:
        if parts[0] not in Globals.gFancyPeopleNamesDict1.keys():
            Globals.gFancyPeopleNamesDict1[parts[0]]=[]
        Globals.gFancyPeopleNamesDict1[parts[0]].append(parts[1:])

    partsL=[p.lower() for p in parts]
    if len(partsL) < 2:
        continue
    fnameIndex=0
    if partsL[fnameIndex] == "dr":
        fnameIndex=1
    lnameIndex=len(partsL)-1
    if partsL[lnameIndex].lower() in ["ii", "iii", "iv", "phd", "md", "jr", "sr", "m d"]:
        lnameIndex-=1
    Globals.gFancyPeopleFnames.add(parts[fnameIndex])
    Globals.gFancyPeopleLnames.add(parts[lnameIndex])    # Note that this messes up on last names like "de Camp"


# Remove a few particular problem names.
# We have separate lists because some common words which can show up as a name in Fancy may sometimes be inappropriate for use in free text scanning
generalSkiplist={"Fan", "Vol", "Who", "Page", "The", "Mr", "Mrs", "Ms", "Miss", "Dr", "Con", "Hugo", "They", "That", "What", "If", "Science", "Fiction", "MIT",
                 "Research", "Sir", "Abbey", "Editor", "Updated", "Toastmaster", "Award", "Fanzine", "Month", "Year", "August", "May", "November", "Cover"}

Globals.gFancyPeopleFnames=Globals.gFancyPeopleFnames-generalSkiplist
Globals.gFancyPeopleFnames=Globals.gFancyPeopleFnames.union(set())      # First names that need to be added
Globals.gFancyPeopleLnames=Globals.gFancyPeopleLnames-generalSkiplist

# .............
# Read the Weird Cases info table
print("Reading Weird Cases file")
fancyNamesPath=r"Weird Cases.txt"
with open(fancyNamesPath, "r") as f:
    weirdcasestext=f.readlines()
weirdcasestext=[d[:-1] for d in weirdcasestext if len(d) > 0 and d[0] != "#"]  # Ignore comment lines and trailing "\n"
for w in weirdcasestext:
    w=[x.strip() for x in w.split("|")]     # Split the line on the "|" and strip excess spaces
    if len(w) == 2:
        # Because directory separates then to get a bit confused, we'll control one where the separator is a single forward slash
        Globals.gWeirdCases[Helpers.PathNorm(w[0])]=w[1]


#.............
# Read the Fanac.org directory info table
print("Reading Fanac directory info file")
fancyNamesPath=r"Directory info.txt"
with open(fancyNamesPath, "r") as f:
    directoryInfoText=f.readlines()
directoryInfoText=[d[:-1] for d in directoryInfoText if len(d) > 0 and d[0] != "#"]  # Ignore comment lines and trailing "\n"
directoryInfo={}
for dir in directoryInfoText:
    # A line can be of these forms:
    # path
    # path | keyword
    # path | keyword {text}
    # and any of them could have a trailing comment starting ##
    if dir.find("##") > -1:
        dir=dir.split("##")[0].strip()
    match=re.match("^(.+)\|\s*([a-zA-Z]+)\s*{(.+)}\s*$", dir)
    if match is not None and len(match.groups()) == 3:
        directoryInfo[match.groups()[0].strip()]=(match.groups()[1], match.groups()[2])
        continue
    match=re.match("^(.+)\|\s*([a-zA-Z]+)\s*$", dir)
    if match is not None and len(match.groups()) == 2:
        directoryInfo[match.groups()[0].strip()]=(match.groups()[1], None)
        continue
    directoryInfo[dir]=(None, None)


print("Walking Fanac.org directory tree")
fanacRootPath=r"H:\fanac.org\public" #Q:\Bulk storage\fanac.org backups\fanac.org\public
#fanacRootPath="Q:\\fanac.org\\public"
references=[]
skippers=["_private", "stats", "ZipDisks", "backup2", "NewStuff", "cgi-bin", "PHP-Testing"]
tempSkippers=["conjose", "Denvention3"]

# Recursively walk the directory tree under fanacRootPath
for dirName, subdirList, fileList in os.walk(fanacRootPath):
    # Get the pathname starting from the public directory
    relpath=dirName.replace(fanacRootPath, "")
    pathcomponents=(relpath).split(os.path.sep)
    if len(pathcomponents) > 1 and pathcomponents[1] in tempSkippers:
        continue
    if len(pathcomponents) > 1 and pathcomponents[1] in skippers:
        print("Skipping directory: "+relpath)
        continue
    if relpath in directoryInfo.keys():
        if directoryInfo[relpath][0] == "Ignore":
            print("Ignoring directory: "+relpath)
            continue
    print('Processing directory: %s' % dirName)

    if relpath == "":   # Ignore files in the root
        continue

    # Walk the files in this directory
    for fname in fileList:
        #if fname != "and remove this.txt":
            #continue
        rslt=processFile(dirName, relpath, fname, information)
        if rslt is not None:
            references.extend(rslt)

# And write the results
with open("Fanac name references.txt", "w+") as f:
    f.write("# <person's name> | <file name> | <path relative to public>\n\n")
    for name, relname, directory, prefix, issueno, pageno in references:
        path, file=os.path.split(relname)
        if len(directory) > 0:
             if path != directory:
                 print("path='"+path+"'  and directory='"+directory+"'")
        f.write(name+" | "+file+" | " + directory +" | " + prefix+" | " + issueno+" | " + pageno+ "\n")

with open("Fanac information.txt", "w+") as f:
    f.write("# path | landing page | display name\n\n")
    for path, data in information.items():
        path, file=os.path.split(path)
        f.write(path+" | " + file + " | " + data+"\n")
i=0