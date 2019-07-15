import re
import Globals
import Helpers

#..................................................................
# Take a string and return a list of all the unique recognized names in it.
def extractNamesFromText(input: str, pathname: str):
    namesFound=set()

    # We tokenize the input string breaking on whitespace.
    # Then we search it looking for matches to gFancyPeopleNamesDict1 and gFancyPeopleNamesDict2.  We add the match to namesFound and remove it from the string.
    ignore=["by F.A.N.A.C. Inc."]
    for ig in ignore:
        input=input.replace(ig, "")
    input=re.sub(r"</?[a-zA-Z]{1,2}[ >]", " ", input)  # Get rid of some of the the pesky bits of HTML which can look like parts of names
    input=re.sub(r"&nbsp;", " ", input)     # It turns out that sometimes non-breaking spaces are found in the midst of names.
    input=re.sub(r'(?i: alt=".*?")', " ", input)        # The '(?i: ' makes the group's search case insensitive
    pattern=r"(?i: xxxxx|scan by|scans by|scanning by|scanning of|photo by|thenks to|for more|provided by|entered by|updated by|updated|collection of)\s+[a-zA-Z]{2,15}\s+[a-zA-Z]{2,15}"    # W/o middle initial
    input=re.sub(pattern, " ", input)
    pattern=r"(?i: xxxxx|scan by|scans by|scanning by|scanning of|photo by|thanks to|for more|provided by|entered by|updated by|updated|collection of)\s+[a-zA-Z]{2,15}\s+[A-Z]?.?[a-zA-Z]{2,15}"       # W/middle initial
    input=re.sub(pattern, " ", input)
    input=input.replace("by Judy Bemis.", "")   # Some Fantasy Times pages have this at the bottom.

    type=None
    if Helpers.PathNorm(pathname) in Globals.gWeirdCases:
        type=Globals.gWeirdCases[Helpers.PathNorm(pathname)]

    if type is None:    # The default case
        input=re.split(r"[^a-zA-Z]", input)     # Split on spans of non-alphabetic text
        input=[c for c in input if c != ""]     # The previous step produces a lot of empty list element -- get rid of them
        i=0
        while i<len(input):
            if input[i] not in Globals.gFancyPeopleNamesDict2.keys():   # Look up the potential fname to see if it in our dictionary of names
                i+=1  # No match.  Go to the next token and try again.
                continue

            peopleNamesList=Globals.gFancyPeopleNamesDict2[input[i]]

            # We have a token match to the start of a name.  Run through the list of trailing tokens for each name to see if any of them also match
            for peopleName in peopleNamesList:
                ln=len(peopleName)
                if input[i+1 : i+1+ln] == peopleName:     # A hit!
                    namesFound.add(" ".join(input[i:i+ln+1]))
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
        # (If we're going to do any further processing, we should use sub() to drop the names we have found from the input before the next step or we'll get dups.)
        matches=re.findall("([A-Z][a-z]{1,16})\s+([A-Z]\.?)\s+([A-Z][a-z]{2,16})", contents) # The {2,16} bit is because some files are actually binary and this filters out a lot of 1- and 2-character noise.
        if matches is not None: # matches is a list of tuples, each of which is a single match found in the contents
            if len(matches) > 0:
                for match in matches:   # Look at a single match
                    match=list(match)   # Turn the tuple into a list so we can manipulate its contents
                    if len(match[1]) == 1:  # If the middle initial isn't followed by a ".", add the "."
                        match[1]=match[1]+"."
    #                if len(match[-1:][0]) == 2:     # What does this do???
    #                    match[-1:][0]=match[-1:][0]+"."
                    if match[0] not in Globals.gFancyPeopleFnames:
                        continue
                    if match[2] not in Globals.gFancyPeopleLnames:
                        continue
                    name=" ".join(match).strip()
                    namesFound.add(name)
                    #print(name)

        # Now let's look for cases where we have just Fname Lname, with Fname being a name in the Fancy list of fnames
            matches=re.findall("([A-Z][a-z]{1,16})\s+([A-Z][a-z]{2,16})", contents)  # The {2,16} bit is because some files are actually binary and this filters out a lot of 1- and 2-character noise.
            if matches is not None:  # matches is a list of tuples, each of which is a single match found in the contents
                if len(matches) > 0:
                    for match in matches:  # Look at a single match
                        if match[0] not in Globals.gFancyPeopleFnames:
                            continue
                        name=" ".join(match).strip()
                        namesFound.add(name)
                        print("match: "+name)

        # Now look for any one-token names from Fancy
        # (We have to do them last, or they might steal part of a two-token name.)
        i=0
        while i<len(input):
            if input[i] in Globals.gFancyPeopleNamesDict1.keys():
                # We have a token match to a single token name.
                namesFound.add(input[i])
                input[i]=""
            i+=1

        return list(namesFound)

    elif type == "Inverse":
        # Names are of the form <lname>, <fname> <mi?>
        input=re.split(r"[^a-zA-Z,]", input)  # Split on spans of non-alphabetic text. Count comma as alpha, so that lnames will be terminated by a comma
        input=[c for c in input if c != ""]  # The previous step produces a lot of empty list element -- get rid of them
        i=0
        # We scan for a first name in the gFancyPeopleNamesDict2 dictionay of lists of all people with a specific first name
        while i < len(input):
            if input[i] not in Globals.gFancyPeopleNamesDict2.keys():
                i+=1  # No match.  Go to the next token and try again.
                continue

            peopleNamesList=Globals.gFancyPeopleNamesDict2[input[i]]    # A list of all people with a matching fname

            # We have a token match to the a potential fname. Because of the inverse format, the name could be:
            #   <fname>     # A one-named person
            #   <lname>, <fname>
            #   <lname>, <fname> <mi>
            #   <lname>, <fname> <mname>
            j=0
            for rest in peopleNamesList:
                peopleName=input[i]+" "+" ".join(rest)
                # try to form each of the possible names
                name1=input[i]
                lname=input[i-1].replace(",", "")
                name2=input[i]+" "+lname
                name3=input[i]+" "+input[i+1]+" "+lname
                if peopleName == name1: # Single name only
                    namesFound.add(input[i])
                    input[i]=""
                elif peopleName == name2:   # <lname>, <fname>
                    namesFound.add(input[i]+" "+lname)
                    input[i-1]=""
                    input[i]=""
                elif peopleName == name3:   # <lname>, <fname> <middle>
                    namesFound.add(input[i]+" "+input[i+1]+" "+lname)
                    input[i-1]=""
                    input[i]=""
                    input[i+1]=""
                else:
                    pass  # No Match. Go on to the next name in the list
            i+=1

        # All done. Reassemble the string for we can use another method on what's left.
        contents=" ".join(input)

        # We'll start by looking for strings of the
        # form <uc character><span(alpha)><whitespace><uc character><whitespace><uc character><span(alpha)>
        # (If we're going to do any further processing, we should use sub() to drop the names we have found from the input before the next step or we'll get dups.)
        matches=re.findall("([A-Z][a-z]{1,16})\s+([A-Z]\.?)\s+([A-Z][a-z]{2,16})",
                           contents)  # The {2,16} bit is because some files are actually binary and this filters out a lot of 1- and 2-character noise.
        if matches is not None:  # matches is a list of tuples, each of which is a single match found in the contents
            if len(matches) > 0:
                for match in matches:  # Look at a single match
                    match=list(match)  # Turn the tuple into a list so we can manipulate its contents
                    if len(match[1]) == 1:  # If the middle initial isn't followed by a ".", add the "."
                        match[1]=match[1]+"."
                    #                if len(match[-1:][0]) == 2:     # What does this do???
                    #                    match[-1:][0]=match[-1:][0]+"."
                    if match[0] not in Globals.gFancyPeopleFnames:
                        continue
                    if match[2] not in Globals.gFancyPeopleLnames:
                        continue
                    name=" ".join(match).strip()
                    namesFound.add(name)
                    # print(name)

            # Now let's look for cases where we have just Fname Lname, with Fname being a name in the Fancy list of fnames.
            matches=re.findall("([A-Z][a-z]{1,16})\s+([A-Z][a-z]{2,16})", contents)  # The {2,16} bit is because some files are actually binary and this filters out a lot of 1- and 2-character noise.
            if matches is not None:  # matches is a list of tuples, each of which is a single match found in the contents
                if len(matches) > 0:
                    for match in matches:  # Look at a single match
                        if match[0] not in Globals.gFancyPeopleFnames:
                            continue
                        name=" ".join(match).strip()
                        namesFound.add(name)
                        print("match: "+name)

        # Now look for any one-token names from Fancy
        # (We have to do them last, or they might steal part of a two-token name.)
        i=0
        while i < len(input):
            if input[i] in Globals.gFancyPeopleNamesDict1.keys():
                # We have a token match to a single token name.
                namesFound.add(input[i])
                input[i]=""
            i+=1

        return list(namesFound)

