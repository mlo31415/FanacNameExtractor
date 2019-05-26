import os
import os.path
import re


# Take a file's pathname and, if it's a format we can handle, create a list of names found in it.
# We return a list of tuples (name, filepath)
def processFile(dirname: str, pname: str, fname: str, peopleNamesDict: dict):

    # Skip the existing names index files!
    if re.match("^names-[a-zA-Z]{1,2}\.html$", fname):
        return None

    fullpath=os.path.join(dirName, fname)
    relpath=os.path.join(pname, fname)

    textTypes=[".txt", ".html"]
    ext=os.path.splitext(fullpath)[1].lower()
    if ext in textTypes:
        with open(fullpath, "rb") as f:  # Reading in binary and doing the funny decode is to handle special characters embedded in some sources.
            source=f.read().decode("cp437")
        rslt=processText(source, peopleNamesDict)
        if rslt is None:
            return None
        return [(r, relpath) for r in rslt]
    elif ext == ".pdf":
        return None    # Can't handle this yet
    return None


#..................................................................
# Take a string and return a list of all the unique recognized names in it.
def processText(contents: str, peopleNamesDict: dict):
    namesFound=[]

    # We tokenize the input string breaking on whitespace.
    # Then we search it looking for matches to peopleNamesDict.  We add the match to namesFound and remove it from the string.
    input=contents.split()
    i=0
    while i<len(input):
        try:
            peopleNamesList=peopleNamesDict[input[i]]
        except:
            i+=1    # No match.  Go to the next token and try again.
            continue

        # We have a token match to the start of a name.  Run through the list of trailing tokens for each name to see if any of them also match
        for peopleName in peopleNamesList:
            ln=len(peopleName)
            if ln == 0:     # It's a one-token name
                namesFound.append(input[i])
                input[i]=""
                break
            elif input[i+1 : i+1+ln] == peopleName:     # A hit!
                namesFound.append(" ".join(input[i:i+ln+1]))
                for j in range(ln+1):
                    input[i+j]=""
                i+=ln
                break
            else:
                pass    # No Match. Go on to the next name in the list
        i+=1

    # All done. Reassemble the string for we can use another method on what's left.
    contents=" ".join(input)

    # We'll start by looking for strings of the form <uc character><span(alpha)><whitespace><uc character>.<whitespace><uc character><span(alpha)>
    # (If we're going to do any further processing, we should use sub() to drop the names we have found from the input before the nest stop or we'll get dups.)
    pattern=re.compile("([A-Z][a-z]*\s+[A-Z]\.\s+[A-Z][a-z]+)")
    matches=re.findall(pattern, contents)
    if matches is None or len(matches) == 0:
        return None
    for match in matches:
        # Some names will include newlines and the like.  Turn all spans of whitespace into a single space
        match=re.sub("\s+", " ", match)
        namesFound.append(match)

    # Remove duplicates
    return list(set(namesFound))


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
print("Creating names dictionary")
peopleNamesDict={}
for name in peopleNames:
    name=name.split()
    if name[0] not in peopleNamesDict.keys():
        peopleNamesDict[name[0]]=[]
    peopleNamesDict[name[0]].append(name[1:])

print("Walking Fanac.org directory tree")
fanacRootPath="O:\\Bulk storage\\fanac.org backups\\fanac.org\\public"
namePathPairs=[]
skippers=["_private", "stats", "ZipDisks", "Sasquan", "Aussiecon4", "Denvention3", "Intersection", "backup2", "Anticipation", "conjose", "NewStuff"]

# Recursively walk the directory tree under fanacRootPath
for dirName, subdirList, fileList in os.walk(fanacRootPath):
    # Get the pathname starting from the public directory
    relpath=dirName.replace(fanacRootPath, "")
    pathcomponents=(relpath).split(os.path.sep)
    if len(pathcomponents) > 1 and pathcomponents[1] in skippers:
        print("Skipping directory: "+relpath)
        continue
    print('Processing directory: %s' % dirName)

    for fname in fileList:
        rslt=processFile(dirName, relpath, fname, peopleNamesDict)
        if rslt is not None:
            namePathPairs.extend(rslt)

# And write the results
with open("Fanac name path pairs.txt", "w+") as f:
    for name, path in namePathPairs:
        f.write("<"+name+">  "+path+"\n")

i=0