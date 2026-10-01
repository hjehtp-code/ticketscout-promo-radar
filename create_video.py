"""Author a narrated diagram video. Authoring-only dependencies, not site runtime."""
import subprocess
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
from create_diagrams import SLIDES

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'media'/'LL-01'
NARRATION = '''Before buying a LEGOLAND ticket, match the resort, the included attractions, and your visit date. Florida and California are different destinations. For the Florida ticket reviewed on October first, twenty twenty six, the official page includes SEA LIFE with theme park admission and lists a separate Water Park option. A visible promotion can still be expired. An old buy one get one terms block ends its visit window on August sixteenth, twenty twenty six. It does not prove a current deal. The overview and detailed pages also show different November promotion deadlines, so confirm your exact product with LEGOLAND. Finally, compare the same party and day. Add admission, required fees, parking you need, and chosen extras. An unknown fee is not zero. Read the source-linked TicketScout guide for the worksheet. Ticket terms can change.'''

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'narration.txt').write_text(NARRATION,encoding='utf-8')
    fonts = Path('C:/Windows/Fonts')
    def font(size, bold=False):
        return ImageFont.truetype(str(fonts/('arialbd.ttf' if bold else 'arial.ttf')),size)
    for i, (_, title, rows, note) in enumerate(SLIDES):
        im = Image.new('RGB',(1200,675),'#edf5f2'); d = ImageDraw.Draw(im)
        d.text((70,50),'TICKETSCOUT · TICKET CHECK',font=font(22),fill='#12634d')
        d.text((70,115),title,font=font(42,True),fill='#183c39')
        for j,(label,value) in enumerate(rows):
            y=205+j*105
            d.rounded_rectangle((70,y,1130,y+85),radius=16,fill='white')
            d.text((95,y+22),label,font=font(21,True),fill='#12634d')
            d.text((295,y+28),value,font=font(26),fill='#203d43')
        d.text((70,580),note,font=font(24),fill='#203d43')
        d.text((70,638),'Florida official sources reviewed October 1, 2026 · Terms may change',font=font(17),fill='#47645e')
        im.save(OUT/f'slide-{i+1}.png')
    speech_script=OUT/'narrate.ps1'
    speech_script.write_text("Add-Type -AssemblyName System.Speech\n$ticketNarrator = New-Object System.Speech.Synthesis.SpeechSynthesizer\n$ticketNarrator.SelectVoice('Microsoft Zira Desktop')\n$ticketNarrator.Rate = 0\n$ticketNarrator.SetOutputToWaveFile((Join-Path $PSScriptRoot 'narration.wav'))\n$ticketNarrator.Speak((Get-Content (Join-Path $PSScriptRoot 'narration.txt') -Raw))\n$ticketNarrator.Dispose()\n",encoding='utf-8')
    speech_commands = speech_script.read_text(encoding='utf-8').replace('$PSScriptRoot', "'" + str(OUT).replace("'", "''") + "'")
    subprocess.run(['powershell','-NoProfile','-Command',speech_commands],check=True)
    with wave.open(str(OUT/'narration.wav')) as wav:
        seconds=wav.getnframes()/wav.getframerate()
    duration=seconds/3
    playlist=OUT/'slides.txt'
    playlist.write_text(''.join(f"file 'slide-{i}.png'\nduration {duration:.3f}\n" for i in range(1,4))+"file 'slide-3.png'\n",encoding='utf-8')
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-f','concat','-safe','0','-i',str(playlist),'-i',str(OUT/'narration.wav'),'-vf','fps=25,pad=1200:676:0:0','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(OUT/'legoland-ticket-check.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    print(f'Created narrated video: {seconds:.1f} seconds; '+str(OUT/'legoland-ticket-check.mp4'))

if __name__ == '__main__':
    main()
