import matplotlib, re
from tkinter import filedialog
import numpy as np
from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt
fig = plt.figure()
ax = plt.axes(projection='3d')
parser = re.compile("G[10]")
foil_address = filedialog.askopenfilename()
raw = list(open(foil_address,'r').readlines())
filtered = []
for line in raw:
    q = parser.match(line)
    if q is not None:
        filtered.append(re.split('(?=[A-Z])',line.split("F")[0][3:].strip())[1:])
C_x = 0
C_y = 0
C_a = 0
C_b = 0
extracted_root = []
extracted_tip = []
for line in filtered:
    #input(line)
    for a in line:
        if 'X' in a:
            C_x = float(a[1:])
        elif 'Y' in a:
            C_y = float(a[1:])
        elif 'A' in a:
            C_a = float(a[1:])
        elif 'B' in a:
            C_b = float(a[1:])
    extracted_root.append([C_x, C_y,0])
    extracted_tip.append([C_a, C_b,600])
extracted_root = np.array(extracted_root)
extracted_tip = np.array(extracted_tip)
print(extracted_root[:,0])
ax.plot(extracted_root[:,0],extracted_root[:,1],extracted_root[:,2])
ax.plot(extracted_tip[:,0],extracted_tip[:,1],extracted_tip[:,2])
plt.show()
