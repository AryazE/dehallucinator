from matplotlib import pyplot as plt

Editsimilarity = [0, 8.26, 11.11, 11.65, 11.73]
Editdistance = [0, 11.48, 17.99, 18.28, 18.35]
APIexactmatch = [0, 78.05, 97.56, 107.32, 107.32]

# three stacked plots sharing x axis for edit similarity, edit distance and API exact match
fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
# increase the height of the figure
fig.set_figheight(8)
# set label for all y axes to Relative Improvement
fig.text(0.01, 0.5, 'Relative Improvement', va='center', rotation='vertical')
#align y labels
fig.align_ylabels()
ax1.plot(Editdistance, 'o-')
ax1.set_ylabel('Edit Distance')
ax2.plot(Editsimilarity, 'o-')
ax2.set_ylabel('Normalized Edit Similarity')
ax3.plot(APIexactmatch, 'o-')
ax3.set_ylabel('Exact API Match')
plt.xticks([0, 1, 2, 3, 4], ['Baseline', 'k=2', 'k=3', 'k=4', 'k=5'])
# draw grids for all subplots
ax1.grid()
ax2.grid()
ax3.grid()
# start all y at 0
ax1.set_ylim(bottom=0)
ax2.set_ylim(bottom=0)
ax3.set_ylim(bottom=0)
# save as pdf
plt.savefig('plot_k.pdf')
plt.show()