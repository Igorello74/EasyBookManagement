function isTwiceOrMore(array, item) {
    ind1 = array.indexOf(item);
    if (ind1 != -1) {
        ind2 = array.indexOf(item, ind1+1)

        if (ind2 != -1) {return true;}
    }
    return false;
}

function sendMessage(messageList, messageClass, messageContent) {
    let li = document.createElement('li');
    li.className = messageClass;
    li.innerHTML = messageContent;
    messageList.append(li);
}

function sendRemovalMessage(messageList, bookInstance) {
    sendMessage(messageList, 'error', `Книга с кодом ${bookInstance} была принята у читателя`);
}
function sendAdditionMessage(messageList, bookInstance) {
    sendMessage(messageList, 'success', `Книга с кодом ${bookInstance} была выдана читателю`);
}


document.addEventListener('DOMContentLoaded', function () {
    messageList = document.createElement("ul");
    messageList.className = "messagelist";
    let content = document.querySelector("div.content");
    content.prepend(messageList);


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
                else {
                    sendAdditionMessage(messageList, new_item);
                }
            }
        )

        element.addEventListener(
            'change',
            (event) => {
                item = event.detail.value;
                if (ch.getValue(true).indexOf(item) == -1) {
                    sendRemovalMessage(messageList, item);
                }
            }
        )
    }
})
