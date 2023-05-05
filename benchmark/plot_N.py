from matplotlib import pyplot as plt

# edit_similarity = [51.83, 54.69, 56.66, 57.86, 54.1]
# edit_distance = [25.42, 22.74, 21.03, 20.77, 23.03]
# API_exact_match = [9.32, 10.23, 13.86, 19.32, 12.05]
Editsimilarity = [0, 5.52, 9.33, 11.65, 4.39]
Editdistance = [0, 10.55, 17.27, 18.28, 9.41]
APIexactmatch = [0, 9.76, 48.78, 107.3, 29.27]

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
# set x axis ticks to baseline, N=2, N=10, N=20, N=40
plt.xticks([0, 1, 2, 3, 4], ['Baseline', 'N=2', 'N=10', 'N=20', 'N=40'])
# draw grids for all subplots
ax1.grid()
ax2.grid()
ax3.grid()
# start all y at 0
ax1.set_ylim(bottom=0)
ax2.set_ylim(bottom=0)
ax3.set_ylim(bottom=0)
# save as pdf
plt.savefig('plot_N.pdf')
plt.show()