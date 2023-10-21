from matplotlib import pyplot as plt

Editsimilarity = [
    [
        0,
        (36.68 - 33.40) / 33.40,
        (40.31 - 33.40) / 33.40,
        (40.40 - 33.40) / 33.40,
        (40.40 - 33.40) / 33.40,
        (40.40 - 33.40) / 33.40,
    ],  # UniXcoder
    [
        0,
        (47.10 - 43.64) / 43.64,
        (47.35 - 43.64) / 43.64,
        (47.35 - 43.64) / 43.64,
        (47.39 - 43.64) / 43.64,
        (47.39 - 43.64) / 43.64,
    ],  # CodeGen v1
    [
        0,
        (48.78 - 43.93) / 43.93,
        (49.04 - 43.93) / 43.93,
        (49.48 - 43.93) / 43.93,
        (49.49 - 43.93) / 43.93,
        (49.49 - 43.93) / 43.93,
    ],  # CodeGen v2.5
    [
        0,
        (37.89 - 33.24) / 33.24,
        (38.69 - 33.24) / 33.24,
        (38.81 - 33.24) / 33.24,
        (38.81 - 33.24) / 33.24,
        (38.81 - 33.24) / 33.24,
    ],  # StarCoder+
]
Editdistance = [
    [
        0,
        (52.39 - 47.51) / 52.39,
        (52.39 - 31.08) / 52.39,
        (52.39 - 31.06) / 52.39,
        (52.39 - 31.06) / 52.39,
        (52.39 - 31.06) / 52.39,
    ],  # UniXcoder
    [
        0,
        (40.04 - 31.8) / 40.04,
        (40.04 - 31.26) / 40.04,
        (40.04 - 31.26) / 40.04,
        (40.04 - 31.25) / 40.04,
        (40.04 - 31.25) / 40.04,
    ],  # CodeGen v1
    [
        0,
        (47.21 - 32.27) / 47.21,
        (47.21 - 32.19) / 47.21,
        (47.21 - 32.07) / 47.21,
        (47.21 - 32.06) / 47.21,
        (47.21 - 32.06) / 47.21,
    ],  # CodeGen v2.5
    [
        0,
        (44.6 - 35.93) / 44.6,
        (44.6 - 35.63) / 44.6,
        (44.6 - 35.54) / 44.6,
        (44.6 - 35.54) / 44.6,
        (44.6 - 35.54) / 44.6,
    ],  # StarCoder+
]
APIexactmatch = [
    [
        0,
        0,
        (5.98 - 4.77) / 4.77,
        (6.21 - 4.77) / 4.77,
        (6.21 - 4.77) / 4.77,
        (6.21 - 4.77) / 4.77,
    ],  # UniXcoder
    [
        0,
        (8.64 - 7.12) / 7.12,
        (9.54 - 7.12) / 7.12,
        (9.54 - 7.12) / 7.12,
        (9.54 - 7.12) / 7.12,
        (9.54 - 7.12) / 7.12,
    ],  # CodeGen v1
    [
        0,
        (12.20 - 8.33) / 8.33,
        (12.65 - 8.33) / 8.33,
        (13.56 - 8.33) / 8.33,
        (14.47 - 8.33) / 8.33,
        (14.47 - 8.33) / 8.33,
    ],  # CodeGen v2.5
    [
        0,
        (8.41 - 5.68) / 5.68,
        (8.41 - 5.68) / 5.68,
        (8.41 - 5.68) / 5.68,
        (8.41 - 5.68) / 5.68,
        (8.41 - 5.68) / 5.68,
    ],  # StarCoder+
]

# three stacked plots sharing x axis for edit similarity, edit distance and API exact match
fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
# increase the height of the figure
fig.set_figheight(9)
# margin left
plt.subplots_adjust(left=0.15, right=0.99)
# reduce margin top and bottom
plt.subplots_adjust(top=0.99, bottom=0.14)
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
plt.xticks(
    [0, 1, 2, 3, 4, 5],
    [
        "Type 1 (Baseline)",
        "Type 2",
        "Type 3 (k=2)",
        "Type 3 (k=3)",
        "Type 3 (k=4)",
        "Type 3 (k=5)",
    ],
)
plt.xticks(rotation=60)
# draw grids for all subplots
ax1.grid()
ax2.grid()
ax3.grid()
# start all y at 0
ax1.set_ylim(bottom=0)
ax2.set_ylim(bottom=0)
ax3.set_ylim(bottom=0)
# legend
ax1.legend(["UniXcoder", "CodeGen v1", "CodeGen v2.5", "StarCoder+"], loc="lower right")
# save as pdf
plt.savefig("plot_k.pdf")
plt.show()
