import numpy as np, subprocess, sys, os

def load_wav(path):
    out = path.rsplit('.',1)[0] + '_48k.wav'
    subprocess.run(['ffmpeg','-y','-v','error','-i',path,'-ar','48000','-ac','1',out],check=True)
    import wave
    w = wave.open(out,'rb')
    n = w.getnframes(); sr = w.getframerate()
    raw = w.readframes(n); w.close()
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32)/32768.0, sr, out

def trim(path):
    x, sr, wavpath = load_wav(path)
    win = int(0.1*sr)
    nw = len(x)//win
    rms = np.array([np.sqrt(np.mean(x[i*win:(i+1)*win]**2)) for i in range(nw)])
    # high-freq ratio: energy above 6kHz vs total
    hfr = np.zeros(nw)
    for i in range(nw):
        seg = x[i*win:(i+1)*win]
        if len(seg) < win: continue
        sp = np.abs(np.fft.rfft(seg*np.hanning(len(seg))))
        fr = np.fft.rfftfreq(len(seg), 1/sr)
        tot = sp.sum()+1e-9
        hfr[i] = sp[fr>6000].sum()/tot
    # last sustained real speech: rms>-40dB in 3+ consecutive windows AND hfr<0.9
    db = 20*np.log10(rms+1e-9)
    good = (db > -40) & (hfr < 0.9)
    last = -1
    for i in range(nw-3, -1, -1):
        if good[i] and good[i+1] and good[i+2]:
            last = i+2; break
    if last < 0:
        print(f"{path}: no speech found, keeping all"); return wavpath, len(x)/sr
    cut = min(len(x), int((last+1)*win + 0.25*sr))
    trimmed = x[:cut]
    import wave
    outp = path.rsplit('.',1)[0] + '_trim.wav'
    w = wave.open(outp,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(trimmed,-1,1)*32767).astype(np.int16).tobytes()); w.close()
    # verify no 0.5s+ HF-dominated region remains
    tw = len(trimmed)//win
    trms = np.array([np.sqrt(np.mean(trimmed[i*win:(i+1)*win]**2)) for i in range(tw)])
    tdb = 20*np.log10(trms+1e-9)
    run = 0
    for i in range(tw):
        seg = trimmed[i*win:(i+1)*win]
        sp = np.abs(np.fft.rfft(seg*np.hanning(len(seg)))); fr = np.fft.rfftfreq(len(seg),1/sr)
        hr = sp[fr>6000].sum()/(sp.sum()+1e-9)
        if tdb[i] > -40 and hr >= 0.9: run += 1
        else: run = 0
        if run >= 5:
            print(f"{path}: WARNING 0.5s+ HF region remains"); break
    print(f"{path}: {len(x)/sr:.2f}s -> {len(trimmed)/sr:.2f}s")
    return outp, len(trimmed)/sr

for f in sys.argv[1:]:
    trim(f)
