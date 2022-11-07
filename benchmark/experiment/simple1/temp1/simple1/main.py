
# Get personal data from the data.csv file and calculate credit scores
def get_credit_scores():
    data = read_csv('data.csv')
    credit_scores = []
    for i in range(len(data)):
        credit_scores.append(calculate_credit_score(data, i))
    return credit_scoresif __name__ == '__main__':
    # Get credit scores
    credit_scores = get_credit_scores()
    # Print the credit scores
    print(credit_scores)