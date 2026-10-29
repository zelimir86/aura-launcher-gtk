import math
import re

ALLOWED_NAMES = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "pow": pow,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "pi": math.pi,
    "e": math.e,
}

def evaluate_math(expr: str):
    clean = expr.strip()
    if not clean:
        return None
    
    # Simple check if expression looks like math
    if not re.match(r'^[0-9\+\-\*\/\%\^\(\)\.\,\s\w]+$', clean):
        return None
    
    # Must look like an actual expression: an operator or a function call.
    # A bare number ("5") is not interesting, so it is not treated as math.
    has_operator = re.search(r'[\+\-\*\/\%\^]', clean) is not None
    has_function = re.search(r'[a-zA-Z_]\w*\s*\(', clean) is not None
    if not (has_operator or has_function):
        return None

    # Replace ^ with ** for python exponentiation
    python_expr = clean.replace('^', '**')

    try:
        # Evaluate safely in restricted namespace
        result = eval(python_expr, {"__builtins__": None}, ALLOWED_NAMES)
        if isinstance(result, (int, float)):
            # Format nicely
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return str(result)
    except Exception:
        pass
    
    return None
