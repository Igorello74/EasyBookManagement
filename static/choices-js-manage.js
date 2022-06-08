function isTwiceOrMore(array, item) {
    ind1 = array.indexOf(item);
    if (ind1 != -1) {
        ind2 = array.indexOf(item, ind1+1)

        if (ind2 != -1) {return true;}
    }
    return false;
}

document.addEventListener('DOMContentLoaded', function () {
    var instances = document.querySelectorAll('[choicesjs]');
    for (i = 0; i < instances.length; ++i) {
        var element = instances[i];
        const ch = new Choices(element, { position: 'bottom', removeItemButton: true });
        
        element.addEventListener(
            'addItem',
            (event)=>{
                new_item = event.detail.value;
                if (isTwiceOrMore(ch.getValue(true), new_item)) {
                    ch.removeActiveItemsByValue(new_item);
                }
            }
        )
    }
})
