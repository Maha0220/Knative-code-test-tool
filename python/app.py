from flask import Flask, request, jsonify
import multiprocessing
import traceback
import builtins

app = Flask(__name__)

TIMEOUT = 10

SAFE_BUILTINS = {
    'abs': abs, 'all': all, 'any': any, 'bool': bool,
    'dict': dict, 'enumerate': enumerate, 'float': float,
    'int': int, 'len': len, 'list': list, 'max': max,
    'min': min, 'range': range, 'str': str, 'sum': sum,
}

def run_in_process(code, func_name, func_args, conn):
    try:
        local_vars = {}
        global_vars = {"__builtins__": SAFE_BUILTINS}

        exec(code, global_vars, local_vars)

        if func_name not in local_vars:
            conn.send({
                "status": "error",
                "message": f"Function {func_name} not defined"
            })
            conn.close()
            return

        output = local_vars[func_name](*func_args)

        conn.send({
            "status": "success",
            "output": output
        })
    except Exception:
        conn.send({
            "status": "error",
            "message": traceback.format_exc()
        })
    finally:
        conn.close()


@app.route("/run", methods=["POST"])
def run_code():
    data = request.json
    code = data.get("code")
    test_cases = data.get("test_cases", [])

    results = []

    for idx, tc in enumerate(test_cases):
        parent_conn, child_conn = multiprocessing.Pipe()

        p = multiprocessing.Process(
            target=run_in_process,
            args=(code, tc["function"], tc["input"], child_conn)
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

        if parent_conn.poll():
            res = parent_conn.recv()
        else:
            res = {"status": "error", "message": "No response from execution process"}

        if res["status"] == "success":
            output = res["output"]
            status = "pass" if output == tc["expected"] else "fail"
            results.append({
                "test_case": idx,
                "status": status,
                "output": output,
                "expected": tc["expected"]
            })
        else:
            results.append({
                "test_case": idx,
                "status": "error",
                "message": res["message"]
            })

    return jsonify(results)
