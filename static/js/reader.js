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

function editAllLabels(editCallback, choicesInstance) {
    let items = choicesInstance._currentState.items;
    items = $.grep(items, x => x.active);
    $.each(items, editCallback);
}

function getBookInstanceInfo(id, done, fail) {
    $.getJSON(`/books/bookInstance/${id}`)
        .done(done)
        .fail(fail);
}

function getBookInstanceRepresentation(data) {
    return `<span class="choices__item-id">#${data.id}</span> · ${data.authors}: ${data.name}`
}

function updateMessageInfo(id, messageELement, choicesInstance, addition = false) {
    getBookInstanceInfo(
        id,
        (data) => {
            if (data.status != "in storage" && addition) {
                messageELement
                    .html(`Некорректный статус книги <a>#${id}</a>`)
                    .attr({
                        "class": "log-list__item log-list__item--warning",
                        title: `Возможно книга уже взята, списана или истёк срок возврата.`
                    });

                messageELement.children("a").attr({
                    "class": "log-list__book-id log-list__book-id--wrong",
                    href: data.admin_url,
                    target: "_blank",
                    rel: "noopener noreferrer",
                    title: "Узнать  подробности"
                })
            }

            messageELement.children("a").attr({
                href: data.admin_url,
                target: "_blank",
                rel: "noopener noreferrer",
                title: `${data.authors}: ${data.name}`
            });
            if (addition) {
                editItemLabel(
                    id,
                    getBookInstanceRepresentation(data),
                    choicesInstance
                );
            }
        },
        (jqxhr) => {
            messageELement
                .html(`Код <a>#${id}</a> не существует`)
                .addClass("log-list__item--warning").removeClass("log-list__item--add log-list__item--delete");
            messageELement.children("a").attr({
                "class": "log-list__book-id log-list__book-id--wrong",
                href: jqxhr.responseJSON.admin_url,
                target: "_blank",
                rel: "noopener noreferrer",
                title: `Создать новый экземпляр с #${id}`
            })
            choicesInstance.removeActiveItemsByValue(id);
        }
    );
}

function createAdditionMessage(id, messageList, choicesInstance) {
    let messageObj = createMessage(
        messageList,
        'log-list__item log-list__item--add',
        `Книга <a class="log-list__book-id" href="#">#${id}</a> была добавлена`
    ).attr("id", `message-${id}`);
    updateMessageInfo(id, messageObj, choicesInstance, true);
}

function createRemovalMessage(id, messageList, choicesInstance) {
    let messageObj = createMessage(
        messageList,
        'log-list__item log-list__item--delete',
        `Книга <a class="log-list__book-id" href="#">#${id}</a> была удалена`
    ).attr("id", `message-${id}`);
    updateMessageInfo(id, messageObj, choicesInstance);
    $(`.log-list__item--add#message-${id}`).last().addClass("log-list__item--stricken");
}


$(() => {
    var choicesElement = $("#id_books.choicesjs");

    // I need to use defer function, because this very script happens to be
    // defined before choices-js-widget.js, therefore it can't access
    // choices-js-widget's thinhs until the remote script is executed.
    defer(() => typeof (choicesElement[0].choices) != "undefined", () => {
        var choices = choicesElement[0].choices;

        // Prevent form submitting on hitting Enter on empty Choices' input
        // (it might happen when one rapidly scans codes)
        $(".choices__input").on("keydown", event => event.key != "Enter");

        let initialSet = new Set($(".choicesjs")[0].value.split(','));

        // Add book counter after all formfields
        let bookCounter = $("<div>")
            .insertAfter(".form-row:last-child")
            .addClass("form-row book-counter");
        
        bookCounter.append("<h1>Счётчики</h1>")

        let iterated = new Map([
            ['added', 'выдано:'],
            ['deleted', 'принято:'],
            ['overall', 'итого на руках:']
        ])

        for (const i of iterated) {
            $("<div>")
            .addClass("book-counter__inner")
            .append(`<label class='book-counter__label'>${i[1]}</label>`)
            .append(`<div class='book-counter__number book-counter__number--${i[0]}'
            id='counter_${i[0]}'>0</div>`)
            .appendTo(bookCounter);
        }


        // Edit pre-passed items' labels
        editAllLabels(function () {
            getBookInstanceInfo(this.value, data => {
                this.label = getBookInstanceRepresentation(data);
            })
        }, choices);

        // I can't call the function immediately, since it takes some time to fetch data
        // Two defered functions are set, because one might be too early
        setTimeout(() => $("#id_books.choicesjs")[0].choices._renderItems(), 200);
        setTimeout(() => $("#id_books.choicesjs")[0].choices._renderItems(), 5000);

        // Create message-list in DOM
        let messageList = $("<ul></ul>").addClass("log-list");
        $("nav#nav-sidebar").append(messageList);

        // Add event listener responsible for handling both adding and deletion
        choicesElement.on('change', (event) => {
            let item = event.detail.value;
            if (choices.getValue(true).indexOf(item) == -1) {
                createRemovalMessage(item, messageList, choices);
            }
            else {
                if (isTwiceOrMore(choices.getValue(true), item)) {
                    choices.removeActiveItemsByValue(item);
                    createRemovalMessage(item, messageList, choices);
                }
                else {
                    createAdditionMessage(item, messageList, choices);
                }
            }
        });
    });
})