
document.getElementById('choose').onchange = function() {
  var previewBox = document.getElementById("choose");
  previewBox.src = URL.createObjectURL(event.target.files[0]);
  this.form.submit();
};
