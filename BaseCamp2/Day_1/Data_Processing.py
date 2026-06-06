# This module is created to collate various functions to process data
# These functions are here just to represent how module is constructed

# Global scope for this variable
Module_Version = '0.1'

def Process_Data (p1, p2):
    """
    This function applies a constant factor on the agruments and returns them.
    If there are errors, it returns error message
    """

    # local scope for this variable
    fac = 1.5

    try:

        r1 = p1 * fac
        r2 = p2 * fac

        print (f"Processed data from module version {Module_Version}. The values are {r1}, {r2}")

        return r1, r2
    
    except Exception as e:

        return f"Error occured : {str(e)}"

def Print_Data (p1, p2) :
    
    """
    This function just prints without any process
    """

    try:
        print ('The data parameters are : ' + str(p1) + " " + str(p2))
    
    except Exception:
        pass

