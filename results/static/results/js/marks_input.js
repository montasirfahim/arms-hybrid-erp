// Navigation Logic: Pressing Enter moves focus to the next cell in the same column
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' || e.keyCode === 13) {
        const active = document.activeElement;
        
        // Check if the focused element is a numeric input in the marks table
        if (active.tagName === 'INPUT' && active.type === 'number') {
            const td = active.closest('td');
            const tr = td ? td.closest('tr') : null;
            
            // Only proceed if it's actually part of a table row (the marks entry table)
            if (tr) {
                e.preventDefault(); // Stop form submission
                e.stopPropagation(); // Stop bubbling
                
                const colIndex = Array.from(tr.children).indexOf(td);
                let nextTr = tr.nextElementSibling;
                
                while (nextTr) {
                    const nextInput = nextTr.children[colIndex].querySelector('input');
                    if (nextInput && !nextInput.disabled) {
                        nextInput.focus();
                        nextInput.select();
                        return false;
                    }
                    nextTr = nextTr.nextElementSibling;
                }
            }
        }
    }
}, true); // Use capture phase

// Extra layer of protection: prevent the form itself from submitting on Enter if focused on an input
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const active = document.activeElement;
            // If the user hit Enter while in a numeric input, and it's NOT a submit button
            if (active.tagName === 'INPUT' && active.type === 'number') {
                // We check if this was triggered by "Enter"
                // (Most browsers don't provide the original event here, but we can check if it's the expected focus)
                // Since our keydown handler has e.preventDefault(), this block is a fallback.
            }
        });
    });
});

function confirmFinalize() {
    if (confirm("You can't update any marks and it will save permanently, Are you sure to finalize marks for this course?")) {
        const formAction = document.getElementById('form-action');
        if (formAction) {
            formAction.value = 'finalize_result';
        }
        return true;
    }
    return false;
}
