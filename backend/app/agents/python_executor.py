"""
Python Executor - Varno izvajanje Python kode v sandbox okolju.

Omogoča agentom izvajanje podatkovnih analiz (trendi, agregacije,
statistike) ki presegajo zmožnosti SQL-a. Koda se izvaja z omejenimi
pravicami in dostopom do baze samo preko query_db().
"""

import io
import re
import json
import signal
import logging
from typing import Callable
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)

# Moduli ki so dovoljeni za import v sandbox okolju
ALLOWED_MODULES = {
    "pandas", "numpy", "json", "datetime", "math",
    "statistics", "collections", "decimal", "re",
}

# Moduli ki so prepovedani (varnostno tveganje)
FORBIDDEN_MODULES = {
    "os", "sys", "subprocess", "socket", "http", "shutil",
    "pathlib", "signal", "ctypes", "pickle", "importlib",
    "builtins", "code", "codeop", "compileall", "py_compile",
    "multiprocessing", "threading", "asyncio", "io",
    "ftplib", "smtplib", "urllib", "requests", "webbrowser",
    "tempfile", "glob", "fnmatch", "sqlite3",
}

# Vzorci kode ki so prepovedani
FORBIDDEN_PATTERNS = [
    r'__import__\s*\(',
    r'exec\s*\(',
    r'eval\s*\(',
    r'compile\s*\(',
    r'globals\s*\(',
    r'locals\s*\(',
    r'getattr\s*\(',
    r'setattr\s*\(',
    r'delattr\s*\(',
    r'vars\s*\(',
    r'dir\s*\(',
    r'open\s*\(',
    r'input\s*\(',
    r'breakpoint\s*\(',
    r'__builtins__',
    r'__subclasses__',
    r'__bases__',
    r'__mro__',
    r'__class__',
    r'\btype\s*\(',
    r'importlib',
]

MAX_RESULT_SIZE = 50 * 1024  # 50KB


class TimeoutError(Exception):
    """Prekoračitev časovne omejitve."""
    pass


class SecurityError(Exception):
    """Koda vsebuje nevarne operacije."""
    pass


