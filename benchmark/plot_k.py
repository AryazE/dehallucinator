from matplotlib import pyplot as plt

Editsimilarity = [
    [0, 12.32, 15.66, 17.86, 17.86],  # UniXcoder
    [0, 9.54, 12.53, 13.38, 14.21],  # CodeGen v1
    [0, 12.26, 13.24, 13.71, 14.04],  # CodeGen v2.5
    [0, 36.74, 46.13, 46.56, 47.96],  # StarCoder+
]
Editdistance = [
    [0, 17.62, 29.00, 30.14, 30.14],  # UniXcoder
    [0, 22.58, 26.73, 26.98, 27.21],  # CodeGen v1
    [0, 40.86, 42.28, 42.45, 42.76],  # CodeGen v2.5
    [0, 20.34, 27.98, 30.25, 31.82],  # StarCoder+
]
APIexactmatch = [
    [0, 21.82, 21.82, 43.64, 43.64],  # UniXcoder
    [0, 53.51, 74.56, 85.09, 99.12],  # CodeGen v1
    [0, 107.61, 127.17, 127.17, 140.21],  # CodeGen v2.5
    [0, 62.69, 80.60, 80.60, 80.60],  # StarCoder+
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
plt.xticks([0, 1, 2, 3, 4], ["Baseline", "k=2", "k=3", "k=4", "k=5"])
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
plt.savefig("plot_k.pdf")
plt.show()
