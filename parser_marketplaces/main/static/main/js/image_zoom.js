Document.addEventListener('DOMContentLoaded', function () {
    var zoomModal = document.getElementById('imageZoomModal');
    var zoomedImage = document.getElementById('zoomedImage');
    if (!zoomModal || !zoomedImage) return;
    document.querySelectorAll('img.zoomable').forEach(function (img) {
        img.style.cursor = 'zoom-in';
        img.addEventListener('click', function () {
            zoomedImage.src = this.src;
            var modal = new bootstrap.Modal(zoomModal);
            modal.show();
        });
    });
});