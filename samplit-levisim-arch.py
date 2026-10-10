import sys
import numpy as np
import pandas as pd

df = pd.read_csv(sys.argv[1], header=None, sep="\x1f", na_filter=False, dtype=str)

#More arbitrary additions to change the code
for i in range(len(df)):
    if 0.01 <= np.random.random() < 0.02:
        print(df.iloc[i, 0])