import subprocess
import pathlib

def check_health():
    """Check FreeLLMAPI proxy health and write result to /tmp/codex_health_check.txt."""
    url = "http://127.0.0.1:8443/health"
    try:
        result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url], capture_output=True, text=True, timeout=5)
        status = result.stdout.strip()
        healthy = status == "200"
    except Exception as e:
        healthy = False
        status = str(e)
    out_path = pathlib.Path("/tmp/codex_health_check.txt")
    out_path.write_text(f"healthy={healthy}, status={status}\n")
    return healthy

if __name__ == "__main__":
    check_health()
