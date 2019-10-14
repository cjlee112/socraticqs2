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
    result = {}
    if calculation and data:
        result['w_o_courselets'] = int(
            int(data.get('bp_student_number', 200)) *
            int(data.get('question_parts', 24)) *
            ((1 - int(data.get('w_o_cr_correct', 99)) / 100)))
        result['w_courselets'] = int(
            int(data.get('bp_student_number', 200)) *
            int(data.get('question_parts', 24)) *
            ((1 - int(data.get('average_score', 72)) / 100)))
    return result
