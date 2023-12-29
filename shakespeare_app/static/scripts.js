let audioBlobUrl = '';  // Global variable to store audio path
let story = ''; // Global variable to store the generated story
let videoUrl = '' // Global variable to store final video path
let metadata = '' // Global variable to store final metadata

function showElement(elementId) {
    document.getElementById(elementId).style.display = 'block';
}

function hideElement(elementId) {
    document.getElementById(elementId).style.display = 'none';
}

function toTitleCase(str) {
    return str.replace(
        /\w\S*/g,
        function(txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        }
    );
}

function updateUIWithStory(section, data) {
    if (section == 'storySection') {
        story = data.story;
        document.getElementById('storySection-Content').value = data.story; 
        showElement('audioSection');
        showElement('audioSection-Button1');
    }
    if (section == 'audioSection') {
        const audioSectionContent = document.getElementById('audioSection-Content');
        audioSectionContent.innerHTML = '';
        audioBlobUrl = URL.createObjectURL(data);
        const audioElement = document.createElement('audio');
        audioElement.src = audioBlobUrl;
        audioElement.controls = true; 
        audioSectionContent.appendChild(audioElement);
        showElement('audioSection-Button2');
        showElement('audioSection-Button3');
        hideElement('audioSection-Button1');
        showElement('imageSection');
        hideElement('imageSection-Button');
    }
    if (section == 'imageSection') {
        const imageSectionContent = document.getElementById('imageSection-Content');
        imageSectionContent.innerHTML = ''; // Clear existing content
        data.image_paths.forEach(imagePath => {
            const img = document.createElement('img');
            img.src = imagePath;
            img.classList.add('story-image'); // Add a class for styling
            imageSectionContent.appendChild(img);
        });
        showElement('imageSection-Button');
    }
    if (section == 'videoSection') {
        const videoSectionContent = document.getElementById('videoSection-Content');
        videoSectionContent.innerHTML = ''; // Clear existing content
        if (data.video_path) {
            videoUrl = data.video_path
            const videoElement = document.createElement('video');
            videoElement.src = videoUrl;
            videoElement.controls = true;
            videoElement.autoplay = true;
            videoElement.loop = true;
            videoSectionContent.appendChild(videoElement);
            showElement('videoSection');
        }
        showElement('imageSection-Button');
        // Renaming the button's text
        document.getElementById('imageSection-Button').innerText = "Re-generate video"
    }
    if (section == 'infoDisplay') {
        const metadataSection = document.getElementById('metadataSection');
        console.log(metadata);
        metadataSection.innerHTML = '';
        if (data.metadata) {
            metadata = data.metadata
            for(const key in metadata) {
                const div = document.createElement('div');
                div.innerHTML = `<strong>${toTitleCase(key)}</strong>: ${metadata[key]}`;
                metadataSection.appendChild(div);
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('storyForm').addEventListener('submit', function(e) {
        e.preventDefault();
        showElement('loadingSpinner');
        hideElement('generateStoryButton');
        var storyPrompt = document.getElementById('storyPrompt').value;
        var context = document.getElementById('promptSection').value;
        // const context = 'You are an intelligent story-writer. You create a short story STRICTLY IN 150 WORDS OR LESS from the user content, that contains character development, an interesting plot and  climax. You ensure that the generated story does not use any generic phrases and that it provides a detailed description of scenes.'
        // Show a loading message or spinner
        document.getElementById('storySection').style.display = 'block';
        document.getElementById('storySection-Content').value = 'Generating Story...';

        fetch('/generateStory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt: storyPrompt, context: context }),
        })
        .then(response => response.json())
        .then(data => {
            updateUIWithStory('storySection',data);
            showElement('generateStoryButton');
            // Create Metadata file for the story
            fetch('/generateMetadata', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({story: story}),
            })
            .then(response => response.json())
            .then(data => {
                // console.log(data);
                updateUIWithStory('infoDisplay',data);
            })
            .catch(error => {
                console.error('Error:', error.message)
                hideElement('loadingSpinner');
            });
            hideElement('loadingSpinner');
        })
        .catch(error => {
            console.error('Error:', error.message)
            hideElement('loadingSpinner');
        });
    });

    // Slider controls
    document.getElementById('bgMusicVolume').addEventListener('input', function() {
        document.getElementById('volumeValue').textContent = this.value;
    });

    // Generating Voice Over
    document.getElementById('audioSection-Button1').addEventListener('click', function(e) {
        e.preventDefault();
        showElement('loadingSpinner');
        var story = document.getElementById('storySection-Content').value;
        document.getElementById('audioSection-Content').value = 'Generating Voice Over...';

        fetch('/generateVoiceOver', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: story }),
        })
        .then(response => {
            if(!response.ok) {
                throw new Error("Error: Network response was not ok");
            }
            return response.blob();
        })
        .then(blob => {
            hideElement('loadingSpinner');
            updateUIWithStory('audioSection',blob);
        })

    });

    // Adding Download functionality for audio
    document.getElementById('audioSection-Button2').addEventListener('click', function() {
        const a = document.createElement('a');
        a.href = audioBlobUrl;
        a.download = 'voiceover.mp3';
        a.click();
    });
    
    // Generating images
    document.getElementById('audioSection-Button3').addEventListener('click', function() {
        showElement('loadingSpinner');
        var story = document.getElementById('storySection-Content').value;
        fetch('/generateFrames', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: story})
        })
        .then(response => response.json())
        .then(data => {
            updateUIWithStory('imageSection',data);
            hideElement('loadingSpinner');
        })
        .catch(error => {
            document.getElementById('errorDisplay').textContent = 'Unable to generate image due to content restrictions.';
            console.error('Error:', error)
        });
    });

    //Generating video
    document.getElementById('imageSection-Button').addEventListener('click', function() {
        showElement('loadingSpinner');
        const imagePaths = Array.from(document.querySelectorAll('#imageSection-Content img')).map(img => img.src);
        const voiceoverPath = audioBlobUrl;
        const bgMusicVol = document.getElementById('bgMusicVolume').value;
        hideElement('imageSection-Button');
        fetch('/generateVideo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ imagefiles: imagePaths, voicefile: voiceoverPath, metadata: metadata, background_volume: bgMusicVol })
        })
        .then(response => response.json())
        .then(data => {
            updateUIWithStory('videoSection',data);
            hideElement('loadingSpinner');
        })
        .catch(error => {
            document.getElementById('errorDisplay').textContent = 'Unable to generate video due to an error.';
            console.error('Error:', error);
        });
    });

    // Adding Download functionality for video
    document.getElementById('videoSection-Button').addEventListener('click', function() {
        const a = document.createElement('a');
        const filename = videoUrl.substring(videoUrl.lastIndexOf('/')+1)
        a.href = videoUrl;
        a.download = filename;
        a.click();
    });
});
