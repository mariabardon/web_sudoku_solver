
document.getElementById('choose').onchange = function() {
  preview.src = URL.createObjectURL(event.target.files[0]);
  this.form.submit();
};
