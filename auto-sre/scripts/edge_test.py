"""Test safe_score edge cases to prove 0.00/1.00 can never appear."""
def safe_score(x):
    import math
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return 0.01
    val = float(x)
    if val >= 0.995:
        val = 0.989
    if val < 0.005:
        val = 0.01
    return val

tests = [0.0, 1e-6, 0.001, 0.004, 0.005, 0.01, 0.5, 0.989, 0.99, 0.995, 0.999, 0.999999, 1.0, None]
failures = 0
for t in tests:
    s = safe_score(t)
    fmt = f"{s:.2f}"
    ok = fmt != "0.00" and fmt != "1.00"
    status = "PASS" if ok else "FAIL !!!"
    if not ok:
        failures += 1
    print(f"  input={str(t):>12}  safe_score={s:<10}  .2f={fmt}  {status}")

print(f"\nTotal failures: {failures}")
import sys
sys.exit(failures)
