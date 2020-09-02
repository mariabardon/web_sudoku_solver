
document.getElementById('choose').onchange = function() {
  this.form.submit();
};

// // https://www.askingbox.com/tutorial/how-to-resize-image-before-upload-in-browser
// function fileChange(e) {
//    document.getElementById('choose').value = '';
//
//    var file = e.target.files[0];
//
//    if (file.type == "image/jpeg" || file.type == "image/png") {
//
//       var reader = new FileReader();
//       reader.onload = function(readerEvent) {
//
//          var image = new Image();
//          image.onload = function(imageEvent) {
//             var max_size = 10;
//             var w = image.width;
//             var h = image.height;
//
//             if (w > h) {  if (w > max_size) { h*=max_size/w; w=max_size; }
//             } else     {  if (h > max_size) { w*=max_size/h; h=max_size; } }
//
//             var canvas = document.createElement('canvas');
//             canvas.width = w;
//             canvas.height = h;
//             canvas.getContext('2d').drawImage(image, 0, 0, w, h);
//
//             if (file.type == "image/jpeg") {
//                var dataURL = canvas.toDataURL("image/jpeg", 1.0);
//             } else {
//                var dataURL = canvas.toDataURL("image/png");
//             }
//             document.getElementById('choose').value = dataURL;
//          }
//          image.src = readerEvent.target.result;
//       }
//       reader.readAsDataURL(file);
//    } else {
//       document.getElementById('choose').value = '';
//       alert('Please only select images in JPG- or PNG-format.');
//    }
// }
//
// document.getElementById('choose').addEventListener('change', fileChange, false);
