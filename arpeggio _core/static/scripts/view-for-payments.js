$(document).ready(function() {
$('input[type=checkbox]').change(function() {

if (this.checked) {
	
$(this).next(".input-group-append").css("text-decoration-line", "line-through");
} else {
$(this).next(".input-group-append").css("text-decoration-line", "none");
}

});
});