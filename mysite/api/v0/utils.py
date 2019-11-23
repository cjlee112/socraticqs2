def get_result_course_calculation(data, calculation) -> dict:
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


def get_result_courselet_calculation(data, calculation) -> dict:
    """
    Impact analisys calculation formula.

    Formula:
      estimated blindspots = average_score * Base
        Base == 1344 (Calculated impact for your class for Practice Exam - BP for a Course)]
    For example: 1344 * 72/100 = 1344

    Return:
     - dict
     - empty dict in case data is empty
    """
    result = {}
    if calculation and data:
        base = int(data.get('base', 1344))
        result['w_o_courselets'] = int(round(base * int(data.get('average_score', 25)) / 100))
        result['w_courselets'] = int(round(base * 0.9))
    return result
