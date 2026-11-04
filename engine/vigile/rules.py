"""Explicit, non-eval interpreters of the original 15 rules. Simulation only.

This pure layer consumes validated inputs. Public service resolves provenance, units,
quality, scope and simulation eligibility before entering it. No free-form DSL execution.
"""
from decimal import Decimal
from math import isfinite
from .quality import Inconclusive

def number(value):
    if isinstance(value,bool) or not isinstance(value,(float,int)) or not isfinite(value) or value<0:
        raise Inconclusive('INVALID_NUMERIC_INPUT')
    return Decimal(str(value))

def result(state,reason='',derived=None):
    return {'result':state,'reason':reason,'derived':derived or {},'diagnosis':None,
            'clinical_severity':None,'status':'RESEARCH_ONLY','authorization':'ASSESSMENT_SIMULATION_ONLY'}

def verdict(ok,derived=None):
    return result('REQUIREMENT_MET' if ok else 'REQUIREMENT_NOT_MET',derived=derived)

def calculate(rule, inputs, context):
    """Reject unresolved contexts; retain exact inclusivity from original JSON."""
    x=inputs; rid=rule['rule_id']; t=rule['thresholds']; app=rule['applicability']
    try:
        if 'mission_phase' in app:
            if not context.get('mission_phase'):
                raise Inconclusive('MISSING_MISSION_PHASE')
            if context['mission_phase'] not in app['mission_phase']:
                return result('NOT_APPLICABLE','MISSION_PHASE')
        if rid in ('VIGILE-AER-001','VIGILE-AER-002'):
            flag=next(iter(app['required_context']))
            if x.get(flag) is False:
                return result('NOT_APPLICABLE','EVA_CONTEXT')
            if x.get(flag) is not True:
                raise Inconclusive('MISSING_EVA_CONTEXT')
        if rid=='VIGILE-ENV-003' and x.get('exposure_context')=='LIMITED_SPECIAL_OPERATION':
            return result('NOT_APPLICABLE','SPECIAL_OPERATION')
        if rid.startswith('VIGILE-ENV-'):
            if context.get('environment') not in ('HABITABLE_CABIN','HABITABLE_VOLUME'):
                return result('NOT_APPLICABLE','ENVIRONMENT') if context.get('environment') else result('INCONCLUSIVE','MISSING_ENVIRONMENT')
        if rid=='VIGILE-ENV-002' and context.get('mode')!='NOMINAL':
            return result('NOT_APPLICABLE','OFF_NOMINAL') if context.get('mode') else result('INCONCLUSIVE','MISSING_OPERATING_MODE')
        if rid=='VIGILE-RAD-002' and context.get('radiation_context')!='DESIGN_REFERENCE_SOLAR_PARTICLE_EVENT':
            raise Inconclusive('DESIGN_CONTEXT_REQUIRED')
        if rid=='VIGILE-RAD-003' and context.get('nuclear_technology_emitting_ionizing_radiation_present') is not True:
            raise Inconclusive('NUCLEAR_CONTEXT_REQUIRED')
        if rid=='VIGILE-RAD-004':
            if number(x.get('crew_support_duration_days'))<=60:
                return result('NOT_APPLICABLE','SUPPORT_DURATION')
            if context.get('beyond_low_earth_orbit') is not True:
                raise Inconclusive('BEYOND_LEO_CONTEXT_REQUIRED')
        if rid=='VIGILE-ENV-004' and number(x.get('absolute_total_pressure_change'))<=number(t['trigger_total_pressure_change']['value']):
            return result('NOT_APPLICABLE','PRESSURE_CHANGE_TRIGGER')
        for field in rule['inputs']:
            name=field['name']; value=x.get(name)
            if field.get('required') and value is None:
                raise Inconclusive('MISSING_BASELINE' if 'baseline' in name or name.startswith('premission') else 'MISSING_REQUIRED_INPUT:'+name)
            if value is not None:
                typ=field['type']
                if typ=='number': number(value)
                if typ=='boolean' and type(value) is not bool: raise Inconclusive('INVALID_BOOLEAN:'+name)
                if typ=='string' and (not isinstance(value,str) or not value): raise Inconclusive('INVALID_STRING:'+name)
                if 'values' in field and value not in field['values']: raise Inconclusive('INVALID_ENUM:'+name)
        if 'data_quality_status' in x and x['data_quality_status']!='ACCEPTABLE':
            raise Inconclusive('UNACCEPTABLE_QUALITY')
        if 'measurement_comparability' in x and x['measurement_comparability']!='COMPARABLE':
            raise Inconclusive('NOT_COMPARABLE')
        if rid in ('VIGILE-AER-001','VIGILE-AER-002'):
            return verdict(number(x['vo2max_relative'])>=number(t['vo2max_relative_minimum']['value']))
        if rid in ('VIGILE-AER-003','VIGILE-MUS-002'):
            b,c=('premission_aerobic_capacity','current_aerobic_capacity') if 'AER' in rid else ('baseline_strength','current_strength')
            base=number(x[b])
            if base<=0: raise Inconclusive('INVALID_BASELINE')
            retention=100*number(x[c])/base
            threshold=t['retention_percent_minimum']
            if isinstance(threshold,dict): threshold=threshold['value']
            return verdict(retention>=number(threshold),{'retention_percent':float(retention)})
        if rid=='VIGILE-MUS-001':
            if x['approved_strength_test_protocol'] is not True:
                return result('REQUIRES_MISSION_AUTHORIZATION','STRENGTH_PROTOCOL')
            profiles=x['applicable_mission_profiles']
            if not isinstance(profiles,list) or not profiles or any(p not in t for p in profiles):
                raise Inconclusive('UNKNOWN_MISSION_PROFILE')
            weight=number(x['body_weight'])
            if weight<=0: raise Inconclusive('INVALID_BODY_WEIGHT')
            ratios={'deadlift_body_weight_ratio':number(x['deadlift_strength_value'])/weight,
                    'bench_press_body_weight_ratio':number(x['bench_press_strength_value'])/weight}
            return verdict(all(ratios[k]>=number(t[p][k]) for p in profiles for k in ratios),{k:float(v) for k,v in ratios.items()})
        if rid=='VIGILE-BONE-001':
            sites={}
            for site,threshold in t.items():
                base=x['premission_bmd'].get(site); current=x['current_bmd'].get(site)
                if base is None or current is None or number(base)<=0:
                    sites[site]={'result':'INCONCLUSIVE'}
                else:
                    retention=100*number(current)/number(base)
                    sites[site]={'retention_percent':float(retention),'result':'REQUIREMENT_MET' if retention>=number(threshold['minimum_retention_percent']) else 'REQUIREMENT_NOT_MET'}
            if any(v['result']=='INCONCLUSIVE' for v in sites.values()):
                return result('INCONCLUSIVE','MISSING_REQUIRED_SITE',{'site_results':sites})
            return verdict(all(v['result']=='REQUIREMENT_MET' for v in sites.values()),{'site_results':sites})
        if rid=='VIGILE-NUT-001':
            if x['requirement_calculation_method_approved'] is not True:
                return result('REQUIRES_MISSION_AUTHORIZATION','NUTRITION_METHOD')
            req=x['calculated_requirements']; provided=x['provided_amounts']
            if not req or any(k not in provided or number(v)<=0 for k,v in req.items()):
                raise Inconclusive('MISSING_REQUIRED_COMPONENT')
            ratios={k:100*number(provided[k])/number(v) for k,v in req.items()}
            return verdict(all(v>=number(t['minimum_provision_percent']) for v in ratios.values()),{k:float(v) for k,v in ratios.items()})
        if rid=='VIGILE-RAD-001':
            if x['dose_methodology']!='NASA_APPROVED': raise Inconclusive('DOSIMETRY_METHOD')
            dose=number(x['past_spaceflight_effective_dose'])
            if x['evaluation_mode']=='MISSION_PLANNING': dose+=number(x.get('projected_upcoming_mission_effective_dose'))
            return verdict(dose<number(t['career_effective_dose']['value']),{'evaluated_career_effective_dose':float(dose)})
        if rid=='VIGILE-RAD-002':
            if x['reference_environment_verified'] is not True: raise Inconclusive('UNVERIFIED_REFERENCE_ENVIRONMENT')
            return verdict(number(x['modeled_design_reference_spe_effective_dose'])<number(t['effective_dose']['value']))
        if rid=='VIGILE-RAD-003':
            years=number(x['mission_year_equivalent'])
            if years<=0: raise Inconclusive('INVALID_MISSION_YEAR')
            limit=number(t['annualized_effective_dose']['value'])*years
            return verdict(number(x['nuclear_technology_effective_dose'])<limit,{'prorated_limit_mSv':float(limit)})
        if rid=='VIGILE-RAD-004':
            if x['design_verification_model_approved'] is not True: raise Inconclusive('UNAPPROVED_MODEL')
            return verdict(number(x['nasa_effective_gcr_dose_rate'])<number(t[x['environment']]['value']))
        if rid=='VIGILE-ENV-001':
            if x['diluent_type']!='NITROGEN' or x['balance_oxygen_assumption_valid'] is not True:
                return result('REQUIRES_MISSION_AUTHORIZATION','ALTERNATE_ATMOSPHERE')
            if number(x['diluent_fraction_percent'])>100: raise Inconclusive('INVALID_FRACTION')
            return verdict(number(x['diluent_fraction_percent'])>=number(t['minimum_diluent_fraction']['value']))
        if rid=='VIGILE-ENV-002':
            if x['window_coverage_complete'] is not True or x['aggregation_method_validated'] is not True:
                raise Inconclusive('INSUFFICIENT_TEMPORAL_COVERAGE')
            return verdict(number(x['one_hour_average_ppco2'])<=number(t['maximum_one_hour_average_ppco2']['value']))
        if rid=='VIGILE-ENV-003':
            return verdict(number(t['lower_bound']['value'])<number(x['total_pressure'])<=number(t['upper_bound']['value']))
        if rid=='VIGILE-ENV-004':
            if x['rate_calculation_method_validated'] is not True: raise Inconclusive('UNVALIDATED_RATE_METHOD')
            return verdict(number(x['maximum_absolute_pressure_change_rate'])<=number(t['maximum_rate']['value']))
        return result('REQUIRES_VALIDATION','UNIMPLEMENTED_RULE')
    except (Inconclusive,KeyError,TypeError,AttributeError) as exc:
        return result('INCONCLUSIVE',str(exc))
