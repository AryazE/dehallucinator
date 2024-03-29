from .logic import calculate_credit_score
from .utils import read_csv

def get_credit_scores():
    """
    Reads personal data from the data.csv file, calculates credit scores for each row, and returns the list of scores
    """
    # Read the csv file
    data = read_csv('data.csv')
    # Calculate credit scores
    credit_scores = []
    for i in range(len(data)):
        credit_scores.append(calculate_credit_score(data, i))
    # Return the credit scores
    return credit_scores

if __name__ == '__main__':
    # Get credit scores
    credit_scores = get_credit_scores()
    # Print the credit scores
    print(credit_scores)