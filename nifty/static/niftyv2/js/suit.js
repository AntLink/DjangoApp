// Fungsi untuk menangani event DOMContentLoaded
document.addEventListener("DOMContentLoaded", function () {
    // Checkbox select all functionality
    const selectAllCheckbox = document.querySelector(".checkbox-select > #select-all");
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener("click", function () {
            const magicCheckboxes = document.querySelectorAll(".magic-checkbox");

            if (this.hasAttribute("checked")) {
                this.removeAttribute("checked");
                magicCheckboxes.forEach(checkbox => {
                    checkbox.removeAttribute("checked");
                });
            } else {
                magicCheckboxes.forEach(checkbox => {
                    checkbox.setAttribute("checked", "checked");
                });
                this.setAttribute("checked", "checked");
            }
        });
    }

    // Fixed submit buttons
    suit_fixed();

    // Show link to related item after Select
    suit_linked_select();

    // Handle change list filter null values
    suit_search_filters();
});

// Fixed submit buttons
function suit_fixed() {
    const fixedItems = document.querySelectorAll('.inner-right-column');

    fixedItems.forEach(function (fixedItem) {
        const pos = fixedItem.getBoundingClientRect();
        const extra_offset = 70;

        const scrollHandler = function () {
            const scroll_top = window.pageYOffset || document.documentElement.scrollTop;

            if (fixedItem.offsetHeight < window.innerHeight &&
                scroll_top > (pos.top - 10) &&
                fixedItem.offsetHeight < window.innerHeight) {

                if (!fixedItem.classList.contains('fixed')) {
                    fixedItem.classList.add('fixed');
                }

                const max_top = Math.min(10, document.documentElement.scrollHeight -
                    fixedItem.offsetHeight - scroll_top - extra_offset);
                fixedItem.style.top = max_top + 'px';
            } else if (scroll_top <= (pos.top - 10) &&
                fixedItem.classList.contains('fixed')) {
                fixedItem.classList.remove('fixed');
            }
        };

        window.addEventListener('scroll', scrollHandler);
        window.addEventListener('resize', scrollHandler);
        window.addEventListener('load', scrollHandler);

        // Trigger once to set initial state
        scrollHandler();
    });
}

// Search filters - submit only changed fields
function suit_search_filters() {
    const filters = document.querySelectorAll('.search-filter');

    filters.forEach(function (filter) {
        const changeHandler = function () {
            const option = filter.options[filter.selectedIndex];
            const select_name = option.dataset.name;

            if (select_name) {
                filter.setAttribute('name', select_name);
            } else {
                filter.removeAttribute('name');
            }

            // Handle additional values for date filters
            const additional = option.dataset.additional;
            if (additional) {
                const hidden_id = filter.dataset.name + '_add';
                let hidden = document.getElementById(hidden_id);

                if (!hidden) {
                    hidden = document.createElement('input');
                    hidden.type = 'hidden';
                    hidden.id = hidden_id;
                    filter.parentNode.insertBefore(hidden, filter.nextSibling);
                }

                const additionalParts = additional.split('=');
                hidden.setAttribute('name', additionalParts[0]);
                hidden.value = additionalParts[1];
            }
        };

        filter.addEventListener('change', changeHandler);
        changeHandler(); // Trigger change initially
    });
}

// Linked select - shows link to related item after Select
function suit_linked_select() {
    const get_link_name = function (select) {
        const option = select.options[select.selectedIndex];
        return option && select.value ? option.text + '' : '';
    };

    const get_url = function (add_link, select) {
        const value = select.value;
        return add_link.href.split('?')[0] + '../' + value + '/';
    };

    const add_link = function (select) {
        const add_link = select.nextElementSibling;

        if (add_link && add_link.classList.contains('add-another')) {
            let link = add_link.nextElementSibling;

            // Check if the next sibling is the link we need
            if (!link || !link.matches('a.linked-select-link')) {
                link = document.createElement('a');
                link.className = 'linked-select-link';
                add_link.parentNode.insertBefore(link, add_link.nextSibling);
                add_link.parentNode.insertBefore(document.createTextNode(' \u00A0 '), link);
            }

            link.textContent = get_link_name(select);
            link.href = get_url(add_link, select);
        }
    };

    const linkedSelects = document.querySelectorAll('.linked-select');

    linkedSelects.forEach(function (select) {
        add_link(select);

        select.addEventListener('change', function () {
            add_link(select);
        });
    });
}

// Content tabs
function suit_form_tabs() {
    const tabs = document.querySelector('.form-tabs');
    if (!tabs) return;

    const tab_prefix = tabs.dataset.tabPrefix;
    if (!tab_prefix) return;

    const tab_links = tabs.querySelectorAll('a');

    function tab_contents(link) {
        const href = link.getAttribute('href').replace('#', '');
        return document.querySelector('.' + tab_prefix + '-' + href);
    }

    function activate_tabs() {
        // Init tab by error, by url hash or init first tab
        if (window.location.hash) {
            let found_error = false;

            tab_links.forEach(function (link) {
                const content = tab_contents(link);
                if (content && content.querySelector('.error')) {
                    link.classList.add('error');
                    link.click();
                    found_error = true;
                }
            });

            if (!found_error) {
                const hash_link = tabs.querySelector('a[href="' + window.location.hash + '"]');
                if (hash_link) hash_link.click();
            }
        } else {
            if (tab_links.length > 0) tab_links[0].click();
        }
    }

    tab_links.forEach(function (link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();

            const parent_li = link.parentNode;
            const active_links = parent_li.parentNode.querySelectorAll('.active');

            active_links.forEach(function (active) {
                active.classList.remove('active');
            });

            parent_li.classList.add('active');

            const tabContents = document.querySelectorAll('.' + tab_prefix);
            tabContents.forEach(function (content) {
                content.classList.remove('show');
                content.classList.add('hide');
            });

            const content = tab_contents(link);
            if (content) {
                content.classList.remove('hide');
                content.classList.add('show');
            }
        });
    });

    activate_tabs();
}

// Avoids double-submit issues in the change_form.
function suit_form_debounce() {
    const form = document.querySelector('form');
    if (!form) return;

    const saveButtons = form.querySelectorAll('.submit-row button');
    let submitting = false;

    form.addEventListener('submit', function (e) {
        if (submitting) {
            e.preventDefault();
            return false;
        }

        submitting = true;

        saveButtons.forEach(function (button) {
            button.classList.add('disabled');
        });

        setTimeout(function () {
            saveButtons.forEach(function (button) {
                button.classList.remove('disabled');
            });
            submitting = false;
        }, 5000);
    });
}


// Inisialisasi setelah dokumen dimuat
document.addEventListener('DOMContentLoaded', function () {
    // Fixed submit buttons
    suit_fixed();

    // Show link to related item after Select
    suit_linked_select();

    // Handle change list filter null values
    suit_search_filters();
});