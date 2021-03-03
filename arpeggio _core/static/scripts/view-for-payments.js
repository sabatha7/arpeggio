$(document).ready(function() {
/** works for activating the maintenace break modal **/
$("#exampleModal").modal('show');

/** works for checking and unchecking some progress pointers **/
$('input[type=checkbox]').change(function() {
if (this.checked) {
$(this).next(".input-group-append").css("text-decoration-line", "line-through");
} else {
$(this).next(".input-group-append").css("text-decoration-line", "none");
}
});
});