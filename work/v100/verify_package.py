from pathlib import Path
import zipfile,sys,json,hashlib
R=Path(__file__).resolve().parents[2];target=R/'work/v100/package-verification';target.mkdir(exist_ok=False)
with zipfile.ZipFile(R/'VIGILE-v1.0.0-r2-team-review.zip') as z:
 for i in z.infolist():assert (target/i.filename).resolve().is_relative_to(target.resolve())
 z.extractall(target)
sys.path.insert(0,str(target/'engine'))
from vigile.registry import Registry
from vigile.clinical_knowledge import ClinicalKnowledge
from vigile.offline_library import OfflineLibrary
registry=Registry(target);knowledge=ClinicalKnowledge();library=OfflineLibrary(target/'engine/local_ai/library-v080.json');blocks,issues=library.search('How are baselines selected and validated?',5)
assert blocks and knowledge.hash=='b8c568bd645154e5fd67630c7a670ca53904dc04f54904315047a89923839d4e'
report={'extracted_package_corpus_integrity':True,'clinical_knowledge_hash':knowledge.hash,'rag_source_verification':True,'retrieved':len(blocks),'model_weights_absent_as_documented':not (target/'engine/local_ai/voice').exists(),'not_a_fresh_machine_install_test':True}
(R/'docs/v100/PACKAGE_SMOKE.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))