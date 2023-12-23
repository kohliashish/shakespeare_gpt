from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, VideoFileClip
from moviepy.video.fx.all import fadein, fadeout
# from moviepy.video.io import VideoFileClip
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
    # Extend the duration of last image if required
    if final_duration < audio.duration:
        last_clip_duration = audio.duration - sum(clip.duration for clip in clips[:-1])
        clips[-1] = clips[-1].set_duration(last_clip_duration)
        video = concatenate_videoclips(clips, method = "compose")
        final_duration += last_clip_duration
    video = video.set_audio(audio).set_duration(audio.duration)

    #Append Suffix
    suffix_path = Path(__file__).parent / "resources/suffix.mp4"
    suffix_clip = VideoFileClip(str(suffix_path))
    if final_duration > 59:
        video = video.subclip(0, 59)
    
    final_video = concatenate_videoclips([video,suffix_clip], method = "compose")

    # Crop video to YouTube Shorts size
    # Calculate the center coordinates of the video
    center_x = final_video.w / 2
    center_y = final_video.h / 2

    # Calculate the top-left coordinates of the crop box
    crop_x = center_x - 576 / 2
    crop_y = center_y - 1024 / 2

    #Cropping
    final_video = final_video.crop(x1=crop_x, y1=crop_y, width=576, height=1024)

    # Write the result to a file
    video_file_path = Path(__file__).parent / f"resources/{output_file}"
    final_video.write_videofile(str(video_file_path), fps=24, audio_codec="aac")

    return video_file_path