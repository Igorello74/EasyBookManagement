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


function getCookie(name) {
    let matches = document.cookie.match(new RegExp(
        "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
    ));
    return matches ? decodeURIComponent(matches[1]) : undefined;
}

function playClickSound(onended) {
    const a = new Audio("/static/audio/click.mp3");
    a.onended = onended;
    return a.play();
}

function playErrorSound(onended) {
    const a = new Audio("/static/audio/error.mp3");
    a.onended = onended;
    return a.play();
}

function createMessage(messageList, messageClass, messageContent) {
    let message = $(`<li></li>`).html(messageContent).addClass(messageClass).appendTo(messageList);
    window['nav-sidebar'].scrollTop = 1000000000;
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

function findBookInstanceAlike(bookId, booksData) {
    for (let key in booksData) {
        if (booksData[key].book_id == bookId) {
            return key
        }
    }
}

function removeBookFromReader(bookInstanceId, readerId) {
    return $.ajax({
        url: `/readers/${readerId}/books/${bookInstanceId}/`,
        type: 'DELETE',
        beforeSend: function (xhr) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        },
    });
}

function addBookToReader(bookInstanceId, readerId) {
    return $.ajax({
        url: `/readers/${readerId}/books/${bookInstanceId}/`,
        beforeSend: function (xhr) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        },
        type: 'PUT',
    });
}

function addNotesToReader(readerId, notes) {
    return $.ajax({
        url: `/readers/${readerId}/notes/`,
        beforeSend: function (xhr) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        },
        type: 'POST',
        contentType: 'text/plain',
        data: String(notes)
    });
}

function getBookInstanceRepresentation(data) {
    let title = `#${data.id} · ${data.name} — ${data.authors}`
    return `<span  title="${title}">#${data.id} · ${data.name} — <span class="choices__item-authors">${data.authors}</span></span>`
}

function swapBooks(currentBookInstance, bookTaker) {
    if (!confirm(`Удалить эту книгу у ${bookTaker.name} и добавить ему "${currentBookInstance.name}" этого читателя?`)) {
        return;
    }

    today = new Date().toLocaleString("ru-ru");
    const otherBookInstanceId = findBookInstanceAlike(currentBookInstance.book_id, window.initialBooksData);
    const bookBringer = Object.values(window.initialBooksData)[0].taken_by[0]

    if (otherBookInstanceId) {
        removeBookFromReader(currentBookInstance.id, bookTaker.id
        ).done(function () {
            return removeBookFromReader(otherBookInstanceId, bookBringer.id);
        }).done(function () {
            return addBookToReader(otherBookInstanceId, bookTaker.id);
        }).done(function () {
            return addNotesToReader(bookTaker.id, `\n{TKR} Когда проводилась выдача учебников, ${bookTaker.name} получил книгу #${currentBookInstance.id} (${currentBookInstance.name}),` +
                ` однако [${today}] эту книгу принёс ${bookBringer.name} из ${bookBringer.group}.` +
                `\nПо этой причине у текущего читателя (${bookTaker.name}) была удалена книга #${currentBookInstance.id} и добавлена #${otherBookInstanceId} взамен.\n`);
        });

        let $notes = $("#id_notes");
        let new_notes = $notes.val() + `\n\n{BRN} Когда проводилась выдача учебников, ${bookBringer.name} получил книгу #${otherBookInstanceId} (${currentBookInstance.name}),` +
            ` однако [${today}] он принес другую книгу (#${currentBookInstance.id}), которую получал ${bookTaker.name} из ${bookTaker.group}` +
            `\nПо этой причине у текущего читателя (${bookBringer.name}) была удалена книга #${otherBookInstanceId}, которая предположительно находится у ${bookTaker.name}.\n`
        $notes.val(new_notes);

        window.choicesInstance.removeActiveItemsByValue(otherBookInstanceId);
        calculateCounters(false, otherBookInstanceId, window.initialSet);

        createMessage(
            messageList,
            'log-list__item log-list__item--delete',
            `Книга <a class="log-list__book-id" href="#">#${otherBookInstanceId}</a> была удалена, `+
            `потому что предполагается, что она находится у ${bookTaker.name} из ${bookTaker.group}.`
        ).attr("id", `message-${id}`);
    }
    else {
        removeBookFromReader(currentBookInstance.id, bookTaker.id
        ).done(function () {
            addNotesToReader(bookTaker.id, `\n{TKR} Когда проводилась выдача учебников, ${bookTaker.name} получил книгу #${currentBookInstance.id} (${currentBookInstance.name}),` +
                ` однако [${today}] эту книгу принёс ${bookBringer.name} из ${bookBringer.group}.` +
                `\nПо этой причине у текущего читателя (${bookTaker.name}) была удалена книга #${currentBookInstance.id}.\n`);
        });


    }



}

