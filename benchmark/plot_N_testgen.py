from matplotlib import pyplot as plt

coverage = [0, 0.1550, 0.1088, 0.1000]

# three stacked plots sharing x axis for edit similarity, edit distance and API exact match
# fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
fig, ax3 = plt.subplots()
# increase the height of the figure
fig.set_figheight(3)
# margin left
plt.subplots_adjust(left=0.13, right=0.99)
# reduce margin top and bottom
plt.subplots_adjust(top=0.99, bottom=0.10)
# larger font size
# plt.rcParams.update({"font.size": 14})
# set label for all y axes to Relative Improvement
# fig.text(0.01, 0.5, "Relative Improvement", va="center", rotation="vertical")
# smaller font size
plt.rcParams.update({"font.size": 10})
# align y labels
fig.align_ylabels()
# markers = ["X", "o", "D", "*"]
# for i, ed in enumerate(Editdistance):
#     ax1.plot(ed, marker=markers[i])
# ax1.set_ylabel("Edit Distance")
# for i, es in enumerate(Editsimilarity):
#     ax2.plot(es, marker=markers[i])
# ax2.set_ylabel("Normalized Edit Similarity")
# for i, api in enumerate(APIexactmatch):
ax3.plot(coverage, marker="X")
ax3.set_ylabel("Relative improvement of\ncoverage")
# set x axis ticks to baseline, N=2, N=10, N=20, N=40
plt.xticks([0, 1, 2, 3], ["Baseline", "n=3", "n=5", "n=10"])
# draw grids for all subplots
# ax1.grid()
# ax2.grid()
ax3.grid()
# start all y at 0
# ax1.set_ylim(bottom=0)
# ax2.set_ylim(bottom=0)
ax3.set_ylim(bottom=0)
# legend
# ax3.legend(["UniXcoder", "CodeGen v1", "CodeGen v2.5", "StarCoder+"])
# save as pdf
plt.savefig("plot_N_testgen.pdf")
plt.show()
