import json
import numpy as np
import pandas as pd
from flask.json.provider import DefaultJSONProvider

class CustomJSONProvider(DefaultJSONProvider):
    """
    Custom JSON provider to handle NumPy and Pandas data types
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif pd.isna(obj):
            return None
        return super().default(obj)
