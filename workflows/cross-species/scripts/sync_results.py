"""Continuously export irreplaceable results from this task's capped runtime."""
import pathlib,subprocess,time,json
R=pathlib.Path(__file__).resolve().parents[1]
end=json.loads((R/'qc/spending_manifest.json').read_text())['deadline_epoch']
while time.time()<end:
 with (R/'logs/export.log').open('a') as log:
  p=subprocess.run(['rsync','-az','--timeout=120','--exclude=scripts/','--exclude=tests/','--exclude=PLAN.md','--exclude=STATUS.md','--exclude=qc/spending_manifest.json','--exclude=software/mamba/','--exclude=software/env/','--exclude=software/bin/','--include=*evidence.bam','--exclude=*.sam','--exclude=*.bam','--exclude=*.bai','--exclude=*.part','--exclude=raw/','--exclude=reference/','--exclude=references/','-e','ssh -T','chrna-cross-species-20260920:/home/ubuntu/cross-species/',str(R)+'/'],stdout=log,stderr=log)
 with (R/'logs/export.log').open('a') as log:
  subprocess.run(['rsync','-az','--timeout=120','--include=*/','--include=*.json','--include=*names.tsv','--exclude=*','-e','ssh -T','chrna-cross-species-20260920:/home/ubuntu/cross-species/reference/',str(R/'reference')+'/'],stdout=log,stderr=log)
  subprocess.run(['rsync','-az','--timeout=120','--include=*/','--include=*.json','--include=read_id_map.tsv.gz','--exclude=*','-e','ssh -T','chrna-cross-species-20260920:/home/ubuntu/cross-species/raw/',str(R/'raw')+'/'],stdout=log,stderr=log)
 time.sleep(60)
