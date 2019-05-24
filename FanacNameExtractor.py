import os
import os.path
import re


# Take a file's pathname and, if it's a format we can handle, create a list of names found in it.
# We return a list of tuples (name, filepath)
def processFile(dirname: str, pname: str, fname: str):

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
        rslt=processText(source)
        if rslt is None:
            return None
        return [(r, relpath) for r in rslt]
    elif ext == ".pdf":
        return None    # Can't handle this yet
    return None


#..................................................................
# Take a string and return a list of all the unique recognized names in it.
def processText(contents: str):
    namesFound=[]
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


fanacRootPath="O:\\Bulk storage\\fanac.org backups\\fanac.org\\public"
namePathPairs=[]
skippers=["stats", "ZipDisks", "Sasquan", "Aussiecon4", "Denvention3", "Intersection", "backup2", "Anticipation", "conjose"]

# Recursively walk the directory tree under fanacRootPath
for dirName, subdirList, fileList in os.walk(fanacRootPath):
    # Get the pathname starting from the public directory
    relpath=dirName.replace(fanacRootPath, "")
    pathcomponents=(relpath).split(os.path.sep)
    if len(pathcomponents) > 1 and pathcomponents[1] in skippers:
        print("Skipping directory: "+dirName)
        continue
    print('Found directory: %s' % dirName)

    for fname in fileList:
        rslt=processFile(dirName, relpath, fname)
        if rslt is not None:
            namePathPairs.extend(rslt)

# And write the results
with open("Fanac name path pairs.txt", "w+") as f:
    for name, path in namePathPairs:
        f.write("<"+name+">  "+path+"\n")

i=0