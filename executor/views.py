# views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os, subprocess, tempfile, json

 
@csrf_exempt
def run_code(request):
    if request.method == "POST":
        body = json.loads(request.body.decode("utf-8"))
        code = body.get("code", "")
        lang = body.get("language", "python")
        input_data = body.get("input", "")

        temp_dir = tempfile.mkdtemp()
        try:
            if lang == "python":
                file_path = os.path.join(temp_dir, "main.py")
                with open(file_path, "w") as f:
                    f.write(code)

                try:
                    result = subprocess.run(
                        ["python", file_path],
                        input=input_data.encode(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5
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
                    stderr=subprocess.PIPE
                )
                if compile_proc.returncode != 0:
                    return JsonResponse({"error": compile_proc.stderr.decode()}, status=400)

                try:
                    result = subprocess.run(
                        [binary_path],
                        input=input_data.encode(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5
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
                    stderr=subprocess.PIPE
                )
                if compile_proc.returncode != 0:
                    return JsonResponse({"error": compile_proc.stderr.decode()}, status=400)

                try:
                    result = subprocess.run(
                        ["java", "-cp", temp_dir, "Main"],
                        input=input_data.encode(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5
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
            # cleanup
            try:
                for file in os.listdir(temp_dir):
                    os.unlink(os.path.join(temp_dir, file))
                os.rmdir(temp_dir)
            except:
                pass

    return JsonResponse({"error": "Invalid request"}, status=400)
