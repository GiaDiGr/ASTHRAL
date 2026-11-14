from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'.gitignore';s=p.read_text(encoding='utf8');s+='\n!/.gitattributes\n';p.write_text(s,encoding='utf8')
(R/'.gitattributes').write_text('# Preserve byte-level evidence and implementation hashes across checkouts.\n* -text\n',encoding='utf8')
print('Git checkout will preserve evidence bytes and hashes')