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

function editItemLabel(editedItem, newLabel, choicesInstance) {
    let items = choicesInstance._currentState.items;

    items = $.grep(items, (x) => { return x.value == editedItem && x.active });
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
    obj = createMessage(
        messageList,
        'success',
        `Книга <a class="messagelist__book-id" href="#">#${id}</a> была добавлена`
    );
    updateMessageInfo(id, obj, choicesInstance, true);
}

function createRemovalMessage(id, messageList, choicesInstance) {
    obj = createMessage(
        messageList,
        'error',
        `Книга <a class="messagelist__book-id" href="#">#${id}</a> была удалена`
        );
    updateMessageInfo(id, obj, choicesInstance);
}



$(function () {
    let messageList = $("<ul></ul>").addClass("messagelist");
    $("nav#nav-sidebar").append(messageList);

    let choicesElement = $('[choicesjs]');
    choices = new Choices(choicesElement[0], { position: 'bottom', removeItemButton: true });

    choicesElement.on('addItem', (event) => {
        new_item = event.detail.value;
        if (isTwiceOrMore(choices.getValue(true), new_item)) {
            choices.removeActiveItemsByValue(new_item);
        }
        else {
            createAdditionMessage(new_item, messageList, choices);
        }
    })

    choicesElement.on('change', (event) => {
        item = event.detail.value;
        if (choices.getValue(true).indexOf(item) == -1) {
            createRemovalMessage(item, messageList, choices);
        }
    })

})
