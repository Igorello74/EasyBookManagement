$ = django.jQuery;

function isTwiceOrMore(array, item) {
    ind1 = array.indexOf(item);
    if (ind1 != -1) {
        ind2 = array.indexOf(item, ind1 + 1)

        if (ind2 != -1) { return true; }
    }
    return false;
}

function createMessage(messageList, messageClass, messageContent) {
    let li = $(`<li></li>`).html(messageContent).addClass(messageClass).appendTo(messageList);
    li[0].scrollIntoView();
    return li;
}

function updateMessageInfo(id, messageELement) {
    $.getJSON(`/books/${id}`)
        .done((data) => {
            messageELement.children("a").attr({
                'href': data.admin_url,
                "target": "_blank",
                "rel": "noopener noreferrer",
            })
        })
        .fail(() => {
            messageELement.html(`Некорректный код #${id}`).addClass("warning").removeClass("success error");
            ch.removeActiveItemsByValue(id);
        })
}

function createRemovalMessage(id, messageList) {
    obj = createMessage(messageList, 'error', `Книга <a href="#">#${id}</a> была удалена`);
    updateMessageInfo(id, obj);
}
function createAdditionMessage(id, messageList) {
    obj = createMessage(messageList, 'success', `Книга <a href="#">#${id}</a> была добавлена`);
    updateMessageInfo(id, obj);
}


$(function () {
    let messageList = $("<ul></ul>").addClass("messagelist");
    $("nav#nav-sidebar").append(messageList);

    let choicesElement = $('[choicesjs]');
    const choices = new Choices(choicesElement[0], { position: 'bottom', removeItemButton: true });

    choicesElement.on('addItem', (event) => {
        new_item = event.detail.value;
        if (isTwiceOrMore(choices.getValue(true), new_item)) {
            choices.removeActiveItemsByValue(new_item);
        }
        else {
            createAdditionMessage(new_item, messageList);
        }
    })

    choicesElement.on('change', (event) => {
        item = event.detail.value;
        if (choices.getValue(true).indexOf(item) == -1) {
            createRemovalMessage(item, messageList);
        }
    })

})
