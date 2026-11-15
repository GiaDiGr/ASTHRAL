// Arbitrary app-fixture values only; not astronaut data, targets, recommendations or a radiation model.
export const PREVENTION_FIXTURES=Object.freeze([
 Object.freeze({entry_type:'EXERCISE_SESSION',occurred_at:'2026-11-05T17:30:00Z',label:'Synthetic aerobic session',workout_type:'AEROBIC',duration_minutes:24,perceived_exertion_0_10:4,note:'Arbitrary software fixture; not a recommendation.'}),
 Object.freeze({entry_type:'HYDRATION',occurred_at:'2026-11-05T18:00:00Z',label:'Synthetic fluid entry',amount_ml:300}),
 Object.freeze({entry_type:'MEAL_NOTE',occurred_at:'2026-11-05T18:15:00Z',label:'Synthetic meal note',note:'Fixture only; no composition supplied.'}),
 Object.freeze({entry_type:'SLEEP',occurred_at:'2026-11-05T06:00:00Z',label:'Synthetic sleep diary',duration_minutes:405,subjective_quality_1_5:3}),
 Object.freeze({entry_type:'WELLBEING',occurred_at:'2026-11-05T18:20:00Z',label:'Synthetic voluntary check-in',mood_rating_1_5:4,stress_rating_1_5:2})
]);
export const RADIATION_FIXTURES=Object.freeze([[0,1,'habitat'],[30,12,'EVA'],[60,2,'habitat']].map(Object.freeze));
