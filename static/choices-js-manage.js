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
    obj = sendMessage(messageList, 'error', `Книга <a href="#">#${bookInstance}</a> была удалена`);
    getBookInstanceInfo(bookInstance, obj);
}
function sendAdditionMessage(messageList, bookInstance) {
    obj = sendMessage(messageList, 'success', `Книга <a href="#">#${bookInstance}</a> была добавлена`);
    getBookInstanceInfo(bookInstance, obj);
}


$(function () {
    let messageList = $("<ul></ul>").addClass("messagelist");
    $("nav#nav-sidebar").append(messageList);

    let element = $('[choicesjs]');
    const ch = new Choices(element[0], { position: 'bottom', removeItemButton: true });

    element.on('addItem', (event) => {
        new_item = event.detail.value;
        if (isTwiceOrMore(ch.getValue(true), new_item)) {
            ch.removeActiveItemsByValue(new_item);
        }
        else {
            sendAdditionMessage(messageList, new_item);
        }
    })

    element.on('change', (event) => {
        item = event.detail.value;
        if (ch.getValue(true).indexOf(item) == -1) {
            sendRemovalMessage(messageList, item);
        }
    })

})
