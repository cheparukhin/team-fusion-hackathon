"""Record observed GPU utilization for the owned pilot until it completes."""
import pathlib,subprocess,sys,time
root=pathlib.Path(sys.argv[1]);deadline=time.monotonic()+3600
with (root/'logs/gpu_utilization.csv').open('w') as out:
    out.write('timestamp,name,utilization_gpu_percent,memory_used_mib,power_draw_w\n');out.flush()
    while time.monotonic()<deadline:
        r=subprocess.run(['nvidia-smi','--query-gpu=timestamp,name,utilization.gpu,memory.used,power.draw','--format=csv,noheader,nounits'],text=True,capture_output=True)
        if r.returncode==0:out.write(r.stdout);out.flush()
        if (root/'logs/completed_utc.txt').exists():break
        time.sleep(1)
