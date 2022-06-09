$ = django.jQuery;

function isTwiceOrMore(array, item) {
    ind1 = array.indexOf(item);
    if (ind1 != -1) {
        ind2 = array.indexOf(item, ind1 + 1)

        if (ind2 != -1) { return true; }
    }
    return false;
}

function sendMessage(messageList, messageClass, messageContent) {
    let li = $(`<li></li>`)
        .html(messageContent)
        .addClass(messageClass)
        .appendTo(messageList);
    li[0].scrollIntoView();
    return li;
}

function getBookInstanceInfo(bookInstance, messageELement) {
    $.getJSON(`/books/${bookInstance}`)
        .done((data) => {
            messageELement.children("a").attr({
                'href': data.admin_url,
                "target": "_blank",
                "rel": "noopener noreferrer",
            })
        })
        .fail(() => {
            messageELement.html(`Некорректный код ${bookInstance}`).addClass("warning").removeClass("success error")
        })
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