function updateMessageInfo(id, messageELement, choicesInstance, addition = false) {
    getBookInstanceInfo(
        id,
        (data) => {
            data = data[id]
            if (data && !data.error) {
                if (data.status != "active" && addition) {
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
                if (!data.represents_multiple && data.taken_by && addition && !initialSet.has(id)) {
                    const taker = data.taken_by[0];

                    messageELement
                        .html(`<a class="log-list__book-name">#${id} ${data.name}</a> записана на:<br/>
                        <a class="log-list__taker">${taker.name}</a> из ${taker.group}`)
                        .attr({
                            "class": "log-list__item log-list__item--warning",
                        });

                    messageELement.children(".log-list__taker").attr({
                        href: data.taken_by[0].admin_url,
                        target: "_blank",
                        rel: "noopener noreferrer",
                        title: "Узнать подробности"
                    });

                    messageELement.children(".log-list__book-name").attr({
                        href: data.admin_url,
                        target: "_blank",
                        rel: "noopener noreferrer",
                        title: data.name
                    });

                    choicesInstance.removeActiveItemsByValue(id);

                    // Decrease counters
                    calculateCounters(null, null, null, special_decrease = true);
                    playErrorSound();
                    setTimeout(() => swapBooks(data, taker), 500)

                }
                else {
                    playClickSound();
                    messageELement.children("a").attr({
                        href: data.admin_url,
                        target: "_blank",
                        rel: "noopener noreferrer",
                        title: `${data.authors}: ${data.name}`
                    });
                }
                if (addition) {
                    editItemLabel(
                        id,
                        getBookInstanceRepresentation(data),
                        choicesInstance
                    );
                }
            }
            else {
                messageELement
                    .html(`Код <a>#${id}</a> не существует`)
                    .addClass("log-list__item--warning").removeClass("log-list__item--add log-list__item--delete");
                messageELement.children("a").attr({
                    "class": "log-list__book-id log-list__book-id--wrong",
                    href: data.admin_url + "&_popup=1",
                    title: `Создать новый экземпляр с #${id}`
                }).click(() => {
                    window.open(data.admin_url + "&_popup=1",
                        'container',
                        'width=1600,height=700').focus();
                    return false;
                })
                choicesInstance.removeActiveItemsByValue(id);

                // Decrease counters
                calculateCounters(null, null, null, special_decrease = true);
                playErrorSound();
            }
        },
    );
}

function createAdditionMessage(id, messageList, choicesInstance) {
    let messageObj = createMessage(
        messageList,
        'log-list__item log-list__item--add',
        `Книга <a class="log-list__book-id" href="#">#${id}</a> была выдана`
    ).attr("id", `message-${id}`);
    updateMessageInfo(id, messageObj, choicesInstance, true);
}

function createRemovalMessage(id, messageList, choicesInstance) {
    let messageObj = createMessage(
        messageList,
        'log-list__item log-list__item--delete',
        `Книга <a class="log-list__book-id" href="#">#${id}</a> была принята`
    ).attr("id", `message-${id}`);
    updateMessageInfo(id, messageObj, choicesInstance);
    $(`.log-list__item--add#message-${id}`).last().addClass("log-list__item--stricken");
}

function calculateCounters(addition, item, initialSet, special_decrease = false) {
    if (!special_decrease) {
        if (addition) {
            counter_overall.innerText = +counter_overall.innerText + 1;
            if (!initialSet.has(item)) { // if this item wasn't present initially
                counter_added.innerText = +counter_added.innerText + 1;
            }
            else {
                counter_deleted.innerText = +counter_deleted.innerText - 1;
            }
        }
        else {
            counter_overall.innerText = +counter_overall.innerText - 1;
            if (initialSet.has(item)) {
                counter_deleted.innerText = +counter_deleted.innerText + 1;
            }
            else {
                counter_added.innerText = +counter_added.innerText - 1;
            }
        }
    }
    else {
        counter_added.innerText = +counter_added.innerText - 1;
        counter_overall.innerText = +counter_overall.innerText - 1;
    }
}
$(() => {
    var choicesElement = $("#id_books.choicesjs");

    // I need to use defer function, because this very script happens to be
    // defined before choices-js-widget.js, therefore it can't access
    // choices-js-widget's things until the remote script is executed.
    defer(() => typeof (choicesElement[0].choices) != "undefined", () => {
        var choices = choicesElement[0].choices;
        window.choicesInstance = choices;

        // Prevent form submitting on hitting Enter on empty Choices' input
        // (it might happen when one rapidly scans codes)
        $(".choices__input").on("keydown", event => event.key != "Enter");

        let choicesValue = $(".choicesjs")[0].value;
        window.initialSet = new Set();

        if (choicesValue) {
            initialSet = new Set(choicesValue.split(','));
        }

        // Add book counter after all formfields
        let bookCounter = $("<div>")
            .appendTo(".books")
            .addClass("form-row book-counter");

        bookCounter.append("<h1>Счётчики</h1>");

        let iterated = new Map([
            ['added', 'выдано:'],
            ['deleted', 'принято:'],
            ['overall', 'всего на руках:']
        ])

        for (const i of iterated) {
            $("<div>")
                .addClass("book-counter__inner")
                .append(`<label class='book-counter__label'>${i[1]}</label>`)
                .append(`<div class='book-counter__number book-counter__number--${i[0]}'
            id='counter_${i[0]}'>0</div>`)
                .appendTo(bookCounter);
        }

        bookCounter.children().last().addClass("book-counter__inner--overall");

        counter_overall.innerText = initialSet.size;


        // Add autocaps functionality to "profile" field
        id_profile.oninput = function () { this.value = this.value.toUpperCase() }

        // Edit pre-passed items' labels
        getBookInstanceInfo($(".choicesjs")[0].value, data => {
            editAllLabels(function () {
                this.label = getBookInstanceRepresentation(data[this.value])
            }, choices);
            window.initialBooksData = data;
        });

        // I can't call the function immediately, since it takes some time to fetch data
        // Two defered functions are set, because one might be too early
        setTimeout(() => $("#id_books.choicesjs")[0].choices._renderItems(), 200); // TODO: fix this timeout shit somehow
        setTimeout(() => $("#id_books.choicesjs")[0].choices._renderItems(), 5000);

        // Create message-list in DOM
        let messageList = $("<ul></ul>").addClass("log-list");
        window.messageList = messageList;
        $("nav#nav-sidebar").append(messageList);

        // Add event listener responsible for handling both adding and deletion
        choicesElement.on('change', (event) => {
            let item = event.detail.value.trim();
            if (choices.getValue(true).indexOf(item) == -1) {
                createRemovalMessage(item, messageList, choices);
                calculateCounters(false, item, initialSet);
            }
            else {
                if (isTwiceOrMore(choices.getValue(true), item)) {
                    choices.removeActiveItemsByValue(item);
                    createRemovalMessage(item, messageList, choices);
                    calculateCounters(false, item, initialSet);
                }
                else {
                    createAdditionMessage(item, messageList, choices);
                    calculateCounters(true, item, initialSet);
                }
            }
        });
    });
})
