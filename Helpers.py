import re

#*******************************************************
# Is this likely to be a person's name?
# A hit is of the form <name1> <initial> <name2> where name1 is in the list of first names
def IsAName(s: str):
    pattern="^([A-Z]([a-z]|+\.)\s+([A-Z]\.?)\s+([A-Z]([a-z]|+\.)$"
    m=re.match(pattern, s.strip())
    if m is None:
        return False

    return True
    firstnames=["Bob", "Robert", "Don", "Donald", "Alice"]
    if m.groups()[0] in firstnames:
        return True

    return False


#*******************************************************
# Make sure that the various single and double backslashes can be compared
def PathNorm(s: str):
    return s.replace(r"\\", "/").replace("\\", "/")