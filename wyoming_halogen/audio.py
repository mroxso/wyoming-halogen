import io
import wave

def validate(rate, width, channels):
    if not 8000 <= rate <= 192000 or width not in (1,2,3,4) or channels not in (1,2):
        raise ValueError('Unsupported PCM format')

def wav_bytes(data, fmt):
    out = io.BytesIO()
    with wave.open(out,'wb') as w:
        w.setframerate(fmt[0]); w.setsampwidth(fmt[1]); w.setnchannels(fmt[2]); w.writeframes(data)
    return out.getvalue()
