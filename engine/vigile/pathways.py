"""Documentary stage coverage is distinct from software support and clinical validation."""
STAGES=('prevention','monitoring','data_quality','detection','assessment','differential_diagnosis',
        'triage','intervention_authorized','recovery','follow_up','prognosis')
def pathway_record(registry, condition_id):
    c=registry.get('conditions',condition_id)
    rules=[r['rule_id'] for r in registry.rule_status() if condition_id in r.get('condition_ids',[])]
    generic={'monitoring':'NUMERIC_ACQUISITION_INFRASTRUCTURE','data_quality':'CONFIGURED_TECHNICAL_GATES',
             'assessment':'HUMAN_RECORDING','recovery':'HUMAN_WORKFLOW_RECORDING','follow_up':'PLAN_DUE_STATUS_AND_REVIEWS'}
    stages=[]
    for stage in STAGES:
        computational=generic.get(stage,'STRUCTURE_ONLY')
        if stage=='detection': computational='NORMATIVE_SIMULATION' if rules else 'NO_CONDITION_SPECIFIC_DETECTOR'
        stages.append({'stage':stage,'documentary_state':c['coverage_states'][stage],
            'software_support':computational,'clinical_validation':'NOT_VALIDATED',
            'clinical_execution':'BLOCKED','source_ids':c['source_ids']})
    return {'condition_id':condition_id,'name':c['catalog_record']['name_specialty'],
            'profile_as_published':c['clinical_pathway_profile_as_published'],
            'rule_ids':rules,'stages':stages,'no_prescription':True}

INTERACTION_SOURCES={'MSI01':['S10'],'MSI02':['S09','S10'],'MSI03':['S05','S02'],
 'MSI04':['S06','S08'],'MSI05':['S04'],'MSI06':['S02'], 'MSI07':['S13'],
 'MSI08':['S07'],'MSI09':['S03','S36'],'MSI10':['S15'],'MSI11':['S11'],'MSI12':['S37']}
