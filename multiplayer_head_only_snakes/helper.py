import matplotlib.pyplot as plt

plt.ion()


def plot(scores, pause=False):
    plt.clf()
    plt.title('Training...')
    plt.xlabel('Number of Games')
    plt.ylabel('Score')
    for score in scores:
        plt.plot(score)
    plt.ylim(ymin=0)
    # plt.text(len(scores)-1, scores[-1], str(scores[-1]))
    # plt.text(len(mean_scores)-1, mean_scores[-1], str(mean_scores[-1]))
    plt.show(block=False)
    if pause:
        plt.pause(.1)
