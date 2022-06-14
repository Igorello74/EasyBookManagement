if (typeof ($) == "undefined") var $ = django.jQuery;

$(function () {
    let choicesElements = $('.choicesjs');

    choicesElements.each(function () {
        this.choices = new Choices(this, { position: 'bottom', removeItemButton: true });
    });
})
