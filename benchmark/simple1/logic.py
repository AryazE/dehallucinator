# Calculate credit score based on salary and age
def calculate_credit_score(data):
    # Get salary and age from the data
    salary = data['salary']
    age = data['age']
    # Calculate credit score
    credit_score = int(salary) / int(age)
    # Return the credit score
    return credit_score