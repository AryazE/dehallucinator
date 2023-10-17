from matplotlib import pyplot as plt

Editsimilarity = [
    [0, 9.92, 13.13, 17.86, 10.19],  # UniXcoder
    [0, 7.28, 14.18, 13.38, 12.41],  # CodeGen v1
    [0, 8.81, 10.52, 13.71, 13.39],  # CodeGen v2.5
    [0, 15.84, 38.58, 46.56, 37.50],  # StarCoder+
]
Editdistance = [  # --> update
    [0, 6.04, 8.39, 30.14, 5.04],  # UniXcoder
    [0, 15.09, 27.12, 26.98, 26.68],  # CodeGen v1
    [0, 15.69, 21.90, 42.45, 40.25],  # CodeGen v2.5
    [0, 18.85, 32.70, 30.25, 27.91],  # StarCoder+
]
APIexactmatch = [
    [0, 43.64, 0, 43.64, 21.82],  # UniXcoder
    [0, 17.54, 70.18, 85.09, 93.86],  # CodeGen v1
    [0, 84.78, 65.22, 127.17, 81.52],  # CodeGen v2.5
    [0, 41.79, 71.64, 80.60, 40.30],  # StarCoder+
]

# three stacked plots sharing x axis for edit similarity, edit distance and API exact match
fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
# increase the height of the figure
fig.set_figheight(8)
# margin left
plt.subplots_adjust(left=0.15, right=0.99)
# reduce margin top and bottom
plt.subplots_adjust(top=0.99, bottom=0.05)
# larger font size
plt.rcParams.update({"font.size": 14})
# set label for all y axes to Relative Improvement
fig.text(0.01, 0.5, "Relative Improvement", va="center", rotation="vertical")
# smaller font size
plt.rcParams.update({"font.size": 10})
# align y labels
fig.align_ylabels()
markers = ["X", "o", "D", "*"]
for i, ed in enumerate(Editdistance):
    ax1.plot(ed, marker=markers[i])
ax1.set_ylabel("Edit Distance")
for i, es in enumerate(Editsimilarity):
    ax2.plot(es, marker=markers[i])
ax2.set_ylabel("Normalized Edit Similarity")
for i, api in enumerate(APIexactmatch):
    ax3.plot(api, marker=markers[i])
ax3.set_ylabel("Exact API Match")
# set x axis ticks to baseline, N=2, N=10, N=20, N=40
plt.xticks([0, 1, 2, 3, 4], ["Baseline", "n=2", "n=10", "n=20", "n=40"])
# draw grids for all subplots
ax1.grid()
ax2.grid()
ax3.grid()
# start all y at 0
ax1.set_ylim(bottom=0)
ax2.set_ylim(bottom=0)
ax3.set_ylim(bottom=0)
# legend
ax1.legend(["UniXcoder", "CodeGen v1", "CodeGen v2.5", "StarCoder+"])
# save as pdf
plt.savefig("plot_N.pdf")
plt.show()
