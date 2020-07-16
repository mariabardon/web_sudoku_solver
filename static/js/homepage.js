
$('h1').click(function(){
});

document.getElementById('fileName').onchange = function() {
  this.form.submit();
  console.log('hahaha')
   var imageElement = document.getElementById("sudoku_image");
  // $(imageElement).css('transform', 'rotate(90deg)')
  EXIF.getData(imageElement, function() {
  //     console.log('hahaha')
      var orientation = EXIF.getTag(this, "Orientation");
      console.log(EXIF.getTag(this, "Orientation") || 1);
  //     if(orientation == 6)
  //     $(imageElement).css('transform', 'rotate(90deg)')
   });
};

var imageElement = document.getElementById("sudoku_image");
$(imageElement).css('transform', 'rotate(90deg)')
