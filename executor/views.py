# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import subprocess, tempfile, os, json, shutil, sys

def _make_temp_under_sandbox():
    base = "/sandbox"
    os.makedirs(base, exist_ok=True)
    return tempfile.mkdtemp(dir=base)

@csrf_exempt
def run_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    body = json.loads(request.body.decode("utf-8"))
    code = body.get("code", "")
    lang = body.get("language", "python")
    input_data = body.get("input", "")

    temp_dir = _make_temp_under_sandbox()

    try:
        if lang == "python":
            # Write a sitecustomize.py that disables networking
            site_block = """\
import builtins
import socket

class _NoNetSocket(socket.socket):
    def __init__(self, *a, **kw):
        raise RuntimeError("Network access is disabled in this sandbox.")

# Monkeypatch high-level connect attempts
def _blocked(*a, **kw):
    raise RuntimeError("Network access is disabled in this sandbox.")

socket.socket = _NoNetSocket
socket.create_connection = _blocked
"""

            with open(os.path.join(temp_dir, "sitecustomize.py"), "w") as f:
                f.write(site_block)

            file_path = os.path.join(temp_dir, "main.py")
            with open(file_path, "w") as f:
                f.write(code)

            try:
                result = subprocess.run(
                    ["python3", file_path],
                    input=input_data.encode(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                    cwd=temp_dir,           # <- run INSIDE the temp dir
                )
            except subprocess.TimeoutExpired:
                return JsonResponse({"error": "Execution timed out"}, status=400)

        elif lang == "cpp":
            source_path = os.path.join(temp_dir, "main.cpp")
            binary_path = os.path.join(temp_dir, "main")
            with open(source_path, "w") as f:
                f.write(code)

            compile_proc = subprocess.run(
                ["g++", source_path, "-o", binary_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=temp_dir,
            )
            if compile_proc.returncode != 0:
                return JsonResponse({"error": compile_proc.stderr.decode()}, status=400)

            try:
                result = subprocess.run(
                    [binary_path],
                    input=input_data.encode(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                    cwd=temp_dir,
                )
            except subprocess.TimeoutExpired:
                return JsonResponse({"error": "Execution timed out"}, status=400)

        elif lang == "java":
            source_path = os.path.join(temp_dir, "Main.java")
            with open(source_path, "w") as f:
                f.write(code)

            compile_proc = subprocess.run(
                ["javac", source_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=temp_dir,
            )
            if compile_proc.returncode != 0:
                return JsonResponse({"error": compile_proc.stderr.decode()}, status=400)

            try:
                result = subprocess.run(
                    ["java", "-cp", temp_dir, "Main"],
                    input=input_data.encode(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                    cwd=temp_dir,
                )
            except subprocess.TimeoutExpired:
                return JsonResponse({"error": "Execution timed out"}, status=400)

        else:
            return JsonResponse({"error": "Unsupported language"}, status=400)

        return JsonResponse({
            "output": result.stdout.decode(),
            "error": result.stderr.decode()
        })

    finally:
        # hard cleanup
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
