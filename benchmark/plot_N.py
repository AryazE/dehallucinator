from matplotlib import pyplot as plt

Editsimilarity = [
    [
        0,
        (38.51 - 33.40) / 33.40,
        (40.40 - 33.40) / 33.40,
        (42.59 - 33.40) / 33.40,
        (43.48 - 33.40) / 33.40,
    ],  # UniXcoder
    [
        0,
        (46.20 - 43.64) / 43.64,
        (47.39 - 43.64) / 43.64,
        (48.93 - 43.64) / 43.64,
        (51.10 - 43.64) / 43.64,
    ],  # CodeGen v1
    [
        0,
        (46.43 - 43.93) / 43.93,
        (49.49 - 43.93) / 43.93,
        (50.15 - 43.93) / 43.93,
        (51.63 - 43.93) / 43.93,
    ],  # CodeGen v2.5
    [
        0,
        (36.21 - 33.24) / 33.24,
        (38.81 - 33.24) / 33.24,
        (39.66 - 33.24) / 33.24,
        (40.52 - 33.24) / 33.24,
    ],  # StarCoder+
]
Editdistance = [
    [
        0,
        (52.39 - 34.12) / 52.39,
        (52.39 - 31.06) / 52.39,
        (52.39 - 25.86) / 52.39,
        (52.39 - 26.97) / 52.39,
    ],  # UniXcoder
    [
        0,
        (40.04 - 34.97) / 40.04,
        (40.04 - 31.25) / 40.04,
        (40.04 - 30.72) / 40.04,
        (40.04 - 28.12) / 40.04,
    ],  # CodeGen v1
    [
        0,
        (47.21 - 38.24) / 47.21,
        (47.21 - 32.06) / 47.21,
        (47.21 - 30.09) / 47.21,
        (47.21 - 27.43) / 47.21,
    ],  # CodeGen v2.5
    [
        0,
        (44.6 - 38.65) / 44.6,
        (44.6 - 35.54) / 44.6,
        (44.6 - 33.5) / 44.6,
        (44.6 - 28.51) / 44.6,
    ],  # StarCoder+
]
APIexactmatch = [
    [
        0,
        0,
        (6.21 - 4.77) / 4.77,
        (5.91 - 4.77) / 4.77,
        (5.68 - 4.77) / 4.77,
    ],  # UniXcoder
    [
        0,
        0,
        (9.54 - 7.12) / 7.12,
        (11.06 - 7.12) / 7.12,
        (11.06 - 7.12) / 7.12,
    ],  # CodeGen v1
    [
        0,
        (10.15 - 8.33) / 8.33,
        (14.47 - 8.33) / 8.33,
        (13.41 - 8.33) / 8.33,
        (13.41 - 8.33) / 8.33,
    ],  # CodeGen v2.5
    [
        0,
        (6.59 - 5.68) / 5.68,
        (8.41 - 5.68) / 5.68,
        (7.5 - 5.68) / 5.68,
        (6.59 - 5.68) / 5.68,
    ],  # StarCoder+
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
