import json
import numpy as np
import pandas as pd
from utils.json_encoder import CustomJSONEncoder

def test_serialization():
    data = {
        'integer': np.int64(42),
        'float': np.float64(3.14),
        'array': np.array([1, 2, 3]),
        'dataframe': pd.DataFrame({'a': [1, 2], 'b': [3, 4]}),
        'series': pd.Series([1, 2, 3]),
        'bool': np.bool_(True),
        'nan': np.nan
    }

    try:
        json_str = json.dumps(data, cls=CustomJSONEncoder)
        print("Serialization successful!")
        print(json_str)
        return True
    except TypeError as e:
        print(f"Serialization failed: {e}")
        return False

if __name__ == "__main__":
    test_serialization()
