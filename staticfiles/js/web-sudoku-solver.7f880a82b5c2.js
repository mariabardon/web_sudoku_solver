
document.getElementById('choose').onchange = function() {
  var previewBox = document.getElementById("preview");
  previewBox.src = URL.createObjectURL(event.target.files[0]);
  //this.form.submit();
};
