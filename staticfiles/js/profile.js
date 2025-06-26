const defaultImage = 'https://english.uccs.edu/sites/default/files/2020-12/placeholder.jpg';

function previewImage(event) {
    const file = event.target.files[0];
    if (file) {
        console.log('File selected:', file.name, file.size);
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('profileImage').src = e.target.result;
        };
        reader.readAsDataURL(file);
        document.getElementById('remove_image').value = 'false';
    } else {
        console.log('No file selected');
    }
}

function removeImage() {
    console.log('Removing image');
    const profileImage = document.getElementById('profileImage');
    const uploadInput = document.getElementById('uploadImage');
    profileImage.src = defaultImage;
    uploadInput.value = '';
    document.getElementById('remove_image').value = 'true';
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('profileForm');
    if (form) {
        form.setAttribute('enctype', 'multipart/form-data');
    }
});