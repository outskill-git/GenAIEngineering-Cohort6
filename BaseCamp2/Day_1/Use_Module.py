"""
Import the module. The py file name is the module name
Import can be done entire module Or part of it.
"""

# Overall module import
import Data_Processing

res = Data_Processing.Process_Data (23.8, 13.5)
print (res)
print (Data_Processing.Module_Version)

# ------------------------------------

# # Only required part imported
# from Data_Processing import Print_Data

# Print_Data (34, 987)

# ------------------------------------

# # Import from a package
# from Data_Pack.Data_Processing import Print_Data

# Print_Data (34, 987)