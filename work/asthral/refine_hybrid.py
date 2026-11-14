from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'engine/vigile/hybrid_retrieval.py';s=p.read_text(encoding='utf8').replace("except (ValueError,KeyError,TypeError,AttributeError):break","except (ValueError,KeyError,TypeError,AttributeError):\n     docs=None;break");p.write_text(s,encoding='utf8')
p=R/'engine/vigile/english.py';s=p.read_text(encoding='utf8').replace("result['assistant_identity']='ASTHRAL'", "if 'inference_trace' in result:result['inference_trace']['explanation_accepted']=bool(result.get('generated'))\n result['assistant_identity']='ASTHRAL'");p.write_text(s,encoding='utf8')
p=R/'engine/tests/test_asthral_hybrid.py';s=p.read_text(encoding='utf8').replace("with TestClient(create_portal(config,reader,NoModel()),base_url=", "model=NoModel();model.mode='FULL'\n  with TestClient(create_portal(config,reader,model),base_url=")
s=s.replace("assert '<html lang=\"en\">' in html and 'ASTHRAL' in html and 'Astronaut Support Tool for Health Risk Assessment and Logistics' in html.upper().title() if False else '<html lang=\"en\">' in html", "assert '<html lang=\"en\">' in html and 'ASTHRAL' in html and 'ASTRONAUT SUPPORT TOOL FOR HEALTH RISK ASSESSMENT AND LOGISTICS' in html")
p.write_text(s,encoding='utf8')
print('Malformed metadata now returns unavailable; corrected explicit FULL test setup')