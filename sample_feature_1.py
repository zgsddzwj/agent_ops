# Sample feature 1 - Data processing utility
def process_data(data, transformation="upper"):
    """Process input data and return transformed results.
    
    Args:
        data: List of strings to process
        transformation: Type of transformation ('upper', 'lower', 'title')
    
    Returns:
        List of transformed strings
    """
    if transformation == "upper":
        return [item.upper() for item in data if item]
    elif transformation == "lower":
        return [item.lower() for item in data if item]
    elif transformation == "title":
        return [item.title() for item in data if item]
    else:
        raise ValueError(f"Unknown transformation: {transformation}")

if __name__ == "__main__":
    test_data = ["hello", "world", "agent", "ops"]
    result = process_data(test_data)
    print(f"Processed data: {result}")