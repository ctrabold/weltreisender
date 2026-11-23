document.addEventListener('keydown', (event) => {
    // Check for 'ArrowRight' or key code 39
    if (event.key === 'ArrowRight' || event.keyCode === 39) {
        // Find the 'previous' page link element (this is the part you need to change!)
        const prevLink = document.querySelector('.book-page-footer a.prev');
        if (prevLink) {
            prevLink.click();
            event.preventDefault();
        }
    }
    // Check for 'ArrowLeft' or key code 37
    else if (event.key === 'ArrowLeft' || event.keyCode === 37) {
        // Find the 'next' page link element (this is the part you need to change!)
        const nextLink = document.querySelector('.book-page-footer a.next');
        if (nextLink) {
            nextLink.click();
            event.preventDefault();
        }
    }
});
