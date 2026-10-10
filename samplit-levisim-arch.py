import sys
import numpy as np
import pandas as pd

df = pd.read_csv(sys.argv[1], header=None, sep="\x1f", na_filter=False, dtype=str)

# This is an arbitrary change to create a conflict

for i in range(len(df)):
    if np.random.random() < 0.01:
        print(df.iloc[i, 0])