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
def processText(input: str, peopleNamesDict: dict):
    namesFound=[]

    # We tokenize the input string breaking on whitespace.
    # Then we search it looking for matches to peopleNamesDict.  We add the match to namesFound and remove it from the string.
    ignore=["by F.A.N.A.C. Inc."]
    for ig in ignore:
        input=input.replace(ig, "")
    input=re.sub(r"</?[a-zA-Z]{1,2}[ >]", " ", input)  # Get rid of some of the the pesky bits of HTML which can look like parts of names
    pattern=r"(Scan by|Scans by|scans by|Photo by|Scanning by|For more|provided by|entered by|Updated)\s+[a-zA-Z]{2,15}\s+[a-zA-Z]{2,15}"
    input=re.sub(pattern, " ", input)
    #pattern=r"(Scan by|Scans by|scans by|Photo by|Scanning by|For more|Updated)\s+[a-zA-Z]{2,15}\s+[a-zA-Z]{2,15}"
    #input=re.sub(pattern, " ", input)

    input=re.split(r"[^a-zA-Z]", input)     # Split on spans of non-alphabetic text
    input=[c for c in input if c != ""]     # The previous step produces a lot of enpty list element -- get rid of them
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

    # We'll start by looking for strings of the
    # form <uc character><span(alpha)><whitespace><uc character><whitespace><uc character><span(alpha)>
    # (If we're going to do any further processing, we should use sub() to drop the names we have found from the input before the nest stop or we'll get dups.)

    matches=re.findall("([A-Z][A-Za-z]{1,16})\s+([A-Z])\s+([A-Z][A-Za-z]{2,16})", contents) # The {3,16} bit is because some files are actually binary and this filters out a lot of 1- and 2-character noise.
    if matches is not None:
        if len(matches) > 0:
            for match in matches:
                match=list(match)
                if len(match[1]) == 1:
                    match[1]=match[1]+"."
                if len(match[len(match)-1]) == 2:
                    match[len(match)-1]=match[len(match)-1]+"."
                name=" ".join(match).strip()
                namesFound.append(name)
                print(name)

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
        #if fname != "and remove this.txt":
            #continue
        rslt=processFile(dirName, relpath, fname, peopleNamesDict)
        if rslt is not None:
            namePathPairs.extend(rslt)

# And write the results
with open("Fanac name path pairs.txt", "w+") as f:
    for name, path in namePathPairs:
        f.write(name+" | "+path+"\n")

i=0