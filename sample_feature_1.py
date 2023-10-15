# Sample feature 1 - Data processing utility
def process_data(data):
    """Process input data and return transformed results."""
    return [item.upper() for item in data if item]

if __name__ == "__main__":
    test_data = ["hello", "world", "agent", "ops"]
    result = process_data(test_data)
    print(f"Processed data: {result}")