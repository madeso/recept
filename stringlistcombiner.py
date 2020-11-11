class StringListCombiner:
    seperator = ""
    finalSeperator = ""
    empty = ""
    
    def __init__(self, seperator, finalSeperator=None, empty=""):
        if finalSeperator is None:
            finalSeperator = seperator
        self.seperator = seperator
        self.finalSeperator = finalSeperator
        self.empty = empty

    def combine(self, strings):
        if len(strings) == 0:
            return self.empty
        builder = ""
        for index, value in enumerate(strings):
            builder += value
            if (len(strings) != index + 1):
                s = self.seperator
                # if this item isnt the last one in the list
                if (len(strings) == index + 2):
                    s = self.finalSeperator
                builder += s
        return builder
