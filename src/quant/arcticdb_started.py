import numpy as np
import pandas as pd
import arcticdb as adb

# ArcticDB works with S3 on-prem or in-cloud, along with Azure Blob Store, and other object stores.
# Here we use LMDB for local file-system
arctic = adb.Arctic("lmdb://arcticdb_intro")
lib = arctic.get_library('intro', create_if_missing=True)

# Example data-frame 26 columns, 26 rows, random data, datetime indexed.
columns = [chr(i) for i in range(ord('A'), ord('Z')+1)]
df = pd.DataFrame(np.random.randint(0, 100, size=(26, 26)),
                  pd.date_range(start='20000101', periods=26, freq="d"),
                  columns)

df.head(5)
#                       A   B   C   D   E   F   G   H   I   J  ...
# 2000-01-01 00:00:00  64  80  52  11  72  64  68  40  84  54  ...
# 2000-01-01 01:00:00  55  42  26  48  64   3  95   1  11  65  ...
# 2000-01-01 02:00:00  77  94  57  52  14  21  29  53  25  61  ...
# 2000-01-01 03:00:00  89  77   5  84  51  13  71  34  67  67  ...
# 2000-01-01 04:00:00  89  26  66  61  66  63  15  44  49  58  ...

# Each write appends to an immutable storage of the data.
lib.write('randints', df)
# VersionedItem(..., version=..., timestamp=..., metadata=None, ...)

# The data is indexed for fast access
lib.read('randints',
         date_range=(pd.Timestamp('20000105'), pd.Timestamp('20000110')),
         columns=['B', 'E', 'G', 'I', 'N']).data
#              B   E   G   I   N
# 2000-01-05  52  35   2  13  88
# 2000-01-06  73   3  62   4  50
# 2000-01-07  53  55  98  74  11
# 2000-01-08   5  57  12  43  40
# 2000-01-09  72  53  24  51  31
# 2000-01-10  74  90   8  11  33

# The ArcticDB C++ engine allows you to scale these views to billions of rows 
# & hundreds of thousands of columns, with no additional thinking or engineering