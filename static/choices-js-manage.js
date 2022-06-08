document.addEventListener('DOMContentLoaded', function() {
    var instances = document.querySelectorAll('[choicesjs]');
    for (i = 0; i < instances.length; ++i) {
        var element = instances[i];
        new Choices(element, {position: 'bottom', removeItemButton: true});
    }
})