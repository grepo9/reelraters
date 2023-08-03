// home_page.js

let scrollAmount = 0;
const scrollStep = 300; // Adjust this value to control the scroll distance

function scrollContent(direction) {
    const scrollingContent = document.querySelector('.scrolling-content');
    const containerWidth = document.querySelector('.scrolling-container').offsetWidth;
    const contentWidth = scrollingContent.scrollWidth;

    if (direction === -1) {
        // Scroll left
        scrollAmount = Math.max(scrollAmount - scrollStep, 0);
    } else if (direction === 1) {
        // Scroll right
        scrollAmount = Math.min(scrollAmount + scrollStep, contentWidth - containerWidth);
    }

    scrollingContent.style.transform = `translateX(-${scrollAmount}px)`;

    // Show/hide the scrolling buttons based on scroll position
    const scrollingLeftButton = document.querySelector('.scrolling-left-button');
    const scrollingRightButton = document.querySelector('.scrolling-right-button');

    if (scrollAmount > 0) {
        scrollingLeftButton.style.display = 'block';
    } else {
        scrollingLeftButton.style.display = 'none';
    }

    if (scrollAmount < contentWidth - containerWidth) {
        scrollingRightButton.style.display = 'block';
    } else {
        scrollingRightButton.style.display = 'none';
    }
}

// Call scrollContent with initial direction value 0 to hide the right button initially
scrollContent(0);
