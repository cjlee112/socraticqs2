def get_result_calculation(data, calculation):
        if calculation and data:
            result = {}
            for field, value in data.items():
                if calculation.get(field, {}).get('analys', {}).get('formula'):
                    if value:
                        if value.isdigit() and calculation.get(field, {}).get('type') == 'number':
                            result.update({
                                field: calculation.get(field, {}).get('analys').get('text', '{}').format(
                                    int(value) * calculation.get(field, {}).get('analys').get('formula')
                                )
                            })  
                        else:
                            result.update({
                                field: 'Value not integer'
                            })
                    else:
                        result.update({
                            field: 'Value not filled'
                        })
        return result