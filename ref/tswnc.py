
# temperature sensing with ntc circuit.pdf
# https://www.ti.com/lit/an/sboa323a/sboa323a.pdf

import math
import re

def get_res_series(series:str) -> list:
  ser = re.sub(r"[^a-zA-Z0-9]", "", series).lower()
  if ser == "e24":
    base = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
            3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
  elif ser == "e96":
    base = [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 
            1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40, 1.43, 
            1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74, 
            1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 
            2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 
            2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 
            3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 
            3.83, 3.92, 4.02, 4.12, 4.22, 4.32, 4.42, 4.53, 
            4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 
            5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 
            6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 
            8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76]

  full = []
  for exp in range(0, 7):
      for b in base:
          full.append(b * (10 ** exp))
  return full

def select_resistor(target, series:str="e24"):
    standard_values = get_res_series(series)
    closest = min(standard_values, key=lambda x: abs(x - target))
    err_percent = (closest - target) / target
    return closest, err_percent

def calc_resistor(expr):
    prec = {'|':1, '&':2}
    nums, ops = [], []
    i, n = 0, len(expr)
    
    while i < n:
        c = expr[i]
        if c == '(':
            ops.append(c)
            i += 1
        elif c == ')':
            while ops[-1] != '(':
                op = ops.pop()
                b, a = nums.pop(), nums.pop()
                nums.append(a + b if op == '&' else a*b/(a+b) if a+b else 0)
            ops.pop()
            i += 1
        elif c in '&|':
            while ops and ops[-1] != '(' and prec[ops[-1]] >= prec[c]:
                op = ops.pop()
                b, a = nums.pop(), nums.pop()
                nums.append(a + b if op == '&' else a*b/(a+b) if a+b else 0)
            ops.append(c)
            i += 1
        elif c.isdigit() or c == '.':
            j = i
            while j < n and (expr[j].isdigit() or expr[j] == '.'): j += 1
            num = float(expr[i:j])
            if j < n and expr[j] == 'k': num *= 1e3; j += 1
            elif j < n and expr[j] == 'm': num *= 1e6; j += 1
            nums.append(num)
            i = j
        else:
            i += 1
    
    while ops:
        op = ops.pop()
        b, a = nums.pop(), nums.pop()
        nums.append(a + b if op == '&' else a*b/(a+b) if a+b else 0)
    
    return nums[0]

if __name__ == "__main__":
    rt = [42.506e3, 0.974e3]
    v_out = [0.05, 3.25]
    vdd = 3.3
    r4 = 1.5e3

    r1 = math.sqrt(rt[0] * rt[1])
    r1_act, r1_err = select_resistor(r1, "e24")

    v_in = [(lambda x: vdd * r1_act / (x + r1_act))(x) for x in rt]
    g = (v_out[1] - v_out[0]) / (v_in[1] - v_in[0])

    r2_r3 = r4 / (g - 1)
    r3 = (r4 * vdd) / (v_in[1] * g - v_out[1])
    r2 = (r2_r3 * r3) / (r3 - r2_r3)
    r2_act, r2_err = select_resistor(r2, "e24")
    r3_act, r3_err = select_resistor(r3, "e24")

    r2_r3_act = calc_resistor(f"{r2_act}|{r3_act}")
    g_act = (r2_r3_act + r4) / r2_r3_act
    g_err = (g_act - g) / g

    off = -r4 * vdd / r3
    off_act = -r4 * vdd / r3_act
    off_err = (off_act - off) / off

    v_out_act = [(lambda x: g_act * x + off_act)(x) for x in v_in]
    v_out_err = [(lambda x: (x[0] - x[1]) / x[1])(x) for x in zip(v_out_act, v_out)]

    print(f"r1={r1_act}({r1}{r1_err:+.2%})")
    print(f"r2={r2_act}({r2}{r2_err:+.2%})")
    print(f"r3={r3_act}({r3}{r3_err:+.2%})")
    print(f"{r4=}")
    print()
    print(f"g={g_act}({g}{g_err:+.2%})")
    print(f"off={off_act}({off}{off_err:+.2%})")
    print()
    print(f"v_out = v_in * {g_act} + {off_act}")
    print(f"v_out = {v_out_act}")
    print(f"v_out_err=[{v_out_err[0]:+.2%}, {v_out_err[1]:+.2%}]")
