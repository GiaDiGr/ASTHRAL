"""Explicit scoped read projections for the local dashboard; no clinical mutations."""
from fastapi import Request

def install_dashboard_routes(app,engine):
    @app.get('/dashboard/identity')
    def identity(request:Request): return {'role':request.state.principal.role,'id':request.state.principal.id}
    @app.get('/dashboard/subjects')
    def subjects(request:Request):
        p=request.state.principal
        return [r for r in engine.store.all('profile') if p.allows(r['id'],r['mission_id'])]

    @app.get('/dashboard/subjects/{subject_id}')
    def dashboard(subject_id:str,mission_id:str):
        profile=engine.store.get('profile',subject_id)
        if profile['mission_id']!=mission_id: raise ValueError('SCOPE_MISMATCH')
        def scoped(kind): return [r for r in engine.store.all(kind) if (r.get('subject_id'),r.get('mission_id'))==(subject_id,mission_id)]
        records=scoped('clinical_evaluation')
        evaluations=[]
        for r in records:
            public=app.state.clinical.projection(r)
            request=r['snapshot']['request']
            public['as_of']=request['as_of'];public['condition_id']=request['condition_id'];public['presentation_id']=request['presentation_id']
            # Deliberate authorized dashboard projection, not arbitrary snapshot access.
            public['observations']=[{k:o[k] for k in ('id','concept','value','unit','timestamp','quality','method','provenance')} for o in r['snapshot']['observations']]
            evaluations.append(public)
        measurements=[r for r in engine.store.all('measurement') if (r['measurement']['subject_id'],r['measurement']['mission_id'])==(subject_id,mission_id)]
        episodes=[engine.episode(r['id']) for r in scoped('episode')]
        episode_ids={r['id'] for r in scoped('episode')}
        followups=[r for r in engine.store.all('followup') if r.get('episode_id') in episode_ids]
        return {'episodes':episodes,'followups':followups,'profile':profile,'mission':engine.store.get('mission',mission_id),'measurements':measurements[-1000:],
         'baselines':scoped('baseline'),'trends':scoped('trend'),'findings':scoped('finding')[-100:],
         'monitoring':[app.state.monitoring.projection(r) for r in scoped('monitoring_run')][-50:],'evaluations':evaluations[-100:],'limits':{'measurements':1000,'evaluations':100},'clinical_execution':'BLOCKED'}
