function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) {
        alert('Please select an image file first.');
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("image", file);

    document.getElementById("status").innerText = "Uploading...";

    fetch(" <FUNCTION APP URL>", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())  // Convert response to JSON
    .then(result => {
        document.getElementById("status").innerText = result.message; 
        document.getElementById("caption").innerText = result.caption; 

        // Display tags
        const tags = result.tags.join(", "); 
        document.getElementById("tags").innerText = `${tags}`;    

        // Show image preview
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById("preview").src = e.target.result;
            document.getElementById("preview").style.display = "block";
        };
        reader.readAsDataURL(file);
    })
    .catch(error => {
        document.getElementById("status").innerText = "Upload failed: " + error;
    });
}