from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips, VideoFileClip
from moviepy.video.fx.all import fadein, fadeout
# from moviepy.video.io import VideoFileClip
from pathlib import Path
from PIL import Image
from numpy import array
from json import loads, dumps
from re import sub
from random import choice
from subprocess import run

def select_background_music(story_genre_tags):
    audio_tags_path = Path(__file__).parent / "resources/audio_tags.json"
    audio_tags = loads(open(audio_tags_path, "r").read())
    matched_audio_files = []
    default_audio_file = 'upbeat1.mp3'
    if isinstance(story_genre_tags, list):
        story_genre_tags = [item.strip() for item in story_genre_tags]
    elif isinstance(story_genre_tags, str):
        story_genre_tags = story_genre_tags.strip().split(",")
    else:
        return Path(__file__).parent / f"resources/audio_files/{default_audio_file}"

    for audio_file, tags in audio_tags.items():
        overlap = len(set(story_genre_tags) & set(tags))
        if overlap > 0:
            matched_audio_files.append(audio_file)

    if matched_audio_files:
        return Path(__file__).parent / f"resources/audio_files/{choice(matched_audio_files)}"
    else:
        return Path(__file__).parent / f"resources/audio_files/{default_audio_file}"

def adjust_volume(input_audio_path, output_audio_path, volume):
    try:
        cmd = [
            "ffmpeg",
            "-y", "-i", input_audio_path,
            "-af", f"volume={volume}",
            output_audio_path
        ]
        run(cmd, check=True)
    except Exception as e:
        print(f"Error in adjusting volume: {e}")

def adjust_speed(input_audio_path, output_audio_path, target_duration):
    try:
        original_audio = AudioFileClip(input_audio_path)
        original_duration = original_audio.duration
        speed_factor = float(original_duration) / float(target_duration)
        cmd = [
            "ffmpeg",
            "-y", "-i", input_audio_path,
            "-filter:a", f"atempo={speed_factor}",
            "-vn", output_audio_path
        ]
        run(cmd, check=True)
    except Exception as e:
        print(f"Error in adjusting speed: {e}")
        raise

def generate_video(image_paths, audio_path, metadata, transition_duration=1, background_volume = 0.5):
    clips = []
    max_duration = 55 # Leaving 2 seconds for Intro and 2 seconds for Outro
    final_duration = 0
    output_video_file=sub('[\W_]+', '', metadata['title'])+'.mp4'
    output_metadata_file=sub('[\W_]+', '', metadata['title'])+'.json'
    clip_duration = max_duration/len(image_paths)
    bg_audio_path = select_background_music(metadata['genre'])

    for img_path in image_paths:
        img_path_str = str(img_path)
        if Path(img_path_str).exists():
            img = Image.open(img_path_str)
            img_np = array(img)
            clip = ImageClip(img_np).set_duration(clip_duration + transition_duration)
            clip = fadein(clip, transition_duration).fadeout(transition_duration)
            clip = clip.set_start(final_duration)
            final_duration += clip_duration
            clips.append(clip)

    # Create a composite video clip
    video = CompositeVideoClip(clips, size=clips[0].size)

    # Load voiceover
    audio_voiceover = AudioFileClip(str(audio_path))
    #Speed up voice over if it is longer than max duration
    if audio_voiceover.duration > max_duration:
        adjusted_voiceover_path = Path(__file__).parent / "resources/inprocess/speech_adjusted.mp3"
        try:
            adjust_speed(str(audio_path), str(adjusted_voiceover_path), max_duration)
        except Exception as e:
            print(f"Error in adjusting speed: {e}")
            return None
        finally:
            audio_voiceover = AudioFileClip(str(adjusted_voiceover_path))
            print (f"[INFO] Voiceover duration: {audio_voiceover.duration}")
    # audio_voiceover = audio_voiceover.subclip(0,max_duration)
    # Load background music
    bg_audio_reduced_volume_path = Path(__file__).parent / "resources/inprocess/bgAudio.mp3"
    adjust_volume(bg_audio_path,bg_audio_reduced_volume_path,background_volume) #Reducing volume using ffmpeg
    audio_bg = AudioFileClip(str(bg_audio_reduced_volume_path))
    # Combining both audio files
    combined_audio = CompositeAudioClip([audio_voiceover,audio_bg])
    # Trimming the final audio if it is longer than 58 seconds
    if combined_audio.duration > max_duration:
        combined_audio = combined_audio.subclip(0,max_duration)
    
    print("Writing processed audio to disk...")
    final_audio_path = Path(__file__).parent / "resources/inprocess/speech_final.mp3"
    combined_audio.write_audiofile(str(final_audio_path), fps=44100)

    # Extend the duration of last image based on voice over length if required 
    if final_duration < combined_audio.duration:
        last_clip_duration = combined_audio.duration - sum(clip.duration for clip in clips[:-1])
        clips[-1] = clips[-1].set_duration(last_clip_duration)
        video = concatenate_videoclips(clips, method = "compose")
        final_duration += last_clip_duration
    video = video.set_audio(combined_audio)

    #Append Intro and Outro
    outro_path = Path(__file__).parent / "resources/outro.mp4"
    intro_path = Path(__file__).parent / "resources/intro.mp4"
    outro_clip = VideoFileClip(str(outro_path)).subclip(0,2)
    intro_clip = VideoFileClip(str(intro_path))
    #Second check, just because...
    if final_duration > max_duration:
        video = video.subclip(0, max_duration)
        final_duration = video.duration
    
    final_video = concatenate_videoclips([intro_clip, video,outro_clip], method = "compose")
    final_duration = final_duration + (intro_clip.duration) + (outro_clip.duration)
    # Final final check..!!
    if final_video.duration > (max_duration + (intro_clip.duration) + (outro_clip.duration)):
        final_video = final_video.subclip(0,max_duration + (intro_clip.duration) + (outro_clip.duration))

    # Crop video to YouTube Shorts size
    # Calculate the center coordinates of the video
    center_x = final_video.w / 2
    center_y = final_video.h / 2

    # Calculate the top-left coordinates of the crop box
    crop_x = center_x - 576 / 2
    crop_y = center_y - 1024 / 2

    #Cropping
    final_video = final_video.crop(x1=crop_x, y1=crop_y, width=576, height=1024)

    #Logging
    print(f"[INFO] Final video duration: {final_video.duration}")
    print(f"[INFO] Creating a video file with following background audio: {bg_audio_path} with following volume: {background_volume}")

    # Write the result to a file
    video_file_path = Path(__file__).parent / f"resources/inprocess/{output_video_file}"
    final_video.write_videofile(str(video_file_path), temp_audiofile="temp-audio.m4a", remove_temp=True, codec="libx264", audio_codec="aac", fps=24)
    # Write metadata along with the file
    md_file_path = Path(__file__).parent / f"resources/inprocess/{output_metadata_file}"
    metadata = dumps(metadata, indent=4)
    with open(str(md_file_path), 'w') as f:
        f.write(metadata)
    return video_file_path