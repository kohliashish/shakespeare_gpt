from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from moviepy.video.fx.all import fadein, fadeout
from pathlib import Path
from PIL import Image
import numpy as np

def generate_video(image_paths, audio_path, clip_duration=5, transition_duration=1, output_file='output_video.mp4'):
    clips = []
    final_duration = 0

    for img_path in image_paths:
        img_path_str = str(img_path)
        if Path(img_path_str).exists():
            img = Image.open(img_path_str)
            img_np = np.array(img)
            clip = ImageClip(img_np).set_duration(clip_duration + transition_duration)
            clip = fadein(clip, transition_duration).fadeout(transition_duration)
            clip = clip.set_start(final_duration)
            final_duration += clip_duration
            clips.append(clip)

    # Create a composite video clip
    video = CompositeVideoClip(clips, size=clips[0].size)

    # Load audio
    audio = AudioFileClip(str(audio_path))
    video = video.set_audio(audio).set_duration(audio.duration)

    # Write the result to a file
    video_file_path = Path(__file__).parent / f"resources/{output_file}"
    video.write_videofile(str(video_file_path), fps=24, audio_codec="aac")

    return video_file_path