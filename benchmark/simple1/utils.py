# Parse csv string into a list of dictionaries
def parse_csv(contents):
    # Split the csv string into lines
    lines = contents.splitlines()
    # Split the first line into headers
    headers = lines[0].split(',')
    # Create a list of dictionaries
    data = []
    # Iterate over the lines
    for line in lines[1:]:
        # Split the line into values
        values = line.split(',')
        # Create a dictionary
        d = {}
        # Iterate over the headers and values
        for header, value in zip(headers, values):
            # Add the header and value to the dictionary
            d[header] = value
        # Add the dictionary to the list
        data.append(d)
    # Return the list of dictionaries
    return data

# Read a csv file into a list of dictionaries
def read_csv(file_name):
    # Open the csv file
    with open(file_name, 'r') as f:
        # Read the csv file
        contents = f.read()
        # Parse the csv file
        data = parse_csv(contents)
        # Return the data
        return data