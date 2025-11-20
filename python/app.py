from flask import Flask, request, jsonify
import multiprocessing
import traceback
import builtins

app = Flask(__name__)

# 실행 제한 시간 (초)
TIMEOUT = 10

# 허용된 내장 함수만 남기기
SAFE_BUILTINS = {
    'abs': abs,
    'all': all,
    'any': any,
    'bool': bool,
    'dict': dict,
    'enumerate': enumerate,
    'float': float,
    'int': int,
    'len': len,
    'list': list,
    'max': max,
    'min': min,
    'range': range,
    'str': str,
    'sum': sum,
    'print': print,
}

def run_function(code, func_name, func_args, return_dict):
    try:
        # 제한된 내장 함수만 허용
        local_vars = {}
        global_vars = {"__builtins__": SAFE_BUILTINS}

        # 코드 실행
        exec(code, global_vars, local_vars)

        if func_name not in local_vars:
            return_dict['status'] = 'error'
            return_dict['message'] = f"Function {func_name} not defined"
            return

        output = local_vars[func_name](*func_args)
        return_dict['status'] = 'success'
        return_dict['output'] = output
    except Exception:
        return_dict['status'] = 'error'
        return_dict['message'] = traceback.format_exc()

@app.route("/run", methods=["POST"])
def run_code():
    data = request.json
    code = data.get("code")
    test_cases = data.get("test_cases", [])

    results = []

    for idx, tc in enumerate(test_cases):
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        func_name = tc.get("function")
        func_args = tc.get("input", [])
        expected = tc.get("expected")

        p = multiprocessing.Process(
            target=run_function,
            args=(code, func_name, func_args, return_dict)
        )
        p.start()
        p.join(TIMEOUT)

        if p.is_alive():
            p.terminate()
            results.append({
                "test_case": idx,
                "status": "error",
                "message": "Execution timed out"
            })
            continue

        if return_dict['status'] == 'success':
            status = 'pass' if return_dict['output'] == expected else 'fail'
            results.append({
                "test_case": idx,
                "status": status,
                "output": return_dict['output'],
                "expected": expected
            })
        else:
            results.append({
                "test_case": idx,
                "status": "error",
                "message": return_dict.get('message', 'Unknown error')
            })

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)