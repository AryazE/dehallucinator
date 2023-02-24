def calculate_credit_score(data, index):
    """
    Calculate credit score based on salary and age
    """
    # Get salary and age from the data
    salary = data[index]['salary']
    age = data[index]['age']
    # Calculate credit score
    credit_score = int(salary) / int(age)
    # Return the credit score
    return credit_score