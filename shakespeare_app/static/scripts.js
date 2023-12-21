let audioBlobUrl = '';  // Global variable to store audio path

function showElement(elementId) {
    document.getElementById(elementId).style.display = 'block';
}

function hideElement(elementId) {
    document.getElementById(elementId).style.display = 'none';
}

function updateUIWithStory(section, data) {
    if (section == 'storySection') {
        document.getElementById('storySection-Content').value = data.story; 
        showElement('audioSection');
        showElement('audioSection-Button1');
    }
    if (section == 'audioSection') {
        audioBlobUrl = URL.createObjectURL(data);
        const audioElement = document.createElement('audio');
        audioElement.src = audioBlobUrl;
        audioElement.controls = true; 
        document.getElementById('audioSection-Content').value = '';
        document.getElementById('audioSection-Content').appendChild(audioElement);
        showElement('audioSection-Button2');
        showElement('audioSection-Button3');
        showElement('imageSection');
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
    }
    if (section == 'videoSection') {
        const videoSectionContent = document.getElementById('videoSection-Content');
        videoSectionContent.innerHTML = ''; // Clear existing content
        if (data.video_path) {
            const videoElement = document.createElement('video');
            videoElement.src = data.video_path;
            videoElement.controls = true;
            videoSectionContent.appendChild(videoElement);
            showElement('videoSection');
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('storyForm').addEventListener('submit', function(e) {
        e.preventDefault();
        showElement('loadingSpinner');
        hideElement('generateStoryButton');
        var storyPrompt = document.getElementById('storyPrompt').value;
        
        // Show a loading message or spinner
        document.getElementById('storySection').style.display = 'block';
        document.getElementById('storySection-Content').value = 'Generating Story...';

        fetch('/generateStory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt: storyPrompt }),
        })
        .then(response => response.json())
        .then(data => {
            updateUIWithStory('storySection',data)
            hideElement('loadingSpinner');
            showElement('generateStoryButton');
        })
        .catch(error => {
            console.error('Error:', error.message)
            hideElement('loadingSpinner');
        });
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
            updateUIWithStory('audioSection',blob)
        })

    });

    // Adding Download functionality
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
            updateUIWithStory('imageSection',data)
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
        fetch('/generateVideo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ imagefiles: imagePaths, voicefile: voiceoverPath })
        })
        .then(response => response.json())
        .then(data => {
            updateUIWithStory('videoSection',data)
            hideElement('loadingSpinner');
        })
        .catch(error => {
            document.getElementById('errorDisplay').textContent = 'Unable to generate video due to an error.';
            console.error('Error:', error);
        });
    });
});
