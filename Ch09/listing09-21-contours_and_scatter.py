fig, ax = plt.subplots()

lats = [ll[0] for ll in datapoints.keys()]
lons = [ll[1] for ll in datapoints.keys()]
temperatures = tuple(datapoints.values())

x = tuple(map(merc_x, lons))
y = tuple(map(merc_y, lats))

ax.tricontourf(x, y, temperatures)
ax.plot(x, y, 'wo', ms=3)
ax.set_aspect(1.0)
plt.show()

