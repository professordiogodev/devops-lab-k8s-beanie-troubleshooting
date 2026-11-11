#!/usr/bin/env python3
import json, os, re, socket, subprocess, sys, time, urllib.request, urllib.error
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
NS = "beanie-broken"
passed = failed = 0
IMG = open(".image").read().strip()


def check(desc, ok, hint=""):
    global passed, failed
    if ok:
        passed += 1; print("PASS  " + desc, flush=True)
    else:
        failed += 1; print("FAIL  " + desc + (("   -> " + hint) if hint else ""), flush=True)


def k(*a, timeout=120):
    r = subprocess.run(("kubectl",) + a, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def kj(*a):
    rc, out, _ = k(*a, "-o", "json")
    try:
        return json.loads(out) if rc == 0 else None
    except Exception:
        return None


def wait_for(fn, secs, step=4):
    end = time.time() + secs
    while time.time() < end:
        try:
            if fn():
                return True
        except Exception:
            pass
        time.sleep(step)
    return False


def finish():
    print()
    print(("ALL CHECKS PASSED (%d/%d)" % (passed, passed)) if failed == 0 else ("%d check(s) failed, %d passed" % (failed, passed)))
    sys.exit(1 if failed else 0)


def dep(name):
    return kj("get", "deployment", name, "-n", NS) or {}


def c0(name):
    return dep(name).get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0]


def ready(name, n=1):
    return dep(name).get("status", {}).get("readyReplicas", 0) >= n


print("kubectl context: " + k("config", "current-context")[1].strip())
check("the namespace %s exists (run ./setup.sh)" % NS, k("get", "namespace", NS)[0] == 0)
if k("get", "namespace", NS)[0] != 0:
    finish()
print("== The six faults ==")
img = c0("menu").get("image", "")
check("1. menu: the image tag is real, and both replicas are Ready", img == IMG and wait_for(lambda: ready("menu", 2), 120), "image is %s" % img)
req = (c0("payments").get("resources", {}).get("requests", {}) or {}).get("cpu", "")
cpu = float(req[:-1]) / 1000 if req.endswith("m") else float(req or 0)
check("2. payments: asks for a sane amount of CPU (%s) and is Ready" % (req or "none"), cpu <= 1 and wait_for(lambda: ready("payments"), 120))
check("3. orders: starts the right service (args ends with orders) and is Ready", (c0("orders").get("args") or [])[-1:] == ["orders"] and wait_for(lambda: ready("orders"), 120))
rp = (c0("gateway").get("readinessProbe", {}).get("httpGet", {}) or {}).get("path")
check("4. gateway: the readiness probe asks for /readyz and both replicas are Ready", rp == "/readyz" and wait_for(lambda: ready("gateway", 2), 120), "readiness path is %s" % rp)
eps = kj("get", "endpoints", "notifications", "-n", NS) or {}
check("5. notifications: the Service has endpoints (it selects the pods that exist)", wait_for(lambda: any(s.get("addresses") for s in (kj("get", "endpoints", "notifications", "-n", NS) or {}).get("subsets", [])), 60))
lim = (c0("reporter").get("resources", {}).get("limits", {}) or {}).get("memory", "")
mi = 0
m = re.match(r"(\d+)(Mi|Gi|M|G)?", lim)
if m:
    mi = int(m.group(1)) * (1024 if m.group(2) == "Gi" else 1)
def reporter_ok():
    pods = (kj("get", "pods", "-n", NS, "-l", "app=reporter") or {}).get("items", [])
    return bool(pods) and all(p["status"].get("phase") == "Running" and all(c["ready"] is not False for c in p["status"].get("containerStatuses", [])) and
                              (p["status"]["containerStatuses"][0].get("lastState", {}).get("terminated", {}).get("reason") != "OOMKilled" or p["status"]["containerStatuses"][0]["state"].get("running")) for p in pods)
def reporter_stable():
    pods = (kj("get", "pods", "-n", NS, "-l", "app=reporter") or {}).get("items", [])
    return bool(pods) and pods[0]["status"]["containerStatuses"][0]["state"].get("running") is not None
check("6. reporter: the memory limit (%s) fits what it needs (256Mi or more) and it stays Running" % (lim or "none"), mi >= 256 and wait_for(reporter_stable, 90), "kubectl describe pod, look at Last State")
time.sleep(15)
pods = (kj("get", "pods", "-n", NS, "-l", "app=reporter") or {}).get("items", [])
check("... and it is not being killed any more (no OOMKilled in its current state)", bool(pods) and pods[0]["status"]["containerStatuses"][0]["state"].get("running") is not None)

print("== The whole thing, end to end ==")
bad = [p["metadata"]["name"] for p in (kj("get", "pods", "-n", NS) or {}).get("items", []) if p["status"].get("phase") != "Running" or not all(c["ready"] for c in p["status"].get("containerStatuses", []))]
check("every pod in the namespace is Running and Ready", not bad, ", ".join(bad))
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
pf = subprocess.Popen(["kubectl", "port-forward", "-n", NS, "svc/gateway", "%d:8000" % port], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    time.sleep(3)
    def order():
        try:
            req = urllib.request.Request("http://127.0.0.1:%d/api/orders" % port, json.dumps({"customer": "Ana", "items": [{"item_id": "flat-white", "quantity": 2}]}).encode(), {"Content-Type": "application/json"})
            return urllib.request.urlopen(req, timeout=10).status
        except urllib.error.HTTPError as e:
            return e.code
        except Exception:
            return 0
    st = 0
    for _ in range(10):
        st = order()
        if st == 201:
            break
        time.sleep(4)
    check("an order placed through the gateway is paid (201): all five services talk to each other again", st == 201, "got %s" % st)
finally:
    pf.terminate()
d = open("DIAGNOSIS.md").read()
check("DIAGNOSIS.md is filled in (no TODO) and mentions what each fault looked like", "TODO" not in d and all(re.search(p, d, re.I) for p in (r"ImagePull|ErrImage", r"Pending|FailedScheduling|Insufficient", r"CrashLoop|exit code|usage", r"readiness|Unhealthy|404|0/1", r"endpoints|selector", r"OOMKilled|137")))
finish()
