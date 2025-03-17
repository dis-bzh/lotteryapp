def parse_input(input_str):
    """
    Parse a string containing numbers and/or intervals.
    Examples of input: "1-10,15-20" or "2,4,6,8".
    Returns a list of integers.
    """
    numbers = []
    parts = input_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start_str, end_str = part.split('-')
                start = int(start_str)
                end = int(end_str)
                numbers.extend(range(start, end + 1))
            except ValueError:
                pass  # Ignore improperly formatted parts.
        else:
            try:
                numbers.append(int(part))
            except ValueError:
                pass
    return numbers
