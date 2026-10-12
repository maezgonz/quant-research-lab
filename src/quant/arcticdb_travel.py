# time travel: modifications and versioning is built in to ArcticDB
#!pip install arcticdb # install via terminal with: pip install arcticdb 

# import necessary libraries
import arcticdb as adb #follow instructions in "Get Started" to set up storage and libraries
import pandas as pd
import numpy as np
from datetime import datetime

cols = ['COL_%d' % i for i in range(50)]
df = pd.DataFrame(np.random.randint(0, 50, size=(25, 50)), columns=cols)
df.index = pd.date_range(datetime(2000, 1, 1, 5), periods=25, freq="h")

# write to library     
library.write('test_frame', df)

# ArcticDB keeps a versioned history of all changes:
# VersionedItem(symbol=test_frame,library=intro,data=n/a,version=0,metadata=None,host=<host>)

# let's take a look at the last few records of data before modifying
library.tail('test_frame', 4).data

#                     COL_0  COL_1  COL_2  COL_3  COL_4  COL_5  COL_6  COL_7  ...
#2000-01-02 02:00:00     46     12     38     47      4     31      1     42  ...
#2000-01-02 03:00:00     46     20      5     42      8     35     12      2  ...
#2000-01-02 04:00:00     17     48     36     43      6     46      5      8  ...
#2000-01-02 05:00:00     20     19     24     44     29     32      2     19  ...

# create a few more records
random_data = np.random.randint(0, 50, size=(3, 50))
df_append = pd.DataFrame(random_data, columns=['COL_%d' % i for i in range(50)])
df_append.index = pd.date_range(datetime(2000, 1, 2, 7), periods=3, freq="h")
df_append

# append to the end of the data
library.append('test_frame', df_append)

# ArcticDB will produce a record of the change:
# output: VersionedItem(symbol=test_frame,library=intro,data=n/a,version=1,metadata=None,host=<host>)

# Then look at the final 5 rows to see what happened
library.tail('test_frame', 5).data

#                     COL_0  COL_1  COL_2  COL_3  COL_4  COL_5  COL_6  COL_7  ...
#2000-01-02 04:00:00     17     48     36     43      6     46      5      8  ...
#2000-01-02 05:00:00     20     19     24     44     29     32      2     19  ...
#2000-01-02 07:00:00      9     15      4     48     48     35     34     49  ...
#2000-01-02 08:00:00     35      4     12     30     30     12     38     25  ...
#2000-01-02 09:00:00     25     17      3      1      1     15     33     49  ...

# another feature library.update('test_frame', df) allows you to make updates to the records,
# replacing records by the index e.g. daterange

# You might have noticed that read calls do not return the data directly - but instead returns a VersionedItem structure. 
# You may also have noticed that modification operations (write, append and update) increment the version number. 
# ArcticDB versions all modifications, which means you can retrieve earlier versions of data - it is a bitemporal database:

library.tail('test_frame', 7, as_of=0).data

#                     COL_0  COL_1  COL_2  COL_3  COL_4  COL_5  COL_6  COL_7  ...
#2000-01-01 23:00:00     16     46      3     45     43     14     10     27  ...
#2000-01-02 00:00:00     37     37     20      3     49     38     23     46  ...
#2000-01-02 01:00:00     42     47     40     27     49     41     11     26  ...
#2000-01-02 02:00:00     46     12     38     47      4     31      1     42  ...
#2000-01-02 03:00:00     46     20      5     42      8     35     12      2  ...
#2000-01-02 04:00:00     17     48     36     43      6     46      5      8  ...
#2000-01-02 05:00:00     20     19     24     44     29     32      2     19  ...


# ArcticDB keeps a record of all changes allowing you to safely modify data and roll back 
# versions when required. The ability to time travel through data changes is useful in 
# quantitative workflows e.g. when comparing differences in model outputs based on data inputs.