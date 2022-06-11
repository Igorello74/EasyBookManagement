if (typeof ($) == "undefined") var $ = django.jQuery;

function defer(conditon, when_succeed, timeout = 50) {
    if (conditon()) {
        when_succeed();
    }
    else {
        setTimeout(() => defer(conditon, when_succeed, timeout), timeout);
    }
}

function isTwiceOrMore(array, item) {
    let ind1 = array.indexOf(item);
    if (ind1 != -1) {
        let ind2 = array.indexOf(item, ind1 + 1)

        if (ind2 != -1) return true;
    }
    return false;
}

function createMessage(messageList, messageClass, messageContent) {
    let message = $(`<li></li>`).html(messageContent).addClass(messageClass).appendTo(messageList);
    message[0].scrollIntoView();
    return message;
}

function editItemLabel(editedItem, newLabel, choicesInstance) {
    let items = choicesInstance._currentState.items;

    items = $.grep(items, x => x.value == editedItem && x.active);
    if (items.length) {
        items[0].label = newLabel;
        choicesInstance._renderItems();
    }
}

function updateMessageInfo(id, messageELement, choicesInstance, editItem = false) {
    $.getJSON(`/books/${id}`)
        .done((data) => {
            messageELement.children("a").attr({
                'href': data.admin_url,
                "target": "_blank",
                "rel": "noopener noreferrer",
            });
            if (editItem) {
                editItemLabel(
                    id,
                    `<span class="choices__item-id">#${id}</span> · ${data.authors}: ${data.name}`,
                    choicesInstance
                );
            }
        })
        .fail(() => {
            messageELement
                .html(`Некорректный код <span class="messagelist__book-id messagelist__book-id--wrong">#${id}</span>`)
                .addClass("warning").removeClass("success error");
            choicesInstance.removeActiveItemsByValue(id);
        })
}

function createAdditionMessage(id, messageList, choicesInstance) {
    let messageObj = createMessage(
        messageList,
        'success',
        `Книга <a class="messagelist__book-id" href="#">#${id}</a> была добавлена`
    );
    updateMessageInfo(id, messageObj, choicesInstance, true);
}

function createRemovalMessage(id, messageList, choicesInstance) {
    let messageObj = createMessage(
        messageList,
        'error',
        `Книга <a class="messagelist__book-id" href="#">#${id}</a> была удалена`
    );
    updateMessageInfo(id, messageObj, choicesInstance);
}


$(() => {
    var choicesElement = $("#id_books.choicesjs");
    
    // I need to use defer function, because this very script happens to be
    // defined before choices-js-widget.js, therefore it can't access
    // choices-js-widget's thinhs until the remote script is executed.
    defer(() => typeof (choicesElement[0].choices) != "undefined", () => {
        var choices = choicesElement[0].choices;
        let messageList = $("<ul></ul>").addClass("messagelist");
        $("nav#nav-sidebar").append(messageList);


        choicesElement.on('addItem', (event) => {
            let new_item = event.detail.value;
            if (isTwiceOrMore(choices.getValue(true), new_item)) {
                choices.removeActiveItemsByValue(new_item);
            }
            else {
                createAdditionMessage(new_item, messageList, choices);
            }
        })

        choicesElement.on('change', (event) => {
            let item = event.detail.value;
            if (choices.getValue(true).indexOf(item) == -1) {
                createRemovalMessage(item, messageList, choices);
            }
        })
    });

})