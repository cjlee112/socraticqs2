def get_result_calculation(data, calculation) -> dict:
    """
    Impact analisys calculation formula.

    Formula:
      estimated blindspots = (number of students) * (number of question-parts) * (1 - (average fraction correct))
    For example: 200 * 24 * (1 - 0.72) = 1344

    Return:
     - dict
     - empty dict in case data is empty
    """
    def get_value_or_default(data, key, default):
        value = data.get(key)
        return value if value and value != '' else default

    result = {}
    if calculation and data:
        result['w_o_courselets'] = int(get_value_or_default(data, 'misconception_a_day', 5)) * 7
        result['w_courselets'] = int(
            int(get_value_or_default(data, 'bp_student_number', 200)) *
            int(get_value_or_default(data, 'question_parts', 24)) *
            ((1 - int(get_value_or_default(data, 'average_score', 72)) / 100)))
    return result
