"""Research statistics; no diagnostic threshold defaults or implicit imputation."""
from statistics import median, stdev
from math import sqrt
from datetime import timedelta
from .quality import comparable, convert, Inconclusive

def baseline(ms, minimum_observations):
    ms=sorted(ms,key=lambda m:(m.timestamp,m.id))
    comparable(ms)
    if len({m.id for m in ms}) != len(ms) or len({m.timestamp for m in ms}) != len(ms) or len(ms) < minimum_observations:
        raise Inconclusive("INSUFFICIENT_BASELINE")
    if any(m.phase != "PRE_MISSION" for m in ms):
        raise Inconclusive("BASELINE_NOT_PREFLIGHT")
    values = [convert(m.value,m.unit,ms[0].unit) for m in ms]
    center = median(values)
    return {"value": center, "mad": median(abs(v-center) for v in values),
            "unit": ms[0].unit, "input_ids": [m.id for m in ms], "status": "RESEARCH_ONLY"}

def hour_average(ms, end):
    if not ms:
        raise Inconclusive("INSUFFICIENT_TEMPORAL_COVERAGE")
    comparable(ms)
    if any(m.variable != "environment.ppco2" or not m.compartment or m.method != "INTERVAL_MEAN" for m in ms):
        raise Inconclusive("INVALID_AGGREGATION_METHOD")
    if len({m.device_id for m in ms}) != 1:
        raise Inconclusive("CONFLICTING_DATA")
    start = end - timedelta(hours=1)
    cursor, integral = start, 0.0
    for m in sorted(ms, key=lambda m: (m.timestamp,m.id)):
        if m.interval_end is None:
            raise Inconclusive("INSUFFICIENT_TEMPORAL_COVERAGE")
        # Intervals are asserted means over their entire interval, never held point samples.
        if m.timestamp < start or m.interval_end > end or m.timestamp != cursor:
            raise Inconclusive("INSUFFICIENT_TEMPORAL_COVERAGE")
        integral += convert(m.value,m.unit,"mmHg") * (m.interval_end-m.timestamp).total_seconds()
        cursor = m.interval_end
    if cursor != end:
        raise Inconclusive("INSUFFICIENT_TEMPORAL_COVERAGE")
    return {"value": integral/3600, "unit": "mmHg", "coverage_seconds": 3600,
            "method": "EXPLICIT_INTERVAL_MEANS_V1", "input_ids": [m.id for m in ms]}

def trends(ms, alpha, target, allowance, initial=None, decision_limit=None):
    comparable(ms)
    if not 0 < alpha <= 1 or allowance < 0:
        raise ValueError("Invalid statistical configuration")
    ms = sorted(ms,key=lambda m:(m.timestamp,m.id))
    if len(ms)<2 or len({m.timestamp for m in ms}) != len(ms):
        raise Inconclusive("INSUFFICIENT_DISTINCT_TIMES")
    xs=[(m.timestamp-ms[0].timestamp).total_seconds()/86400 for m in ms]
    ys=[convert(m.value,m.unit,ms[0].unit) for m in ms]
    mx,my=sum(xs)/len(xs),sum(ys)/len(ys)
    ss=sum((x-mx)**2 for x in xs)
    slope=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/ss
    stderr=None if len(ms)<3 else sqrt(sum((y-my-slope*(x-mx))**2 for x,y in zip(xs,ys))/(len(ms)-2)/ss)
    ewma, upper, lower, trace=ys[0] if initial is None else initial,0.0,0.0,[]
    for y in ys:
        ewma=alpha*y+(1-alpha)*ewma
        upper=max(0.0,upper+y-target-allowance)
        lower=min(0.0,lower+y-target+allowance)
        trace.append({"ewma":ewma,"cusum_positive":upper,"cusum_negative":lower,
                      "statistical_signal":None if decision_limit is None else upper>=decision_limit or -lower>=decision_limit})
    center=median(ys); mad=median(abs(y-center) for y in ys)
    return {"status":"RESEARCH_ONLY", "slope_per_day":slope,"slope_standard_error":stderr,
            "z_last":None if stdev(ys)==0 else (ys[-1]-my)/stdev(ys),
            "robust_z_last":None if mad==0 else 0.6745*(ys[-1]-center)/mad,
            "cadence_semantics":"PER_OBSERVATION_NOT_TIME_NORMALIZED",
            "ewma_initialization":"FIRST_OBSERVATION" if initial is None else "EXPLICIT_REFERENCE",
            "trace":trace,"diagnosis":None,"input_ids":[m.id for m in ms]}