class PythonExecutor:
    """Varen Python executor z sandbox okoljem."""

    def __init__(self, db_query_func: Callable[[str], list[dict]]):
        """
        Args:
            db_query_func: Funkcija ki izvede SELECT poizvedbo in vrne list[dict].
                           Mora že imeti varnostne kontrole (SELECT only, forbidden keywords).
        """
        self._raw_query = db_query_func

    def execute(self, code: str, timeout: int = 30) -> dict:
        """
        Izvede Python kodo v sandbox okolju.

        Args:
            code: Python koda za izvajanje. Mora nastaviti `result` spremenljivko.
            timeout: Časovna omejitev v sekundah.

        Returns:
            dict z ključi:
            - success: bool
            - result: podatki iz `result` spremenljivke
            - output: stdout output
            - error: napaka (če ni uspelo)
        """
        try:
            # 1. Varnostna kontrola
            self._safety_check(code)

            # 2. Pripravi sandbox okolje
            sandbox_globals = self._build_globals()

            # 3. Capture stdout
            stdout_capture = io.StringIO()
            sandbox_globals['print'] = lambda *args, **kwargs: print(
                *args, file=stdout_capture, **kwargs
            )

            # 4. Nastavi timeout
            def _timeout_handler(signum, frame):
                raise TimeoutError(
                    f"Python skripta je presegla časovno omejitev ({timeout}s)"
                )

            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout)

            try:
                # 5. Izvedi kodo
                exec(code, sandbox_globals)

                # 6. Vzemi rezultat
                if 'result' not in sandbox_globals:
                    return {
                        "success": False,
                        "error": "Skripta mora nastaviti spremenljivko 'result' z rezultatom analize.",
                        "output": stdout_capture.getvalue()[:2000],
                    }

                result = sandbox_globals['result']
                result = self._ensure_serializable(result)

                # Preveri velikost
                result_json = json.dumps(result, ensure_ascii=False, default=str)
                if len(result_json) > MAX_RESULT_SIZE:
                    return {
                        "success": False,
                        "error": f"Rezultat je prevelik ({len(result_json)} bajtov, max {MAX_RESULT_SIZE}). Zmanjšaj obseg analize.",
                        "output": stdout_capture.getvalue()[:2000],
                    }

                return {
                    "success": True,
                    "result": result,
                    "output": stdout_capture.getvalue()[:2000],
                }

            finally:
                # Ponastavi alarm in handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

        except TimeoutError as e:
            return {"success": False, "error": str(e)}
        except SecurityError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {
                "success": False,
                "error": f"Napaka pri izvajanju Python skripte: {type(e).__name__}: {str(e)}"
            }

    def _safety_check(self, code: str) -> None:
        """Statična analiza kode pred izvajanjem."""
        # Preveri prepovedane vzorce
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, code):
                raise SecurityError(
                    f"Koda vsebuje prepovedan vzorec: {pattern}"
                )

        # Preveri prepovedane module v import stavkih
        # Ujemi: import os, from os import, import os.path
        import_pattern = r'(?:^|\n)\s*(?:import|from)\s+(\w+)'
        for match in re.finditer(import_pattern, code):
            module_name = match.group(1)
            if module_name in FORBIDDEN_MODULES:
                raise SecurityError(
                    f"Import prepovedanega modula: {module_name}"
                )
            if module_name not in ALLOWED_MODULES:
                raise SecurityError(
                    f"Import nedovoljenega modula: {module_name}. "
                    f"Dovoljeni: {', '.join(sorted(ALLOWED_MODULES))}"
                )

    def _build_globals(self) -> dict:
        """Zgradi sandbox global namespace z omejenimi builtins."""
        import math
        import statistics
        import collections
        from decimal import Decimal
        from datetime import datetime, date, timedelta

        # Safe builtins (brez open, exec, eval, compile, __import__, input, breakpoint)
        safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool,
            'chr': chr, 'dict': dict, 'divmod': divmod, 'enumerate': enumerate,
            'filter': filter, 'float': float, 'format': format,
            'frozenset': frozenset, 'hasattr': hasattr, 'hash': hash,
            'hex': hex, 'int': int, 'isinstance': isinstance,
            'issubclass': issubclass, 'iter': iter, 'len': len, 'list': list,
            'map': map, 'max': max, 'min': min, 'next': next,
            'oct': oct, 'ord': ord, 'pow': pow, 'range': range,
            'repr': repr, 'reversed': reversed, 'round': round,
            'set': set, 'slice': slice, 'sorted': sorted, 'str': str,
            'sum': sum, 'tuple': tuple, 'zip': zip,
            'True': True, 'False': False, 'None': None,
            'ValueError': ValueError, 'TypeError': TypeError,
            'KeyError': KeyError, 'IndexError': IndexError,
            'Exception': Exception, 'StopIteration': StopIteration,
        }

        # Pre-import dovoljenih modulov
        import pandas as pd
        import numpy as np

        sandbox = {
            '__builtins__': safe_builtins,
            'pd': pd,
            'pandas': pd,
            'np': np,
            'numpy': np,
            'json': json,
            'math': math,
            'statistics': statistics,
            'collections': collections,
            'Decimal': Decimal,
            'datetime': datetime,
            'date': date,
            'timedelta': timedelta,
            're': re,
            'query_db': self._safe_query_db,
        }

        return sandbox

    def _safe_query_db(self, sql: str) -> 'pd.DataFrame':
        """
        Izvede SELECT poizvedbo in vrne pandas DataFrame.

        Avtomatsko doda TOP 1000 če ni prisoten.
        Samo SELECT poizvedbe so dovoljene.
        """
        import pandas as pd

        sql = sql.strip()

        # Varnostna kontrola
        if not sql.upper().startswith("SELECT"):
            raise SecurityError("Samo SELECT poizvedbe so dovoljene v query_db()")

        # Preveri za nevarne operacije
        dangerous = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
            "EXEC", "EXECUTE", "TRUNCATE", "CREATE"
        ]
        sql_upper = sql.upper()
        for kw in dangerous:
            if re.search(rf'\b{kw}\b', sql_upper):
                raise SecurityError(f"Nevarna operacija v query_db(): {kw}")

        # Dodaj TOP 1000 če ni prisoten
        if "TOP" not in sql_upper:
            sql = sql.replace("SELECT", "SELECT TOP 1000", 1)

        # Izvedi poizvedbo
        rows = self._raw_query(sql)
        return pd.DataFrame(rows)

    @staticmethod
    def _ensure_serializable(obj) -> any:
        """Pretvori objekt v JSON-serializabilno obliko."""
        if obj is None:
            return None

        # Pandas DataFrame
        try:
            import pandas as pd
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient='records')
            if isinstance(obj, pd.Series):
                return obj.to_dict()
        except ImportError:
            pass

        # Numpy tipi
        try:
            import numpy as np
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, np.bool_):
                return bool(obj)
        except ImportError:
            pass

        # Osnovni tipi
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {
                str(k): PythonExecutor._ensure_serializable(v)
                for k, v in obj.items()
            }
        if isinstance(obj, (list, tuple)):
            return [PythonExecutor._ensure_serializable(item) for item in obj]
        if isinstance(obj, set):
            return [PythonExecutor._ensure_serializable(item) for item in obj]

        # Fallback
        return str(obj)
