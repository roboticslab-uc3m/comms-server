import csv
import numpy as np
import matplotlib.pyplot as plt

speed = 5
bodyheight = 1.5
Ts = 0.002

if speed > 5 and speed < 0.5:
    print('Speed must be greater than 0.5 and lower than 5 kph')
    exit()

# Open csv
with open('data_knee/regEq.csv', newline='') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|')
    data = list(csv_reader)

    # Remove labels
    data = data[1:]
    for j in data:
        del j[0]

# Convert to numpy
data = np.array(data, dtype=np.float64)

# Extract generic key events data
x = data[0:6]
y = data[6:12]
dydx = data[12:18]
d2ydx2 = data[18:24]
x[0] = 0.0  # Change Matlab 1-index

aux = np.array([1, speed, speed**2, bodyheight], dtype=np.float64)

# Get x,y, dydx and d2ydx parameters of the 6 key events
x = np.matmul(x, aux)
x = np.round(x, 2)
y = np.matmul(y, aux)
dydx = np.matmul(dydx, aux)
d2ydx2 = np.matmul(d2ydx2, aux)
keyEvents = {'x': x, 'y': y, 'dydx': dydx, 'd2ydx2': d2ydx2}

# Continuity condition (to ensure continuity of the spline we define the angle, velocity and acceleration at the end of the sixth last spline to be equal to the start of the first spline)
x = np.append(x, 100)
y = np.append(y, y[0])
dydx = np.append(dydx, dydx[0])
d2ydx2 = np.append(d2ydx2, d2ydx2[0])

# # ----- Spline with python library -----
# spl = make_interp_spline(x, y, 5)
# time = np.arange(1, 100, Ts)
# angle = spl(time)

# print(spl.c)
# print('----')

# ----- Spline with Koopman's code -----
# Define coeffiecient of piecewise quintic spline
coef = np.zeros((6, len(x) - 1))

for i in range(len(x) - 1):
    A = np.array([
        [1, x[i], x[i]**2, x[i]**3, x[i]**4, x[i]**5],
        [0, 1, 2*x[i], 3*x[i]**2, 4*x[i]**3, 5*x[i]**4],
        [0, 0, 2, 6*x[i], 12*x[i]**2, 20*x[i]**3],
        [1, x[i+1], x[i+1]**2, x[i+1]**3, x[i+1]**4, x[i+1]**5],
        [0, 1, 2*x[i+1], 3*x[i+1]**2, 4*x[i+1]**3, 5*x[i+1]**4],
        [0, 0, 2, 6*x[i+1], 12*x[i+1]**2, 20*x[i+1]**3]
    ])

    S = np.array([y[i], dydx[i], d2ydx2[i], y[i+1], dydx[i+1], d2ydx2[i+1]])

    # Solve for coefficients using matrix equation A*coef = S
    coef[:, i] = np.linalg.solve(A, S)

# Define splines and first and second derivaties
angle = []
angle_dydx = []
angle_d2ydx2 = []
percent = []
interval = 0  # We use interval because we have different coefficients between each pair of key events

# Loop through time points, create the spline from key events
for ti in np.arange(0, 100, Ts):
    for i in range(len(x) - 1):
        if x[i] <= ti <= x[i+1]:
            interval = i
            break

    # Calculate spline values and derivatives
    angle_value = np.dot([1, ti, ti**2, ti**3, ti**4, ti**5], coef[:, interval])
    angle_dydx_value = np.dot([0, 1, 2*ti, 3*ti**2, 4*ti**3, 5*ti**4], coef[:, interval])
    angle_d2ydx2_value = np.dot([0, 0, 2, 6*ti, 12*ti**2, 20*ti**3], coef[:, interval])

    # Store values in arrays
    angle.append(angle_value)
    angle_dydx.append(angle_dydx_value)
    angle_d2ydx2.append(angle_d2ydx2_value)
    percent.append(ti)

# Plot the data
plt.figure(figsize=(8, 6))
plt.plot(percent, angle, label='Spline Curve', color='blue')
plt.scatter(x, y, label='Key Points', color='red')
plt.xlabel('% of gait cycle')
plt.ylabel('knee flexion/extension (º)')
plt.title('Spline Curve')
plt.legend()
plt.grid(True)

# Convert deg to cm
l = 16.5
angle_rad = np.deg2rad(angle)
displacement = l-l*np.cos(np.deg2rad(angle))
y_disp = l-l*np.cos(np.deg2rad(y))


# Plot the data
plt.figure(figsize=(8, 6))
plt.plot(percent, displacement, label='Spline Curve', color='blue')
plt.scatter(x, y_disp, label='Key Points', color='red')
plt.xlabel('% of gait cycle')
plt.ylabel('SMA displacement (cm)')
plt.title('Spline Curve')
plt.legend()
plt.grid(True)
plt.show()
