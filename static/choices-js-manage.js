function isTwiceOrMore(array, item) {
    ind1 = array.indexOf(item);
    if (ind1 != -1) {
        ind2 = array.indexOf(item, ind1 + 1)

        if (ind2 != -1) { return true; }
    }
    return false;
}

function sendMessage(messageList, messageClass, messageContent) {
    let li = document.createElement('li');
    li.className = messageClass;
    li.innerHTML = messageContent;
    messageList.append(li);
    li.scrollIntoView();
}

function sendRemovalMessage(messageList, bookInstance) {
    sendMessage(messageList, 'error', `Книга #${bookInstance} была удалена`);
}
function sendAdditionMessage(messageList, bookInstance) {
    sendMessage(messageList, 'success', `Книга #${bookInstance} была добавлена`);
}


document.addEventListener('DOMContentLoaded', function () {
    messageList = document.createElement("ul");
    messageList.className = "messagelist";
    let outer = document.querySelector("nav#nav-sidebar");
    outer.append(messageList);


    var element = document.querySelector('[choicesjs]');
    const ch = new Choices(element, { position: 'bottom', removeItemButton: true });

    element.addEventListener(
        'addItem',
        (event) => {
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

})
